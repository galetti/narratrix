from engine.constants import LOC_INVENTORY


class EventManager:
    def __init__(self, game):
        self.game = game
        self.events = []

    def load_events(self, events_data):
        self.events = events_data
        for event in self.events:
            event.setdefault("triggered", False)

    def has_event(self, event_id):
        return any(event.get("id") == event_id for event in self.events)

    def update(self):
        for event in self.events:
            if event.get("triggered") and not event.get("repeat", False):
                continue
            if (
                event.get("repeat", False)
                and event.get("last_triggered_at") == self.game.time
            ):
                continue
            if self._check_trigger(event):
                self._execute_event(event)

    def trigger_event_by_id(self, event_id):
        event = next((entry for entry in self.events if entry.get("id") == event_id), None)
        if not event:
            return False
        if event.get("triggered") and not event.get("repeat", False):
            return False
        self._execute_event(event)
        return True

    def _check_trigger(self, event):
        trigger_type = event.get("trigger", "manual")

        if trigger_type == "time":
            base_result = self.game.time >= event.get("trigger_time", 0)
        elif trigger_type == "location":
            target = event.get("location", event.get("value"))
            base_result = self.game.location == target
        elif trigger_type == "condition":
            base_result = self.evaluate_condition(event.get("condition", {}))
        elif trigger_type == "complex":
            conditions = event.get("conditions", [])
            operator = event.get("operator", "AND").upper()
            results = [self.evaluate_condition(condition) for condition in conditions]
            base_result = bool(results) and (
                all(results) if operator == "AND" else any(results)
            )
        else:  # manual
            return False

        # A time/location trigger may carry an additional guard condition.
        if trigger_type != "condition" and "condition" in event:
            base_result = base_result and self.evaluate_condition(event["condition"])
        return base_result

    def evaluate_condition(self, condition):
        if isinstance(condition, str):
            return condition in self.game.knowledge
        if not isinstance(condition, dict):
            return False

        condition_type = condition.get("type")
        negate = bool(condition.get("not", False))
        result = False

        if condition_type == "knowledge":
            result = condition.get("value") in self.game.knowledge
        elif condition_type == "location":
            result = self.game.location == condition.get("value")
        elif condition_type == "item_location":
            item = self.game.objects.get(condition.get("item"))
            result = bool(item and item.get("location") == condition.get("location"))
        elif condition_type == "npc_state":
            npc_id = condition.get("npc")
            npc = next(
                (
                    entry
                    for entry in self.game.npcs
                    if entry.get("id") == npc_id or entry.get("name") == npc_id
                ),
                None,
            )
            result = bool(npc and npc.get("state") == condition.get("state"))
        elif condition_type == "quest_state":
            quest = self.game.quests.states.get(condition.get("quest"), {})
            result = quest.get("status") == condition.get("status", "active")
            if "stage" in condition:
                result = result and quest.get("stage") == int(condition["stage"])
        elif condition_type == "stability":
            threshold = float(condition.get("value", 0))
            operator = condition.get("op", "<")
            comparisons = {
                "<": self.game.stability < threshold,
                "<=": self.game.stability <= threshold,
                ">": self.game.stability > threshold,
                ">=": self.game.stability >= threshold,
                "==": self.game.stability == threshold,
            }
            result = comparisons.get(operator, False)
        elif condition_type == "event_triggered":
            target = next(
                (entry for entry in self.events if entry.get("id") == condition.get("id")),
                None,
            )
            result = bool(target and target.get("triggered"))
        elif condition_type == "inventory":
            # Backward-compatible convenience condition.
            item = self.game.objects.get(condition.get("item"))
            result = bool(item and item.get("location") == LOC_INVENTORY)
        else:
            result = False

        return not result if negate else result

    def _execute_event(self, event):
        event["triggered"] = True
        event["last_triggered_at"] = self.game.time

        origin = event.get("origin_id")
        if "description" in event and (not origin or origin == self.game.location):
            if event.get("title"):
                self.game.log("event", event["title"])
            self.game.log("story", event["description"])

        if "sound_msg" in event:
            source_volume = max(0.0, float(event.get("volume", 1.0)))
            if origin:
                self.game.ai.notify_noise(origin, source_volume)

            if origin and origin != self.game.location:
                propagated, direction = self.game.acoustics.get_audibility_info(
                    origin, self.game.location
                )
                heard_volume = min(1.0, propagated * source_volume)
                if heard_volume > 0.05:
                    prefix = "(leise) " if heard_volume < 0.3 else ""
                    if heard_volume > 0.8:
                        prefix = "(LAUT) "
                    formatted_direction = (
                        direction[0].upper() + direction[1:] if direction else "Irgendwo"
                    )
                    self.game.log(
                        "event",
                        f"{formatted_direction} hörst du: {prefix}{event['sound_msg']}",
                    )
            elif origin == self.game.location and "description" not in event:
                self.game.log("event", event["sound_msg"])

        if "message" in event:
            self.game.log("info", event["message"])
        if "quest_start" in event:
            self.game.quests.start_quest(event["quest_start"])
        if "quest_update" in event:
            payload = event["quest_update"]
            self.game.quests.update_quest(payload["id"], payload["stage"])
        if "quest_complete" in event:
            self.game.quests.complete_quest(event["quest_complete"])
        if "effects" in event:
            self.game.effects.process(event["effects"])
