from engine.constants import *

ITEMS = {
    # --- COCKPIT ---
    "obj_cockpit_door": {
        "id": "obj_cockpit_door",
        "name": "Schott",
        "type": TYPE_CONTAINER,
        "location": "ship_cockpit",
        "linked_exit": "out", 
        "is_locked": True,
        "is_open": False,
        "desc": "Das massive Stahlschott ist verriegelt. Die Status-LED leuchtet rot.",
        "aliases": ["tür", "door", "ausgang"]
    },
    "obj_console": {
        "id": "obj_console",
        "name": "Steuerkonsole",
        "type": TYPE_SURFACE,
        "location": "ship_cockpit",
        "state": STATE_BROKEN, # WICHTIG: Damit 'repariere' Feedback gibt
        "desc": "Die Wartungsklappe hängt schief. Ein Kabelsalat quillt hervor.",
        "aliases": ["konsole", "terminal"]
    },
    "item_screwdriver": {
        "id": "item_screwdriver",
        "name": "Schraubendreher",
        "type": TYPE_ITEM,
        "location": "ship_cockpit",
        "weight": 0.2,
        "desc": "Ein verlässliches Werkzeug.",
        "aliases": ["werkzeug", "tool", "dreher", "schraubenzieher"]
    },
    "item_manual": {
        "id": "item_manual",
        "name": "Wartungshandbuch",
        "type": TYPE_ITEM,
        "location": "ship_cockpit",
        "desc": "Seite 1: 'Bei Stromausfall: Konsole überbrücken.'",
        "aliases": ["buch", "manual"]
    },
    
    # --- WEITERE RÄUME ---
    "item_broken_fuse": {
        "id": "item_broken_fuse",
        "name": "Durchgebrannte Sicherung",
        "type": TYPE_ITEM,
        "location": "ship_corridor",
        "weight": 0.1,
        "desc": "Schrott.",
    },
    "obj_workbench": {
        "id": "obj_workbench",
        "name": "Werkbank",
        "type": TYPE_SURFACE,
        "location": "ship_workshop",
        "desc": "Hier kannst du arbeiten.",
        "aliases": ["bank"]
    },
    "item_battery": {
        "id": "item_battery",
        "name": "Energiezelle",
        "type": TYPE_ITEM,
        "location": "ship_workshop",
        "weight": 0.5,
        "desc": "Voll geladen.",
        "aliases": ["batterie"]
    }
}