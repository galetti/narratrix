from __future__ import annotations

from typing import TYPE_CHECKING

from engine.constants import ATTR_ID, LOC_INVENTORY, TYPE_CONTAINER
from engine.schema import EntityData
from engine.strings import Texts

if TYPE_CHECKING:
    from engine.game_state import GameState


def _root_entity_and_location(
    game: GameState, entity: EntityData
) -> tuple[EntityData, str | None, bool]:
    """Walk up the containment chain to the room/inventory root.

    Returns ``(top_entity, root_location, blocked_by_closed_container)``.
    """
    current: EntityData = entity
    visited: set[str] = set()
    while True:
        current_id = current.get(ATTR_ID)
        if isinstance(current_id, str):
            if current_id in visited:
                return current, None, True
            visited.add(current_id)
        loc = current.get("location")
        if not isinstance(loc, str):
            return current, None, False
        if loc == LOC_INVENTORY or loc in game.rooms:
            return current, loc, False
        parent = game.objects.get(loc)
        if not parent:
            return current, loc, False
        if parent.get("type") == TYPE_CONTAINER and not parent.get("is_open", True):
            return parent, None, True
        current = parent


def is_directly_reachable(
    game: GameState,
    entity: EntityData,
    upward_reach: int = 1,
    allow_below: bool = False,
) -> bool:
    """Return whether the player can physically interact with an entity."""

    top_entity, root_loc, blocked = _root_entity_and_location(game, entity)
    if blocked:
        return False
    if root_loc == LOC_INVENTORY:
        return True
    if root_loc != game.location:
        if not is_connecting_door(game, top_entity, game.location):
            return False
    level = int(top_entity.get("level", entity.get("level", 0)))
    if level < game.elevation:
        return allow_below
    return level <= game.elevation + upward_reach


def is_connecting_door(game: GameState, entity: EntityData, room_id: str) -> bool:
    """Return whether entity is a door connecting room_id with an adjacent room."""
    linked = entity.get("linked_exit")
    if not isinstance(linked, str) or not linked:
        return False
    loc = entity.get("location")
    if not isinstance(loc, str) or not loc:
        return False
    current_room = game.rooms.get(room_id, {})
    if loc == room_id:
        target = current_room.get("exits", {}).get(linked)
        return bool(target and target in game.rooms)
    if loc in current_room.get("exits", {}).values():
        neighbor_room = game.rooms.get(loc, {})
        if neighbor_room.get("exits", {}).get(linked) == room_id:
            return True
    return False


def get_connecting_doors(game: GameState, room_id: str) -> list[EntityData]:
    """Return all doors accessible from room_id (both locally placed and from adjacent rooms)."""
    current_room = game.rooms.get(room_id, {})
    doors: list[EntityData] = []
    exits = current_room.get("exits", {})
    for obj in game.objects.values():
        linked = obj.get("linked_exit")
        if not linked:
            continue
        loc = obj.get("location")
        if loc == room_id:
            doors.append(obj)
        elif loc in exits.values():
            neighbor_room = game.rooms.get(loc, {})
            if neighbor_room.get("exits", {}).get(linked) == room_id:
                if obj not in doors:
                    doors.append(obj)
    return doors


def get_door_target_room(
    game: GameState, door: EntityData, from_room_id: str
) -> str | None:
    """Return the ID of the room on the other side of the door when viewed from from_room_id."""
    linked = door.get("linked_exit")
    loc = door.get("location")
    if not linked or not loc:
        return None
    if loc == from_room_id:
        return game.rooms.get(from_room_id, {}).get("exits", {}).get(linked)
    neighbor_room = game.rooms.get(loc, {})
    if neighbor_room.get("exits", {}).get(linked) == from_room_id:
        return loc
    return None


def get_door_direction(
    game: GameState, door: EntityData, from_room_id: str
) -> str | None:
    """Return the exit direction of the door when viewed from from_room_id."""
    linked = door.get("linked_exit")
    loc = door.get("location")
    if not linked or not loc:
        return None
    if loc == from_room_id:
        return linked
    target_room_id = get_door_target_room(game, door, from_room_id)
    if not target_room_id:
        return None
    for direction, target in game.rooms.get(from_room_id, {}).get("exits", {}).items():
        if target == target_room_id:
            return direction
    return None


def reach_error(game: GameState, entity: EntityData) -> str:
    top_entity, _, _ = _root_entity_and_location(game, entity)
    level = int(top_entity.get("level", entity.get("level", 0)))
    name = entity.get('name', 'Das Ziel')
    if level > game.elevation:
        return Texts.REACH_TOO_HIGH_GENERIC.format(name=name, level=level)
    return Texts.REACH_UNREACHABLE_GENERIC.format(name=name)
