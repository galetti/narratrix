# data/modules/deep_zero/chapters/ep1_deep_zero/config.py
from __future__ import annotations

from engine.schema import GameConfigData
from .rooms import ROOMS
from .items import ITEMS, COMBINATIONS
from .npcs import NPCS
from .events import NARRATIVE_MATRIX, EVENTS, QUESTS

CHAPTER_CONFIG: GameConfigData = {
    "meta": {
        "name": "Episode 1: Die Ankunft",
        "author": "Narratrix Team",
        "description": "Willkommen auf Deep Zero. Ein Tutorial für Ohren und Verstand.",
        "start_room": "room_outer_docking",
        "version": "2.0",
    },
    "theme": "deep_zero",
    "common_module": "data.modules.deep_zero.common.config",
    "asset_dir": "data/modules/deep_zero/assets/images",
    "rooms": ROOMS,
    "objects": ITEMS,
    "npcs": NPCS,
    "combinations": COMBINATIONS,
    "narrative_matrix": NARRATIVE_MATRIX,
    "events": EVENTS,
    "quests": QUESTS,
}
