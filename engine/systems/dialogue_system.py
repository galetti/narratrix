# narratrix_engine/engine/systems/dialogue_system.py
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from engine.constants import ATTR_NAME
from engine.llm_bridge import LLMBridge
from engine.schema import ConditionSpec, DialogueEntry, NPCData
from engine.strings import Texts
from engine.systems.llm_grounding import (
    build_prompts,
    entry_text,
    preserves_core_facts,
    sanitize_reply,
)

if TYPE_CHECKING:
    from engine.game_state import GameState


class DialogueSystem:
    """
    Verwaltet die Logik von Dialogen, unabhängig vom Input-Handler.
    """
    MAX_HISTORY_MESSAGES: int = 8

    def __init__(self, game: GameState) -> None:
        self.game: GameState = game
        self._conversation_history: list[dict[str, str]] = []

    def start_dialogue(self, npc: NPCData) -> None:
        """Startet einen Dialog mit einem NPC."""
        self.game.dialogue_active = True
        self.game.dialogue_partner = npc
        self._conversation_history.clear()
        
        # Begrüßung
        current_state = npc.get('state', 'default')
        dialogue_db = self._get_dialogue_db(npc, current_state)
        greeting = dialogue_db.get('greeting', "...")
        
        self.game.log('event', Texts.DIALOGUE_HEADER.format(npc=npc[ATTR_NAME].upper()))
        self.print_dialogue(npc, greeting)
        self.show_topics(npc)

    def end_dialogue(self, reason: str | None = None) -> None:
        """Beendet den aktuellen Dialog."""
        suffix = f" ({reason})" if reason else ""
        self.game.log('event', Texts.DIALOGUE_ENDED.format(suffix=suffix))
        self.game.dialogue_active = False
        self.game.dialogue_partner = None
        self._conversation_history.clear()

    def refresh_topics(self) -> None:
        """Zeigt die Themen für den aktuellen NPC erneut an."""
        npc = self.game.dialogue_partner
        if not npc: return
        
        self.show_topics(npc)

    def handle_selection(self, entry: DialogueEntry, topic_key: str | None = None) -> None:
        """Verarbeitet eine gewählte Dialog-Option."""
        selected_label: str | None = None
        with self.game.lock:
            npc = self.game.dialogue_partner
            if not npc:
                return

            if topic_key:  # Wenn es ein Key war, loggen wir den Label als User-Input
                label = topic_key
                if isinstance(entry, dict) and 'label' in entry:
                    label = entry['label']
                selected_label = label
                self.game.log('user', f"> {label}")

        self.print_dialogue(npc, entry, prompt_context=selected_label)

        with self.game.lock:
            # Effekte auslösen (Delegation an EffectProcessor)
            if isinstance(entry, dict) and 'effect' in entry:
                self.game.effects.process(entry['effect'], context_npc=npc)

            # Nach der Interaktion Topics neu laden (Status könnte sich geändert haben)
            self.refresh_topics()

    def handle_fallback(self, user_text: str) -> None:
        """Wenn keine passende Option gefunden wurde."""
        with self.game.lock:
            npc = self.game.dialogue_partner
            if not npc:
                return

            current_state = npc.get('state', 'default')
            dialogue_db = self._get_dialogue_db(npc, current_state)
            use_llm = self.game.config.get('use_llm_dialogue', False)
            default_reply = dialogue_db.get('default')

        if use_llm:
            self.print_dialogue(npc, "LLM_AUTO_REPLY", prompt_context=user_text)
        else:
            with self.game.lock:
                if default_reply:
                    self.print_dialogue(npc, default_reply)
                else:
                    self.game.log('character', Texts.DIALOGUE_CONFUSED.format(npc=npc[ATTR_NAME]))

        with self.game.lock:
            self.show_topics(npc)

    # --- INTERNE HELPER ---

    def _get_dialogue_db(self, npc: NPCData, state: str) -> dict[str, DialogueEntry]:
        if 'states' in npc:
            return npc['states'].get(state, {}).get('dialogue', {})
        return npc.get('dialogue', {}).get(state, {})

    def get_visible_topics(
        self, npc: NPCData
    ) -> tuple[list[tuple[str, DialogueEntry]], dict[str, DialogueEntry]]:
        current_state = npc.get('state', 'default')
        dialogue_db = self._get_dialogue_db(npc, current_state)
        
        visible: list[tuple[str, DialogueEntry]] = []
        for topic, entry in dialogue_db.items():
            if topic in ['greeting', 'default']: continue
            
            if not self._check_condition_wrapper(entry):
                continue
            
            is_hidden = False
            if isinstance(entry, dict) and entry.get('hidden', False):
                is_hidden = True
            
            if not is_hidden:
                visible.append((topic, entry))
        return visible, dialogue_db

    def show_topics(self, npc: NPCData) -> None:
        visible, _ = self.get_visible_topics(npc)
        
        if not visible:
            self.game.log('info', Texts.DIALOGUE_NO_TOPICS)
            return

        options: list[str] = []
        for i, (topic, entry) in enumerate(visible):
            label = topic.capitalize()
            if isinstance(entry, dict) and 'label' in entry:
                label = entry['label']
            options.append(f"[{i+1}] {label}")
        
        self.game.log('info', Texts.DIALOGUE_OPTIONS.format(", ".join(options)))

    def _check_condition_wrapper(self, entry: DialogueEntry) -> bool:
        if isinstance(entry, dict) and 'condition' in entry: 
            return self._check_condition(entry['condition'])
        return True

    def _check_condition(self, condition: ConditionSpec | None) -> bool:
        if not condition: return True
        return self.game.events.evaluate_condition(condition)

    def _known_facts_for_npc(self, npc: NPCData) -> list[str]:
        visible, _ = self.get_visible_topics(npc)
        return [entry_text(entry) for _, entry in visible if entry_text(entry)]

    def _record_history_turn(
        self, npc: NPCData, user_text: str | None, assistant_text: str
    ) -> None:
        if self.game.dialogue_partner is not npc or not assistant_text:
            return
        if user_text and user_text.strip():
            self._conversation_history.append(
                {"role": "user", "content": user_text.strip()}
            )
        self._conversation_history.append(
            {"role": "assistant", "content": assistant_text}
        )
        if len(self._conversation_history) > self.MAX_HISTORY_MESSAGES:
            self._conversation_history = self._conversation_history[
                -self.MAX_HISTORY_MESSAGES :
            ]

    @staticmethod
    def _validate_llm_reply(
        raw: str | None,
        *,
        npc_name: str,
        core_text: str,
        is_auto_reply: bool,
    ) -> str | None:
        cleaned = sanitize_reply(raw, npc_name=npc_name)
        if cleaned and (is_auto_reply or preserves_core_facts(core_text, cleaned)):
            return cleaned
        return None

    def print_dialogue(
        self,
        npc: NPCData,
        response_entry: DialogueEntry,
        prompt_context: str | None = None,
    ) -> None:
        with self.game.lock:
            is_auto_reply = response_entry == "LLM_AUTO_REPLY"
            core_text: Any = "" if is_auto_reply else entry_text(response_entry)
            final_text = str(core_text)
            npc_name = str(npc.get(ATTR_NAME, ""))
            use_llm = bool(self.game.config.get('use_llm_dialogue', False))
            llm_url = self.game.config.get('llm_url')
            llm_model = self.game.config.get('llm_model')
            llm_kwargs: dict[str, Any] = {}
            for cfg_key, arg_name in (
                ('llm_api_key', 'api_key'),
                ('llm_fallback_url', 'fallback_url'),
                ('llm_fallback_model', 'fallback_model'),
                ('llm_fallback_api_key', 'fallback_api_key'),
                ('llm_providers', 'providers'),
            ):
                value = self.game.config.get(cfg_key)
                if value:
                    llm_kwargs[arg_name] = value
            sys_prompt = ""
            user_msg = ""
            history_snapshot: list[dict[str, str]] = (
                list(self._conversation_history)
                if self.game.dialogue_partner is npc
                else []
            )
            if use_llm:
                if (
                    len(
                        LLMBridge.resolve_providers(
                            api_url=llm_url,
                            model=llm_model,
                            **llm_kwargs,
                        )
                    )
                    > 1
                ):
                    core_snapshot = final_text
                    llm_kwargs["response_filter"] = (
                        lambda raw_reply: self._validate_llm_reply(
                            raw_reply,
                            npc_name=npc_name,
                            core_text=core_snapshot,
                            is_auto_reply=is_auto_reply,
                        )
                    )
                known_facts = self._known_facts_for_npc(npc)
                sys_prompt, user_msg = build_prompts(
                    self.game,
                    npc,
                    core_text=None if is_auto_reply else final_text,
                    player_text=prompt_context,
                    known_facts=known_facts,
                )
                self.game.log('info', Texts.DIALOGUE_THINKING.format(npc=npc[ATTR_NAME]))

        if use_llm:
            raw = LLMBridge.call(
                sys_prompt,
                user_msg,
                api_url=llm_url,
                model=llm_model,
                history=history_snapshot or None,
                **llm_kwargs,
            )
            validated = self._validate_llm_reply(
                raw,
                npc_name=npc_name,
                core_text=final_text,
                is_auto_reply=is_auto_reply,
            )
            if validated:
                final_text = validated

        with self.game.lock:
            if is_auto_reply and not final_text:
                current_state = npc.get('state', 'default')
                dialogue_db = self._get_dialogue_db(npc, current_state)
                default_reply = dialogue_db.get('default')
                if default_reply:
                    final_text = entry_text(default_reply)
                else:
                    self.game.log('character', Texts.DIALOGUE_CONFUSED.format(npc=npc[ATTR_NAME]))
                    return

            self._record_history_turn(npc, prompt_context, final_text)
            self.game.log('character', Texts.DIALOGUE_LINE.format(npc=npc[ATTR_NAME], text=final_text))
