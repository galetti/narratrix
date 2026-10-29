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
        if obj.get('linked_exit'): return False
        
        if obj.get('type') == TYPE_SURFACE: return True
        if obj.get('type') == TYPE_CONTAINER and obj.get('is_open', True): return True
        return False

    @staticmethod
    def is_held_by_player(game: GameState, obj: dict[str, Any]) -> bool:
        """Prüft rekursiv, ob sich ein Objekt im Inventar des Spielers befindet."""
        current: dict[str, Any] = obj
        visited: set[str | None] = set()
        while True:
            current_id = current.get(ATTR_ID)
            if current_id in visited: return False
            visited.add(current_id)
            loc = current['location']
            if loc == LOC_INVENTORY: return True
            if loc in game.rooms: return False 
            parent = game.objects.get(loc)
            if not parent: return False
            current = parent

    @staticmethod
    def format_contents_recursive(game: GameState, obj_id: str, depth: int = 0) -> str:
        """Erzeugt einen String für den Inhalt, inklusive Unter-Containern."""
        if depth > 5: return "" 
        
        contents = [sub for sub in game.objects.values() if sub['location'] == obj_id]
        if not contents: return ""
        
        names: list[str] = []
        for item in contents:
            name = item[ATTR_NAME]
            if CommonHandler.is_open_container(item):
                sub_text = CommonHandler.format_contents_recursive(game, item[ATTR_ID], depth+1)
                if sub_text: name += f" ({sub_text})"
            names.append(name)
        return ", ".join(names)
