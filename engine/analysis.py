from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

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
