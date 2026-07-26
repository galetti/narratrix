from engine.constants import LOC_INVENTORY
from engine.schema import SUPPORTED_EFFECTS


class EffectProcessingError(ValueError):
    """Raised when content asks the engine to execute an invalid effect."""


class EffectProcessor:
    """Central, strict processor for all state-changing content effects."""

    def __init__(self, game):
        self.game = game

    def process(self, effects_data, context_npc=None):
        if not effects_data:
            return
        effects = effects_data if isinstance(effects_data, list) else [effects_data]
        for effect in effects:
            self._execute_single_effect(effect, context_npc)

    def _execute_single_effect(self, effect, context_npc):
        if not isinstance(effect, dict):
            raise EffectProcessingError("Effekt muss ein Dict sein.")
        effect_type = effect.get("type")
        if effect_type not in SUPPORTED_EFFECTS:
            raise EffectProcessingError(f"Unbekannter Effekttyp '{effect_type}'.")

        if effect_type in {"move_npc", "teleport_npc"}:
            npc_id = effect.get("npc") or (context_npc and context_npc.get("id"))
            room_id = effect.get("room") or effect.get("target")
            if not npc_id or room_id not in self.game.rooms:
                raise EffectProcessingError(
                    f"{effect_type}: NPC '{npc_id}' oder Raum '{room_id}' ungültig."
                )
            self.game.ai.move_npc(npc_id, room_id, instant=effect_type == "teleport_npc")
            if (
                context_npc
                and context_npc.get("id") == npc_id
                and room_id != self.game.location
                and self.game.dialogue_active
            ):
                self.game.dialogue_system.end_dialogue(reason="Partner geht")
            return

        if effect_type in {"set_state", "set_npc_state"}:
            npc_id = effect.get("npc") or (context_npc and context_npc.get("id"))
            target = self._find_npc(npc_id)
            if not target:
                raise EffectProcessingError(f"NPC '{npc_id}' für Zustandswechsel fehlt.")
            self.game.set_npc_state(target, effect.get("value"))
            if target.get("location") == self.game.location:
                self.game.log("info", f"({target['name']} wirkt verändert.)")
            return

        if effect_type == "learn":
            fact = effect.get("fact")
            if not fact:
                raise EffectProcessingError("learn benötigt 'fact'.")
            was_new = self.game.add_knowledge(fact)
            if was_new and not fact.startswith("task_"):
                self.game.log("success", f"(Wissen erhalten: {fact})")
            return

        if effect_type in {"spawn_item", "receive_item"}:
            item_id = effect.get("item") or effect.get("item_id")
            obj = self._find_object(item_id)
            if not obj:
                raise EffectProcessingError(f"Item '{item_id}' nicht gefunden.")
            location = effect.get("location", LOC_INVENTORY)
            obj["location"] = location
            if location == LOC_INVENTORY:
                self.game.log("success", f"Erhalten: {obj['name']}")
            return

        if effect_type == "update_object":
            target_id = effect.get("target")
            target = self._find_object(target_id) or self._find_npc(target_id)
            if not target:
                raise EffectProcessingError(f"Objekt/NPC '{target_id}' für Update fehlt.")
            updates = effect.get("updates")
            if not isinstance(updates, dict):
                raise EffectProcessingError("update_object benötigt ein 'updates'-Dict.")
            target.update(updates)
            return

        if effect_type == "damage_stability":
            amount = float(effect.get("value", 0))
            self.game.stability -= amount
            if amount > 0:
                self.game.log("alarm", f"WARNUNG: Hüllenintegrität gefallen (-{amount:g}%)")
            return

        if effect_type == "game_over":
            reason = effect.get("reason", "Game Over")
            self.game.log("alarm", reason)
            self.game.game_over = True
            return

        if effect_type == "trigger_event":
            event_id = effect.get("id")
            if not self.game.events.trigger_event_by_id(event_id):
                # A one-shot event that already ran is a valid no-op.
                if not self.game.events.has_event(event_id):
                    raise EffectProcessingError(f"Event '{event_id}' nicht gefunden.")
            return

        if effect_type == "message":
            message = effect.get("message")
            if not message:
                raise EffectProcessingError("message benötigt Text.")
            self.game.log(effect.get("log_type", "info"), message)
            return

        if effect_type == "quest_start":
            quest_id = effect.get("id") or effect.get("quest")
            self.game.quests.start_quest(quest_id)
            return

        if effect_type == "quest_update":
            payload = effect.get("quest_update", effect)
            quest_id = payload.get("id") or payload.get("quest")
            if "stage" not in payload:
                raise EffectProcessingError("quest_update benötigt 'stage'.")
            self.game.quests.update_quest(quest_id, payload["stage"])
            return

        if effect_type == "quest_complete":
            self.game.quests.complete_quest(effect.get("id") or effect.get("quest"))
            return

        if effect_type == "quest_fail":
            self.game.quests.fail_quest(effect.get("id") or effect.get("quest"))
            return

        if effect_type == "load_chapter":
            target = effect.get("chapter") or effect.get("target")
            if not target:
                raise EffectProcessingError("load_chapter benötigt ein Ziel.")
            self.game.pending_chapter_load = target

    def _find_object(self, identifier):
        if identifier in self.game.objects:
            return self.game.objects[identifier]
        return next(
            (obj for obj in self.game.objects.values() if obj.get("id") == identifier),
            None,
        )

    def _find_npc(self, identifier):
        return next(
            (
                npc
                for npc in self.game.npcs
                if npc.get("id") == identifier or npc.get("name") == identifier
            ),
            None,
        )
