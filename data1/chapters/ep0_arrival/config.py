from .rooms import ROOMS
from .items import ITEMS
from .npcs import NPCS
from .events import MATRIX
from .quests import QUESTS # NEU

CHAPTER_CONFIG = {
    "meta": {
        "title": "Episode 0: Ankunft",
        "author": "System",
        "version": "1.0",
        "start_room": "ship_cockpit"
    },
    "rooms": ROOMS,
    "objects": ITEMS,
    "npcs": NPCS,
    "narrative_matrix": MATRIX,
    "combinations": [],
    "quests": QUESTS, # NEU: Quests registrieren
    
    # Links definieren Übergänge zwischen Common-Rooms und Chapter-Rooms
    "links": [
        {
            "from_common": "docking_bay_alpha", 
            "dir": "west", 
            "to_chapter_tag": "ship_airlock"
        }
    ]
}