# narratrix_engine/data/chapters/ep0_test_lab/config.py
from __future__ import annotations

from engine.schema import GameConfigData
from .rooms import ROOMS
from .items import ITEMS, COMBINATIONS
from .npcs import NPCS
from .events import NARRATIVE_MATRIX, EVENTS, QUESTS

# WICHTIG: Der StoryLoader erwartet "CHAPTER_CONFIG" als Variablennamen!
CHAPTER_CONFIG: GameConfigData = {
    "meta": {
        "name": "Episode 0: Test Labor",
        "author": "System",
        "description": "Ein Test-Szenario für vertikale Akustik, Physik, Container, KI und das Resonanz-Rätsel.",
        "start_room": "central_hub",
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
