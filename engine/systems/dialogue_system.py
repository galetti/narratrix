# narratrix_engine/engine/systems/dialogue_system.py
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from engine.constants import ATTR_NAME
from engine.llm_bridge import LLMBridge
from engine.schema import ConditionSpec, DialogueEntry, NPCData

if TYPE_CHECKING:
    from engine.game_state import GameState


class DialogueSystem:
    """
    Verwaltet die Logik von Dialogen, unabhängig vom Input-Handler.
    """
    def __init__(self, game: GameState) -> None:
        self.game: GameState = game

    def start_dialogue(self, npc: NPCData) -> None:
        """Startet einen Dialog mit einem NPC."""
        self.game.dialogue_active = True
        self.game.dialogue_partner = npc
        
        # Begrüßung
        current_state = npc.get('state', 'default')
        dialogue_db = self._get_dialogue_db(npc, current_state)
        greeting = dialogue_db.get('greeting', "...")
        
        self.game.log('event', f"--- GESPRÄCH MIT {npc[ATTR_NAME].upper()} ---")
        self.print_dialogue(npc, greeting)
        self.show_topics(npc)

    def end_dialogue(self, reason: str | None = None) -> None:
        """Beendet den aktuellen Dialog."""
        suffix = f" ({reason})" if reason else ""
        self.game.log('event', f"--- GESPRÄCH BEENDET{suffix} ---")
        self.game.dialogue_active = False
        self.game.dialogue_partner = None

    def refresh_topics(self) -> None:
        """Zeigt die Themen für den aktuellen NPC erneut an."""
        npc = self.game.dialogue_partner
        if not npc: return
        
        self.show_topics(npc)

    def handle_selection(self, entry: DialogueEntry, topic_key: str | None = None) -> None:
        """Verarbeitet eine gewählte Dialog-Option."""
        npc = self.game.dialogue_partner
        if not npc: return

        if topic_key: # Wenn es ein Key war, loggen wir den Label als User-Input
            label = topic_key
            if isinstance(entry, dict) and 'label' in entry:
                label = entry['label']
            self.game.log('user', f"> {label}")

        self.print_dialogue(npc, entry)
        
        # Effekte auslösen (Delegation an EffectProcessor)
        if isinstance(entry, dict) and 'effect' in entry:
            self.game.effects.process(entry['effect'], context_npc=npc)
            
        # Nach der Interaktion Topics neu laden (Status könnte sich geändert haben)
        self.refresh_topics()

    def handle_fallback(self, user_text: str) -> None:
        """Wenn keine passende Option gefunden wurde."""
        npc = self.game.dialogue_partner
        if not npc: return
        
        current_state = npc.get('state', 'default')
        dialogue_db = self._get_dialogue_db(npc, current_state)
        
        use_llm = self.game.config.get('use_llm_dialogue', False)
        if use_llm: 
            self.print_dialogue(npc, "LLM_AUTO_REPLY", prompt_context=user_text)
        else: 
            default_reply = dialogue_db.get('default')
            if default_reply:
                self.print_dialogue(npc, default_reply)
            else:
                self.game.log('character', f"{npc[ATTR_NAME]} schaut dich fragend an.")
        
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
            self.game.log('info', "(Keine offensichtlichen Gesprächsthemen)")
            return

        options: list[str] = []
        for i, (topic, entry) in enumerate(visible):
            label = topic.capitalize()
            if isinstance(entry, dict) and 'label' in entry:
                label = entry['label']
            options.append(f"[{i+1}] {label}")
        
        self.game.log('info', "Optionen: " + ", ".join(options))

    def _check_condition_wrapper(self, entry: DialogueEntry) -> bool:
        if isinstance(entry, dict) and 'condition' in entry: 
            return self._check_condition(entry['condition'])
        return True

    def _check_condition(self, condition: ConditionSpec | None) -> bool:
        if not condition: return True
        return self.game.events.evaluate_condition(condition)

    def print_dialogue(
        self,
        npc: NPCData,
        response_entry: DialogueEntry,
        prompt_context: str | None = None,
    ) -> None:
        core_text: Any = response_entry
        if isinstance(response_entry, dict): core_text = response_entry.get('text', "")
        
        final_text = str(core_text)
        use_llm = self.game.config.get('use_llm_dialogue', False)
        if use_llm:
            personality = npc.get('personality', 'Neutral')
            state = npc.get('state', 'default')
            stress = "HOCH" if self.game.stability < 50 else "NIEDRIG"
            
            if response_entry == "LLM_AUTO_REPLY":
                sys_prompt = f"Du bist {npc[ATTR_NAME]} ({personality}). Stimmung: {state}. Stress: {stress}. Antworte auf: '{prompt_context}'."
                user_msg = "Antworte kurz und passend zur Rolle."
            else:
                sys_prompt = f"Du bist {npc[ATTR_NAME]} ({personality}). Stimmung: {state}. Stress: {stress}. Formuliere um:"
                user_msg = f"Kern-Aussage: {core_text}"
            
            self.game.log('info', f"({npc[ATTR_NAME]} denkt nach...)")
            enhanced = LLMBridge.call(
                sys_prompt,
                user_msg,
                api_url=self.game.config.get('llm_url'),
                model=self.game.config.get('llm_model'),
            )
            if enhanced: final_text = enhanced
            
        self.game.log('character', f"{npc[ATTR_NAME]}: \"{final_text}\"")
