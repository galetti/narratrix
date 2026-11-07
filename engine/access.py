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
        return False
    level = int(top_entity.get("level", entity.get("level", 0)))
    if level < game.elevation:
        return allow_below
    return level <= game.elevation + upward_reach


def reach_error(game: GameState, entity: EntityData) -> str:
    top_entity, _, _ = _root_entity_and_location(game, entity)
    level = int(top_entity.get("level", entity.get("level", 0)))
    name = entity.get('name', 'Das Ziel')
    if level > game.elevation:
        return Texts.REACH_TOO_HIGH_GENERIC.format(name=name, level=level)
    return Texts.REACH_UNREACHABLE_GENERIC.format(name=name)
