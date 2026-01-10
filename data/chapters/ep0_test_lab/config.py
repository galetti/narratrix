# narratrix_engine/data/chapters/ep0_test_lab/config.py
from .rooms import ROOMS
from .items import ITEMS, COMBINATIONS
from .npcs import NPCS
from .events import NARRATIVE_MATRIX, EVENTS

# WICHTIG: Der StoryLoader erwartet "CHAPTER_CONFIG" als Variablennamen!
CHAPTER_CONFIG = {
    "meta": {
        "name": "Episode 0: Test Labor",
        "author": "System",
        "description": "Ein Test-Szenario für vertikale Akustik und KI.",
        "start_room": "central_hub",
        "version": "1.0"
    },
    "rooms": ROOMS,
    "objects": ITEMS,
    "npcs": NPCS,
    "combinations": COMBINATIONS,
    "narrative_matrix": NARRATIVE_MATRIX,
    "events": EVENTS,
    "quests": {}
}