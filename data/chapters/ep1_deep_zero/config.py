# narratrix_engine/data/chapters/ep1_deep_zero/config.py
from .rooms import ROOMS
from .items import ITEMS, COMBINATIONS
from .npcs import NPCS
from .events import NARRATIVE_MATRIX, EVENTS, QUESTS

CHAPTER_CONFIG = {
    "meta": {
        "name": "Episode 1: Die Routine",
        "author": "Narratrix Team",
        "description": "Ein ganz normaler Tag auf der Deep Zero Station. Oder?",
        "start_room": "room_quarters_aris",
        "version": "1.0"
    },
    "rooms": ROOMS,
    "objects": ITEMS,
    "npcs": NPCS,
    "combinations": COMBINATIONS,
    "narrative_matrix": NARRATIVE_MATRIX,
    "events": EVENTS,
    "quests": QUESTS
}