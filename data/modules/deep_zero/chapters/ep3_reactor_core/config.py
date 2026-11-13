# data/modules/deep_zero/chapters/ep3_reactor_core/config.py
from __future__ import annotations

from engine.schema import GameConfigData
from .rooms import ROOMS
from .items import ITEMS, COMBINATIONS
from .npcs import NPCS
from .events import NARRATIVE_MATRIX, EVENTS, QUESTS

CHAPTER_CONFIG: GameConfigData = {
    "meta": {
        "name": "Episode 3: Der Reaktorkern",
        "author": "Narratrix Team",
        "description": "Das Finale von Deep Zero. Stabilisiere den Dunkle-Materie-Reaktorkern vor der kritischen Resonanz.",
        "start_room": "reactor_bridge",
        "version": "2.0",
    },
    "theme": "reactor",
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
