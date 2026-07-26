import heapq

from engine.constants import (
    ACOUSTIC_CLOSED_DOOR,
    ACOUSTIC_OPEN_AIR,
    ACOUSTIC_OPEN_DOOR,
    ATTR_NAME,
    LOC_INVENTORY,
)


class AcousticsSystem:
    """Propagate sound along the path with the highest transmission."""

    def __init__(self, game):
        self.game = game
        self.max_propagation_distance = 30

    def get_audibility_info(
        self, source_room_id, listener_room_id, use_player_tools=True
    ):
        if source_room_id not in self.game.rooms or listener_room_id not in self.game.rooms:
            return 0.0, ""
        if source_room_id == listener_room_id:
            return 1.0, "hier"

        tool_bonus = self._player_tool_bonus() if use_player_tools else 0.0
        best_volume = 0.0
        best_direction = ""
        for neighbor, transmission, direction in self._neighbors(listener_room_id):
            if transmission <= 0.01:
                continue
            remote_volume = self._max_transmission(
                source_room_id,
                neighbor,
                forbidden={listener_room_id},
            )
            effective = transmission
            if tool_bonus and transmission < 0.5:
                effective = min(1.0, transmission + tool_bonus)
            total = remote_volume * effective
            if total > best_volume:
                best_volume = total
                best_direction = self._direction_text(
                    listener_room_id, neighbor, direction
                )

        return (best_volume, best_direction) if best_volume >= 0.01 else (0.0, "")

    def _player_tool_bonus(self):
        return max(
            (
                float(obj.get("acoustic_boost", 0.0))
                for obj in self.game.objects.values()
                if obj.get("location") == LOC_INVENTORY
            ),
            default=0.0,
        )

    def _max_transmission(self, source_id, target_id, forbidden=None):
        if source_id == target_id:
            return 1.0
        forbidden = set(forbidden or ())
        queue = [(-1.0, 0, source_id)]
        best = {source_id: 1.0}

        while queue:
            negative_volume, distance, room_id = heapq.heappop(queue)
            volume = -negative_volume
            if room_id == target_id:
                return volume
            if distance >= self.max_propagation_distance:
                continue
            if volume < best.get(room_id, 0):
                continue
            for neighbor, transmission, _ in self._neighbors(room_id):
                if neighbor in forbidden or transmission <= 0.01:
                    continue
                propagated = volume * transmission
                if propagated <= 0.01 or propagated <= best.get(neighbor, 0):
                    continue
                best[neighbor] = propagated
                heapq.heappush(queue, (-propagated, distance + 1, neighbor))
        return 0.0

    def _neighbors(self, room_id):
        room = self.game.rooms.get(room_id, {})
        found = {}
        for direction, target_id in room.get("exits", {}).items():
            found[target_id] = (
                self._calculate_exit_transmission(room_id, direction),
                direction,
            )
        for target_id, data in room.get("acoustics", {}).items():
            transmission = (
                float(data)
                if isinstance(data, (int, float))
                else float(data.get("transmission", 0.0))
            )
            direction = (
                data.get("direction_text")
                if isinstance(data, dict)
                else None
            )
            if target_id not in found or transmission > found[target_id][0]:
                found[target_id] = (transmission, direction)
        return [
            (target_id, transmission, direction)
            for target_id, (transmission, direction) in found.items()
            if target_id in self.game.rooms
        ]

    def _direction_text(self, listener_id, neighbor_id, direction):
        translations = {
            "north": "aus Norden",
            "south": "aus Süden",
            "east": "aus Osten",
            "west": "aus Westen",
            "up": "von Oben",
            "down": "von Unten",
            "out": "von Draußen",
            "northeast": "aus Nordosten",
            "northwest": "aus Nordwesten",
            "southeast": "aus Südosten",
            "southwest": "aus Südwesten",
        }
        if direction in translations:
            return translations[direction]
        if direction:
            return str(direction)

        neighbor = self.game.rooms.get(neighbor_id, {})
        exits = neighbor.get("exits", {})
        if exits.get("down") == listener_id:
            return "von Oben (durch die Decke)"
        if exits.get("up") == listener_id:
            return "von Unten (durch den Boden)"
        return f"hinter der Wand zu {neighbor.get(ATTR_NAME, neighbor_id)}"

    def _calculate_exit_transmission(self, room_id, direction):
        transmission = ACOUSTIC_OPEN_AIR
        for obj in self.game.objects.values():
            if obj.get("location") != room_id or obj.get("linked_exit") != direction:
                continue
            if obj.get("is_open"):
                transmission = ACOUSTIC_OPEN_DOOR
            else:
                transmission = float(
                    obj.get("acoustic_damping", ACOUSTIC_CLOSED_DOOR)
                )
            break
        return transmission
