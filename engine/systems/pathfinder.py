from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

from engine.access import get_exit_doors
from engine.strings import Texts

if TYPE_CHECKING:
    from engine.game_state import GameState


class Pathfinder:
    def __init__(self, game: GameState) -> None:
        self.game: GameState = game

    def _is_exit_passable(self, room_id: str, direction: str) -> bool:
        return all(
            door.get("is_open", True)
            for door in get_exit_doors(self.game, room_id, direction)
        )

    def find_path(
        self,
        start_room_id: str | None,
        target_room_id: str | None,
        respect_blockers: bool = True,
    ) -> list[str] | None:
        if not start_room_id or not target_room_id:
            return None
        if start_room_id not in self.game.rooms or target_room_id not in self.game.rooms:
            return None
        if start_room_id == target_room_id:
            return []

        queue: deque[list[str]] = deque([[start_room_id]])
        visited: set[str] = {start_room_id}
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

    def get_direction_to(self, start_room: str, target_room_id: str) -> str | None:
        if start_room == target_room_id:
            return Texts.HERE
        path = self.find_path(start_room, target_room_id)
        if not path:
            return None
        next_step = path[0]
        for direction, room_id in self.game.rooms[start_room].get("exits", {}).items():
            if room_id == next_step:
                return Texts.direction_name(direction, long_form=True)
        return Texts.SOMEWHERE
