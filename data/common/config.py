# data/common/config.py
from .rooms import COMMON_ROOMS
from .items import COMMON_ITEMS
from .npcs import COMMON_NPCS
from .events import COMMON_MATRIX

# Manifest für Layer 1
COMMON_CONFIG = {
    "rooms": COMMON_ROOMS,
    "objects": COMMON_ITEMS,
    "npcs": COMMON_NPCS,
    "matrix": COMMON_MATRIX,
    "events": [],
    "quests": {},
    "combinations": []
}
