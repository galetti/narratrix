# data/chapters/ep1_station/config.py
from .rooms import ROOMS
from .items import ITEMS, COMBINATIONS
from .events import NARRATIVE_MATRIX
from .events_flavor import FLAVOR_MATRIX # Import der Flavor Events
from .npcs import NPCS

# Kombiniere Story- und Flavor-Events
FULL_MATRIX = NARRATIVE_MATRIX + FLAVOR_MATRIX

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
    "matrix": FULL_MATRIX, # Nutzung der kombinierten Matrix
    "npcs": NPCS,
    
    # Explizite Definition der Links zum Common Layer
    "links": [
        {
            "from_common": "ship_cockpit", 
            "dir": "out", 
            "to_chapter_tag": "common_dock"
        }
    ]
}
