class QuestManager:
    VALID_STATUSES = {"inactive", "active", "completed", "failed"}

    def __init__(self, game):
        self.game = game
        self.definitions = {}
        self.states = {}

    def load_definitions(self, quests_data):
        self.definitions = quests_data
        for quest_id in self.definitions:
            self.states.setdefault(quest_id, {"status": "inactive", "stage": None})

    def _definition(self, quest_id):
        definition = self.definitions.get(quest_id)
        if not definition:
            raise ValueError(f"Quest '{quest_id}' ist nicht definiert.")
        return definition

    def start_quest(self, quest_id):
        definition = self._definition(quest_id)
        state = self.states.setdefault(quest_id, {"status": "inactive", "stage": None})
        if state["status"] != "inactive":
            return False

        stages = definition["stages"]
        start_stage = int(definition.get("start_stage", min(stages)))
        if start_stage not in stages:
            raise ValueError(f"Quest '{quest_id}': Start-Stage {start_stage} fehlt.")

        state.update(status="active", stage=start_stage)
        title = definition.get("title", quest_id)
        self.game.log("success", f"NEUE AUFGABE: {title}")
        self.game.log("info", f"Ziel: {stages[start_stage]}")
        return True

    def update_quest(self, quest_id, stage):
        definition = self._definition(quest_id)
        state = self.states.get(quest_id)
        if not state or state["status"] != "active":
            return False

        stage = int(stage)
        if stage not in definition["stages"]:
            raise ValueError(f"Quest '{quest_id}': Stage {stage} fehlt.")
        if state.get("stage") == stage:
            return False

        state["stage"] = stage
        title = definition.get("title", quest_id)
        self.game.log("success", f"AUFGABE AKTUALISIERT: {title}")
        self.game.log("info", f"Neues Ziel: {definition['stages'][stage]}")
        return True

    def complete_quest(self, quest_id):
        definition = self._definition(quest_id)
        state = self.states.get(quest_id)
        if not state or state["status"] != "active":
            return False
        state["status"] = "completed"
        if "completion_stage" in definition:
            state["stage"] = int(definition["completion_stage"])
        self.game.log(
            "success",
            f"AUFGABE ERLEDIGT: {definition.get('title', quest_id)}",
        )
        return True

    def fail_quest(self, quest_id):
        definition = self._definition(quest_id)
        state = self.states.get(quest_id)
        if not state or state["status"] != "active":
            return False
        state["status"] = "failed"
        self.game.log(
            "error",
            f"AUFGABE FEHLGESCHLAGEN: {definition.get('title', quest_id)}",
        )
        return True

    def get_active_quests(self):
        active = []
        for quest_id, state in self.states.items():
            if state.get("status") != "active":
                continue
            definition = self.definitions.get(quest_id, {})
            stage = state.get("stage")
            active.append(
                {
                    "id": quest_id,
                    "title": definition.get("title", quest_id),
                    "stage": stage,
                    "stage_desc": definition.get("stages", {}).get(stage, ""),
                }
            )
        return active

    def get_completed_quests(self):
        return [
            self.definitions.get(quest_id, {}).get("title", quest_id)
            for quest_id, state in self.states.items()
            if state.get("status") == "completed"
        ]

    def get_failed_quests(self):
        return [
            self.definitions.get(quest_id, {}).get("title", quest_id)
            for quest_id, state in self.states.items()
            if state.get("status") == "failed"
        ]

    def get_save_data(self):
        return {
            quest_id: {"status": state["status"], "stage": state.get("stage")}
            for quest_id, state in self.states.items()
        }

    def load_save_data(self, data):
        restored = {}
        for quest_id in self.definitions:
            incoming = data.get(quest_id, {})
            status = incoming.get("status", "inactive")
            if status not in self.VALID_STATUSES:
                status = "inactive"
            stage = incoming.get("stage")
            if stage is not None:
                stage = int(stage)
                if stage not in self.definitions[quest_id]["stages"]:
                    stage = None
            restored[quest_id] = {"status": status, "stage": stage}
        self.states = restored
