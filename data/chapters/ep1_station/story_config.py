# data/chapters/ep1_station/config.py
from .rooms import ROOMS
from .items import ITEMS, COMBINATIONS
from .events import NARRATIVE_MATRIX

# Manifest für den Loader
CHAPTER_CONFIG = {
    "meta": {
        "id": "ep1_station",
        "title": "Echo der Station Omega-9",
        "start_room": "hub"
    },
    "rooms": ROOMS,
    "objects": ITEMS,
    "combinations": COMBINATIONS,
    "matrix": NARRATIVE_MATRIX,
    "npcs": [] # Keine lokalen NPCs in diesem Kapitel (nur Globale)
}
