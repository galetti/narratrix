# data/modules/test_lab/chapters/sandbox/config.py
from __future__ import annotations

from engine.schema import GameConfigData
from .rooms import ROOMS
from .items import ITEMS, COMBINATIONS
from .npcs import NPCS
from .events import NARRATIVE_MATRIX, EVENTS, QUESTS

# WICHTIG: Der StoryLoader erwartet "CHAPTER_CONFIG" als Variablennamen!
CHAPTER_CONFIG: GameConfigData = {
    "meta": {
        "name": "Testlabor: Mechanik- & System-Sandbox",
        "author": "System",
        "description": "Modulare Testumgebung zur Demonstration von Physik-, Akustik-, Kletter- und Dialog-Mechaniken.",
        "start_room": "central_hub",
        "version": "2.1",
    },
    "theme": "lab",
    "common_module": None,
    "asset_dir": "data/modules/test_lab/assets/images",
    "rooms": ROOMS,
    "objects": ITEMS,
    "npcs": NPCS,
    "combinations": COMBINATIONS,
    "narrative_matrix": NARRATIVE_MATRIX,
    "events": EVENTS,
    "quests": QUESTS,
}
