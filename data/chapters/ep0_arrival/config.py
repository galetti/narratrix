from .rooms import ROOMS
from .items import ITEMS
from .npcs import NPCS
from .events import MATRIX
from .quests import QUESTS

CHAPTER_CONFIG = {
    "meta": {
        "title": "Ep0: Ankunft",
        "author": "System",
        "start_room": "ship_cockpit"
    },
    "rooms": ROOMS,
    "objects": ITEMS,
    "npcs": NPCS,
    "narrative_matrix": MATRIX,
    "quests": QUESTS,
    
    "combinations": [
        {
            "ingredients": ["obj_console"],
            "tools": ["item_screwdriver"],
            "preserve": ["obj_console"],
            "message": "Du schraubst die Abdeckung ab und schließt den Notfall-Kontakt kurz. Das Schott zischt und gleitet auf!",
            "effects": [
                {
                    "type": "update_object",
                    "target": "obj_cockpit_door",
                    "updates": {"is_locked": False, "is_open": True, "desc": "Das Schott steht offen."}
                },
                {
                    "type": "update_object",
                    "target": "obj_console",
                    "updates": {"state": "normal"}
                }
            ]
        },
        # FIX: Doppelte Absicherung für ARIS
        {
            "ingredients": ["item_battery", "npc_aris"],
            "preserve": ["npc_aris"], 
            "message": "Die Energiezelle passt perfekt. Systeme initialisieren...",
            "effects": [
                # 1. Direktes Update (falls Crafting System NPCs findet)
                {
                    "type": "update_object", 
                    "target": "npc_aris", 
                    "updates": {"state": "online"}
                },
                # 2. Event Trigger (sollte auch State setzen und Quest updaten)
                {
                    "type": "trigger_event", 
                    "id": "aris_online"
                }
            ]
        }
    ],
    
    "links": []
}