# narratrix_engine/data/chapters/ep2_habitat_sector/config.py
from __future__ import annotations

from engine.schema import GameConfigData
from .rooms import ROOMS
from .items import ITEMS, COMBINATIONS
from .npcs import NPCS
from .events import NARRATIVE_MATRIX, EVENTS, QUESTS

CHAPTER_CONFIG: GameConfigData = {
    "meta": {
        "name": "Episode 2: Der Habitat-Sektor",
        "author": "Narratrix Team",
        "description": "Willkommen im Wohnbereich von Deep Zero. Rette die Biosphäre vor dem Überdruckkollaps.",
        "start_room": "quarters_airlock",
        "version": "2.0",
    },
    "rooms": ROOMS,
    "objects": ITEMS,
    "npcs": NPCS,
    "combinations": COMBINATIONS,
    "narrative_matrix": NARRATIVE_MATRIX,
    "events": EVENTS,
    "quests": QUESTS,
}
