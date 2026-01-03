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
        # REZEPT 1: Konsole reparieren / Tür öffnen
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
                    "updates": {"state": "normal", "desc": "Die Konsole leuchtet grün. Tür-Override aktiv."}
                }
            ]
        },
        
        # HINT REZEPT: Schraubendreher + Tür (Damit der Spieler nicht verzweifelt)
        {
            "ingredients": ["obj_cockpit_door"],
            "tools": ["item_screwdriver"],
            "preserve": ["obj_cockpit_door"],
            "result": None,
            "message": "Das Schloss der Tür ist elektronisch. Du kommst hier nicht weiter. Vielleicht steuert die Konsole die Verriegelung?"
        },

        # REZEPT 2: ARIS reparieren
        {
            "ingredients": ["item_battery", "npc_aris"],
            "tools": [],
            "preserve": ["npc_aris"], 
            "result": None, 
            "message": "Du setzt die Batterie ein. Ein leises Surren ertönt, als Aris' Systeme hochfahren.",
            "effects": [
                {
                    "type": "update_object", 
                    "target": "npc_aris", 
                    "updates": {"state": "online"}
                },
                {
                    "type": "trigger_event", 
                    "id": "aris_online"
                }
            ]
        }
    ],
    
    "links": []
}