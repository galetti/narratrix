from collections import deque


class Pathfinder:
    def __init__(self, game):
        self.game = game

    def _is_exit_passable(self, room_id, direction):
        blockers = [
            obj
            for obj in self.game.objects.values()
            if obj.get("location") == room_id and obj.get("linked_exit") == direction
        ]
        return all(obj.get("is_open", True) for obj in blockers)

    def find_path(self, start_room_id, target_room_id, respect_blockers=True):
        if start_room_id not in self.game.rooms or target_room_id not in self.game.rooms:
            return None
        if start_room_id == target_room_id:
            return []

        queue = deque([[start_room_id]])
        visited = {start_room_id}
        while queue:
            path = queue.popleft()
            current = path[-1]
            room = self.game.rooms[current]
            for direction, target in room.get("exits", {}).items():
                if respect_blockers and not self._is_exit_passable(current, direction):
                    continue
                if target in visited or target not in self.game.rooms:
                    continue
                new_path = [*path, target]
                if target == target_room_id:
                    return new_path[1:]
                visited.add(target)
                queue.append(new_path)
        return None

    def get_direction_to(self, start_room, target_room_id):
        if start_room == target_room_id:
            return "hier"
        path = self.find_path(start_room, target_room_id)
        if not path:
            return None
        next_step = path[0]
        translations = {
            "north": "Norden",
            "south": "Süden",
            "east": "Osten",
            "west": "Westen",
            "up": "Oben",
            "down": "Unten",
            "out": "Ausgang",
            "northeast": "Nordosten",
            "northwest": "Nordwesten",
            "southeast": "Südosten",
            "southwest": "Südwesten",
        }
        for direction, room_id in self.game.rooms[start_room].get("exits", {}).items():
            if room_id == next_step:
                return translations.get(direction, direction)
        return "irgendwo"
