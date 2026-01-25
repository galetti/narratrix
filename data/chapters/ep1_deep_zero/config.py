# narratrix_engine/data/chapters/ep1_arrival/config.py
from .rooms import ROOMS
from .items import ITEMS, COMBINATIONS
from .npcs import NPCS
from .events import NARRATIVE_MATRIX, EVENTS, QUESTS

CHAPTER_CONFIG = {
    "meta": {
        "name": "Episode 1: Die Ankunft",
        "author": "Narratrix Team",
        "description": "Willkommen auf Deep Zero. Ein Tutorial für Ohren und Verstand.",
        "start_room": "room_outer_docking",
        "version": "2.0"
    },
    "rooms": ROOMS,
    "objects": ITEMS,
    "npcs": NPCS,
    "combinations": COMBINATIONS,
    "narrative_matrix": NARRATIVE_MATRIX,
    "events": EVENTS,
    "quests": QUESTS
}