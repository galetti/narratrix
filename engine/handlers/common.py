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
from engine.strings import Texts

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
    def get_contained_weight(
        game: GameState, obj_id: str, _visited: set[str] | None = None
    ) -> float:
        """Berechnet rekursiv das Gesamtgewicht aller in ``obj_id`` enthaltenen Objekte."""
        visited = _visited if _visited is not None else set()
        if obj_id in visited:
            return 0.0
        visited.add(obj_id)

        total = 0.0
        for child in game.objects.values():
            if child.get("location") != obj_id:
                continue
            unit_weight = float(child.get("weight", 0.0))
            count = int(child.get("count", 1)) if child.get("is_resource") else 1
            total += unit_weight * max(1, count)
            child_id = child.get(ATTR_ID)
            if isinstance(child_id, str):
                total += CommonHandler.get_contained_weight(game, child_id, visited)
        return total

    @staticmethod
    def get_total_weight(game: GameState, obj: dict[str, Any]) -> float:
        """Berechnet das Eigengewicht eines Objekts plus aller rekursiv enthaltenen Objekte."""
        unit_weight = float(obj.get("weight", 0.0))
        count = int(obj.get("count", 1)) if obj.get("is_resource") else 1
        own_weight = unit_weight * max(1, count)
        obj_id = obj.get(ATTR_ID)
        if not isinstance(obj_id, str):
            return own_weight
        return own_weight + CommonHandler.get_contained_weight(game, obj_id)

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
                npc_label += Texts.LEVEL_INFO_UP.format(level=npc_level)
            elif npc_level < game.elevation:
                npc_label += Texts.LEVEL_INFO_DOWN.format(level=npc_level)
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
