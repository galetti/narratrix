from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING, Any, TypedDict

from engine.constants import ATTR_NAME

if TYPE_CHECKING:
    from engine.game_state import GameState


class RoomSimulationSnapshot(TypedDict):
    npcs: list[str]
    events: list[str]


class TimelineSnapshot(TypedDict):
    time: int
    rooms: dict[str, RoomSimulationSnapshot]


def generate_future_matrix(
    initial_state: GameState,
    minutes_to_simulate: int = 60,
    step_size: int = 5,
) -> list[TimelineSnapshot]:
    """Simulate a cloned state without mutating the live game."""

    if minutes_to_simulate <= 0 or step_size <= 0:
        return []
    simulation = initial_state.clone()
    timeline: list[TimelineSnapshot] = []

    for _ in range(0, minutes_to_simulate, step_size):
        previous_time = simulation.time
        simulation.tick(step_size)
        snapshot: TimelineSnapshot = {
            "time": simulation.time,
            "rooms": {
                room_id: {"npcs": [], "events": []}
                for room_id in simulation.rooms
            },
        }

        for npc in simulation.npcs:
            location = npc.get("location")
            if location in snapshot["rooms"]:
                snapshot["rooms"][location]["npcs"].append(npc[ATTR_NAME])

        for event in simulation.events.events:
            triggered_at = event.get("last_triggered_at")
            if triggered_at is None or not (previous_time < triggered_at <= simulation.time):
                continue
            origin = event.get("origin_id")
            if origin in snapshot["rooms"]:
                snapshot["rooms"][origin]["events"].append(
                    event.get("title", event["id"])
                )
        timeline.append(snapshot)

    return timeline


def _reachable_stages(
    start_stage: int, transitions: dict[int, list[int]]
) -> set[int]:
    visited: set[int] = {start_stage}
    queue: deque[int] = deque([start_stage])
    while queue:
        current = queue.popleft()
        for nxt in transitions.get(current, []):
            if nxt not in visited:
                visited.add(nxt)
                queue.append(nxt)
    return visited


def _can_reach_any(
    start_stage: int, targets: set[int], transitions: dict[int, list[int]]
) -> bool:
    return bool(_reachable_stages(start_stage, transitions) & targets)


def validate_quest_state_graph(config: dict[str, Any]) -> list[str]:
    """Statically analyze quest state-trees, transitions, and condition references.

    Returns a list of human-readable diagnostic issues (empty if clean).
    """
    issues: list[str] = []
    quests: dict[str, dict[str, Any]] = config.get("quests", {})
    reachable_by_quest: dict[str, set[int]] = {}

    for quest_id, quest in quests.items():
        stages: dict[int, str] = {int(k): str(v) for k, v in quest.get("stages", {}).items()}
        if not stages:
            issues.append(f"Quest '{quest_id}': Keine Stages definiert.")
            continue

        start_stage = int(quest.get("start_stage", min(stages)))
        if start_stage not in stages:
            issues.append(f"Quest '{quest_id}': Start-Stage {start_stage} fehlt.")
            continue

        raw_transitions = quest.get("transitions")
        if isinstance(raw_transitions, dict):
            transitions: dict[int, list[int]] = {
                int(src): [int(dst) for dst in dsts]
                for src, dsts in raw_transitions.items()
            }
            reachable = _reachable_stages(start_stage, transitions)
            if "completion_stage" in quest:
                reachable.add(int(quest["completion_stage"]))
            reachable_by_quest[quest_id] = reachable

            unreachable = sorted(set(stages) - reachable)
            if unreachable:
                issues.append(
                    f"Quest '{quest_id}': Nicht erreichbare Stages ab Stage {start_stage}: {unreachable}."
                )

            terminal_stages = {
                stage for stage in reachable if not transitions.get(stage)
            }
            if "completion_stage" in quest:
                terminal_stages.add(int(quest["completion_stage"]))

            for stage in sorted(reachable):
                if not _can_reach_any(stage, terminal_stages, transitions):
                    issues.append(
                        f"Quest '{quest_id}': Stage {stage} liegt in einer Endlosschleife ohne erreichbaren Ausgang."
                    )
        else:
            reachable_by_quest[quest_id] = set(stages)

        for other_id in quest.get("exclusive_with", []):
            other_quest = quests.get(other_id)
            if not other_quest:
                issues.append(
                    f"Quest '{quest_id}': exclusive_with verweist auf unbekannte Quest '{other_id}'."
                )
            elif quest_id not in other_quest.get("exclusive_with", []):
                issues.append(
                    f"Quest '{quest_id}': Asymmetrische exclusive_with-Beziehung mit '{other_id}'."
                )

    def check_condition(condition: Any, context: str) -> None:
        if not isinstance(condition, dict):
            return
        cond_type = condition.get("type")
        if cond_type in {"all", "any", "complex"}:
            for idx, sub in enumerate(condition.get("conditions", [])):
                check_condition(sub, f"{context}.conditions[{idx}]")
            return
        if cond_type == "quest_state":
            quest_id = condition.get("quest")
            if not isinstance(quest_id, str) or quest_id not in quests:
                issues.append(
                    f"{context}: quest_state verweist auf unbekannte Quest '{quest_id}'."
                )
                return
            quest = quests[quest_id]
            stages = {int(k) for k in quest.get("stages", {})}
            reachable = reachable_by_quest.get(quest_id, stages)
            for key in ("stage", "visited_stage"):
                if key in condition:
                    target_stage = int(condition[key])
                    if target_stage not in stages:
                        issues.append(
                            f"{context}: Quest '{quest_id}' hat keine Stage {target_stage}."
                        )
                    elif target_stage not in reachable:
                        issues.append(
                            f"{context}: Quest '{quest_id}' Stage {target_stage} ist laut transitions unerreichbar."
                        )
            if "outcome" in condition and "outcomes" in quest:
                outcome = condition["outcome"]
                if outcome not in quest["outcomes"]:
                    issues.append(
                        f"{context}: Quest '{quest_id}' definiert kein Outcome '{outcome}'."
                    )

    def walk(node: Any, context: str) -> None:
        if isinstance(node, dict):
            if "condition" in node:
                check_condition(node["condition"], context)
            if "conditions" in node and isinstance(node["conditions"], list):
                for idx, sub in enumerate(node["conditions"]):
                    check_condition(sub, f"{context}.conditions[{idx}]")
            for key, value in node.items():
                if key not in {"condition", "conditions"}:
                    walk(value, f"{context}.{key}")
        elif isinstance(node, list):
            for idx, item in enumerate(node):
                walk(item, f"{context}[{idx}]")

    walk(config.get("events", []), "events")
    walk(config.get("narrative_matrix", []), "narrative_matrix")
    walk(config.get("combinations", []), "combinations")
    walk(config.get("npcs", []), "npcs")

    return issues
