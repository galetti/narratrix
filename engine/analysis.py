from engine.constants import ATTR_NAME


def generate_future_matrix(initial_state, minutes_to_simulate=60, step_size=5):
    """Simulate a cloned state without mutating the live game."""

    if minutes_to_simulate <= 0 or step_size <= 0:
        return []
    simulation = initial_state.clone()
    timeline = []

    for _ in range(0, minutes_to_simulate, step_size):
        previous_time = simulation.time
        simulation.tick(step_size)
        snapshot = {
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
