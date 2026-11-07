from __future__ import annotations

from typing import TYPE_CHECKING, Any

from engine.schema import ActiveQuestInfo, QuestDefinitionData, QuestStateData
from engine.strings import Texts

if TYPE_CHECKING:
    from engine.game_state import GameState


class QuestManager:
    VALID_STATUSES: set[str] = {"inactive", "active", "completed", "failed"}

    def __init__(self, game: GameState) -> None:
        self.game: GameState = game
        self.definitions: dict[str, QuestDefinitionData] = {}
        self.states: dict[str, QuestStateData] = {}

    @staticmethod
    def _default_state() -> QuestStateData:
        return {
            "status": "inactive",
            "stage": None,
            "outcome": None,
            "history": [],
        }

    def load_definitions(self, quests_data: dict[str, QuestDefinitionData]) -> None:
        self.definitions = quests_data
        for quest_id in self.definitions:
            self.states.setdefault(quest_id, self._default_state())

    def _definition(self, quest_id: str) -> QuestDefinitionData:
        definition = self.definitions.get(quest_id)
        if not definition:
            raise ValueError(f"Quest '{quest_id}' ist nicht definiert.")
        return definition

    def start_quest(self, quest_id: str) -> bool:
        definition = self._definition(quest_id)
        state = self.states.setdefault(quest_id, self._default_state())
        if state.get("status") != "inactive":
            return False

        # Block starting if a mutually exclusive quest is already completed.
        for other_id in definition.get("exclusive_with", []):
            other_state = self.states.get(other_id, {})
            if other_state.get("status") == "completed":
                return False

        stages = definition["stages"]
        start_stage = int(definition.get("start_stage", min(stages)))
        if start_stage not in stages:
            raise ValueError(f"Quest '{quest_id}': Start-Stage {start_stage} fehlt.")

        state.update(
            status="active",
            stage=start_stage,
            outcome=None,
            history=[start_stage],
        )
        title = definition.get("title", quest_id)
        self.game.log("success", Texts.QUEST_NEW.format(title=title))
        self.game.log("info", Texts.QUEST_GOAL.format(goal=stages[start_stage]))

        # Automatically fail active quests that are mutually exclusive with this one.
        for other_id in definition.get("exclusive_with", []):
            other_state = self.states.get(other_id)
            if other_state and other_state.get("status") == "active":
                self.fail_quest(other_id)

        return True

    def can_transition(self, quest_id: str, target_stage: int) -> bool:
        definition = self._definition(quest_id)
        state = self.states.get(quest_id)
        if not state or state.get("status") != "active":
            return False
        if target_stage not in definition["stages"]:
            return False
        transitions = definition.get("transitions")
        current_stage = state.get("stage")
        if transitions is None or current_stage is None:
            return True
        allowed = transitions.get(int(current_stage), [])
        return target_stage in allowed

    def update_quest(
        self, quest_id: str, stage: int | str, *, force: bool = False
    ) -> bool:
        definition = self._definition(quest_id)
        state = self.states.get(quest_id)
        if not state or state.get("status") != "active":
            return False

        stage_num = int(stage)
        if stage_num not in definition["stages"]:
            raise ValueError(f"Quest '{quest_id}': Stage {stage_num} fehlt.")
        if state.get("stage") == stage_num:
            return False
        if not force and not self.can_transition(quest_id, stage_num):
            return False

        state["stage"] = stage_num
        history = list(state.get("history", []))
        if not history or history[-1] != stage_num:
            history.append(stage_num)
        state["history"] = history

        title = definition.get("title", quest_id)
        self.game.log("success", Texts.QUEST_UPDATED.format(title=title))
        self.game.log(
            "info",
            Texts.QUEST_NEW_GOAL.format(goal=definition["stages"][stage_num]),
        )
        return True

    def _validate_outcome(
        self, quest_id: str, definition: QuestDefinitionData, outcome: str | None
    ) -> str | None:
        if outcome is None:
            return None
        outcomes = definition.get("outcomes")
        if outcomes is not None and outcome not in outcomes:
            raise ValueError(
                f"Quest '{quest_id}': Outcome '{outcome}' ist nicht definiert."
            )
        return outcome

    def complete_quest(self, quest_id: str, outcome: str | None = None) -> bool:
        definition = self._definition(quest_id)
        state = self.states.get(quest_id)
        if not state or state.get("status") != "active":
            return False
        validated_outcome = self._validate_outcome(quest_id, definition, outcome)
        state["status"] = "completed"
        state["outcome"] = validated_outcome
        if "completion_stage" in definition:
            comp_stage = int(definition["completion_stage"])
            state["stage"] = comp_stage
            history = list(state.get("history", []))
            if not history or history[-1] != comp_stage:
                history.append(comp_stage)
            state["history"] = history
        self.game.log(
            "success",
            Texts.QUEST_COMPLETED.format(title=definition.get("title", quest_id)),
        )
        if validated_outcome and validated_outcome in definition.get("outcomes", {}):
            self.game.log(
                "info",
                Texts.QUEST_OUTCOME.format(
                    outcome=definition["outcomes"][validated_outcome]
                ),
            )
        for other_id in definition.get("exclusive_with", []):
            other_state = self.states.get(other_id)
            if other_state and other_state.get("status") == "active":
                self.fail_quest(other_id)
        return True

    def fail_quest(self, quest_id: str, outcome: str | None = None) -> bool:
        definition = self._definition(quest_id)
        state = self.states.get(quest_id)
        if not state or state.get("status") != "active":
            return False
        validated_outcome = self._validate_outcome(quest_id, definition, outcome)
        state["status"] = "failed"
        state["outcome"] = validated_outcome
        self.game.log(
            "error",
            Texts.QUEST_FAILED.format(title=definition.get("title", quest_id)),
        )
        if validated_outcome and validated_outcome in definition.get("outcomes", {}):
            self.game.log(
                "info",
                Texts.QUEST_OUTCOME.format(
                    outcome=definition["outcomes"][validated_outcome]
                ),
            )
        return True

    def get_active_quests(self) -> list[ActiveQuestInfo]:
        active: list[ActiveQuestInfo] = []
        for quest_id, state in self.states.items():
            if state.get("status") != "active":
                continue
            definition = self.definitions.get(quest_id, {})
            stage = state.get("stage")
            stages_map = definition.get("stages", {})
            stage_desc = stages_map.get(stage, "") if stage is not None else ""
            active.append(
                {
                    "id": quest_id,
                    "title": definition.get("title", quest_id),
                    "stage": stage,
                    "stage_desc": stage_desc,
                }
            )
        return active

    def get_completed_quests(self) -> list[str]:
        return [
            self.definitions.get(quest_id, {}).get("title", quest_id)
            for quest_id, state in self.states.items()
            if state.get("status") == "completed"
        ]

    def get_failed_quests(self) -> list[str]:
        return [
            self.definitions.get(quest_id, {}).get("title", quest_id)
            for quest_id, state in self.states.items()
            if state.get("status") == "failed"
        ]

    def get_save_data(self) -> dict[str, QuestStateData]:
        return {
            quest_id: {
                "status": state.get("status", "inactive"),
                "stage": state.get("stage"),
                "outcome": state.get("outcome"),
                "history": list(state.get("history", [])),
            }
            for quest_id, state in self.states.items()
        }

    def load_save_data(self, data: dict[str, Any]) -> None:
        restored: dict[str, QuestStateData] = {}
        for quest_id in self.definitions:
            incoming = data.get(quest_id, {})
            status = incoming.get("status", "inactive")
            if status not in self.VALID_STATUSES:
                status = "inactive"
            stage = incoming.get("stage")
            valid_stages = self.definitions[quest_id]["stages"]
            if stage is not None:
                stage = int(stage)
                if stage not in valid_stages:
                    stage = None
            outcome = incoming.get("outcome")
            outcomes_def = self.definitions[quest_id].get("outcomes")
            if outcome is not None:
                outcome = str(outcome)
                if outcomes_def is not None and outcome not in outcomes_def:
                    outcome = None
            raw_history = incoming.get("history")
            if isinstance(raw_history, list):
                history = [int(s) for s in raw_history if int(s) in valid_stages]
            elif stage is not None:
                history = [stage]
            else:
                history = []
            restored[quest_id] = {
                "status": status,
                "stage": stage,
                "outcome": outcome,
                "history": history,
            }
        self.states = restored
