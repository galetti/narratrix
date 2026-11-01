# engine/handlers/common.py
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from engine.constants import (
    ATTR_ID,
    ATTR_NAME,
    LOC_INVENTORY,
    TYPE_CONTAINER,
    TYPE_SURFACE,
)

if TYPE_CHECKING:
    from engine.game_state import GameState


class CommonHandler:
    """
    Hilfsfunktionen, die von verschiedenen Handlern (Exploration, Inventory, etc.)
    genutzt werden, um Code-Duplizierung zu vermeiden.
    """

    @staticmethod
    def is_open_container(obj: dict[str, Any]) -> bool:
        """Prüft ob ein Objekt ein zugänglicher Container ist."""
        # Türen (linked_exit) werden nicht als Container zum "Reinschauen" behandelt
        if obj.get("linked_exit"):
            return False

        if obj.get("type") == TYPE_SURFACE:
            return True
        if obj.get("type") == TYPE_CONTAINER and obj.get("is_open", True):
            return True
        return False

    @staticmethod
    def is_contained_in(game: GameState, obj: dict[str, Any], target_location: str) -> bool:
        """Prüft rekursiv, ob sich ein Objekt innerhalb einer Ziel-Location/eines Containers befindet."""
        current: dict[str, Any] = obj
        visited: set[str | None] = set()
        while True:
            current_id = current.get(ATTR_ID)
            if current_id in visited:
                return False
            visited.add(current_id)
            loc = current.get("location")
            if loc == target_location:
                return True
            if loc in game.rooms:
                return False
            parent = game.objects.get(loc)
            if not parent:
                return False
            current = parent

    @staticmethod
    def is_held_by_player(game: GameState, obj: dict[str, Any]) -> bool:
        """Prüft rekursiv, ob sich ein Objekt im Inventar des Spielers befindet."""
        return CommonHandler.is_contained_in(game, obj, LOC_INVENTORY)

    @staticmethod
    def format_visible_npcs(game: GameState, room_id: str) -> list[str]:
        """Ermittelt und formatiert anwesende NPCs im Raum inklusive Höhenangaben."""
        visible_npcs: list[str] = []
        for npc in game.npcs:
            if npc.get("location") != room_id:
                continue
            npc_level = int(npc.get("level", 0))
            npc_label = npc[ATTR_NAME]
            if npc_level > game.elevation:
                npc_label += f" (oben auf Ebene {npc_level})"
            elif npc_level < game.elevation:
                npc_label += f" (unten auf Ebene {npc_level})"
            visible_npcs.append(npc_label)
        return visible_npcs

    @staticmethod
    def format_contents_recursive(game: GameState, obj_id: str, depth: int = 0) -> str:
        """Erzeugt einen String für den Inhalt, inklusive Unter-Containern."""
        if depth > 5:
            return ""

        contents = [sub for sub in game.objects.values() if sub["location"] == obj_id]
        if not contents:
            return ""

        names: list[str] = []
        for item in contents:
            name = item[ATTR_NAME]
            if CommonHandler.is_open_container(item):
                sub_text = CommonHandler.format_contents_recursive(game, item[ATTR_ID], depth + 1)
                if sub_text:
                    name += f" ({sub_text})"
            names.append(name)
        return ", ".join(names)
