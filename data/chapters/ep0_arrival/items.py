from engine.constants import *

ITEMS = {
    # --- COCKPIT ---
    "obj_cockpit_door": {
        "id": "obj_cockpit_door",
        "name": "Cockpit-Schott",
        "type": TYPE_CONTAINER,
        "location": "ship_cockpit",
        "linked_exit": "east", # Angepasst: out -> east
        "is_locked": True,
        "is_open": False,
        "desc": "Die Mechanik ist verklemmt. Mit bloßen Händen kriegst du das nicht auf.",
        "aliases": ["tür", "schott"]
    },
    "obj_console": {
        "id": "obj_console",
        "name": "Steuerkonsole",
        "type": TYPE_SURFACE,
        "location": "ship_cockpit",
        "state": STATE_BROKEN,
        "desc": "Die Abdeckung hängt schief. Darunter siehst du die manuelle Entriegelung.",
        "aliases": ["konsole", "terminal"]
    },
    "item_screwdriver": {
        "id": "item_screwdriver",
        "name": "Schraubendreher",
        "type": TYPE_ITEM,
        "location": "ship_cockpit",
        "weight": 0.2,
        "desc": "Ein magnetischer Kreuzschlitz-Dreher. Standardausrüstung.",
        "aliases": ["werkzeug", "dreher"]
    },
    "item_manual": {
        "id": "item_manual",
        "name": "Wartungshandbuch",
        "type": TYPE_ITEM,
        "location": "ship_cockpit",
        "desc": "Seite 1: 'Bei Stromausfall: Konsole überbrücken.'",
        "aliases": ["buch", "manual"]
    },
    
    # --- KORRIDOR ---
    "obj_bio_door": {
        "id": "obj_bio_door",
        "name": "Bio-Schleuse",
        "type": TYPE_CONTAINER,
        "location": "ship_corridor",
        "linked_exit": "south",
        "is_locked": True,
        "is_open": False,
        "desc": "Ein schweres Sicherheitsschott mit Bio-Scanner. 'ZUTRITT NUR FÜR AUTORISIERTES PERSONAL'. Der Scanner leuchtet rot.",
        "aliases": ["schleuse", "tür", "bio-tür"]
    },
    "item_broken_fuse": {
        "id": "item_broken_fuse",
        "name": "Durchgebrannte Sicherung",
        "type": TYPE_ITEM,
        "location": "ship_corridor",
        "weight": 0.1,
        "desc": "Schrott.",
    },

    # --- WERKSTATT ---
    "obj_workbench": {
        "id": "obj_workbench",
        "name": "Werkbank",
        "type": TYPE_SURFACE,
        "location": "ship_workshop",
        "desc": "Eine stabile Arbeitsfläche. Hier liegt allerhand Kleinkram.",
        "aliases": ["bank", "tisch"]
    },
    "item_battery": {
        "id": "item_battery",
        "name": "Energiezelle",
        "type": TYPE_ITEM,
        "location": "ship_workshop",
        "weight": 0.5,
        "desc": "Eine Energiezelle, Typ X-9. Sie summt leise.",
        "aliases": ["batterie", "zelle", "akku"]
    },
    
    # --- SCHACHT ITEMS ---
    "obj_maintenance_hatch": {
        "id": "obj_maintenance_hatch",
        "name": "Wartungsluke",
        "type": TYPE_CONTAINER,
        "location": "maint_shaft_2",
        "linked_exit": "east", # Angepasst: forward -> east
        "is_locked": True,
        "is_open": False,
        "desc": "Eine rostige Luke blockiert den Weg nach Osten. Sie hat kein Schloss, nur ein digitales Interface.",
        "aliases": ["luke", "hatch"]
    }
}