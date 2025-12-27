from .rooms import ROOMS
from .items import ITEMS, COMBINATIONS
from .npcs import NPCS
from .events import NARRATIVE_MATRIX

CHAPTER_CONFIG = {
    "meta": {
        "id": "ep0_arrival",
        "title": "Ankunft auf Omega-9",
        "start_room": "hub"
    },
    "rooms": ROOMS,
    "objects": ITEMS,
    "combinations": COMBINATIONS,
    "matrix": NARRATIVE_MATRIX,
    "npcs": NPCS,
    "links": [
        {
            "from_common": "ship_cockpit", 
            "dir": "out", 
            "to_chapter_tag": "common_dock"
        }
    ]
}