# data/common/items.py
# Layer 1: Items, die der Spieler immer besitzt oder die zum Schiff gehören.

from engine.constants import *

COMMON_ITEMS = {
    # --- Spieler Start-Ausrüstung ---
    "multitool": {
        "id": "multitool", 
        "name": "Omni-Tool", 
        "aliases": ["tool", "werkzeug", "scanner", "multitool"], # Alias 'multitool' hinzugefügt
        "location": LOC_INVENTORY, 
        "type": TYPE_ITEM, 
        "movable": True, 
        "matter": MATTER_SOLID, 
        "desc": "Ein Standard-Werkzeug für Wartung und Hacking. Unverzichtbar."
    },
    "id_card": {
        "id": "id_card", 
        "name": "BSI-Ausweis", 
        "aliases": ["ausweis", "karte", "id"], 
        "location": LOC_INVENTORY, 
        "type": TYPE_ITEM, 
        "movable": True, 
        "matter": MATTER_SOLID, 
        "desc": "Rang: Spezialist. Autorität: Begrenzt."
    },
    
    # --- Schiff-Inventar ---
    "ship_locker": {
        "id": "ship_locker", 
        "name": "Spind", 
        "aliases": ["schrank"], 
        "location": "ship_quarters", 
        "type": TYPE_CONTAINER, 
        "movable": False, 
        "is_open": False,
        "desc": "Hier bewahrst du deine Ausrüstung auf."
    },
    "bed": {
        "id": "bed", 
        "name": "Koje", 
        "aliases": ["bett"], 
        "location": "ship_quarters", 
        "type": TYPE_SURFACE, 
        "movable": False, 
        "desc": "Nicht sehr bequem, aber deins."
    }
}
