# data/common/items.py
from engine.constants import *

COMMON_ITEMS = {
    # --- Spieler Start-Ausrüstung ---
    "multitool": {
        "id": "multitool", 
        "name": "Omni-Tool", 
        "aliases": ["tool", "werkzeug", "scanner", "multitool"], 
        "location": LOC_INVENTORY, 
        "type": TYPE_ITEM, 
        "weight": 0.5, # Handlich
        "matter": MATTER_SOLID, 
        "desc": "Ein Standard-Werkzeug für Wartung und Hacking. Unverzichtbar."
    },
    "id_card": {
        "id": "id_card", 
        "name": "USC-Dienstausweis", 
        "aliases": ["ausweis", "karte", "id", "dienstausweis"], 
        "location": LOC_INVENTORY, 
        "type": TYPE_ITEM, 
        "weight": 0.01, # Sehr leicht
        "matter": MATTER_SOLID, 
        "desc": "Ausgestellt vom United Space Command. Rang: Spezialist. Autorität: Begrenzt."
    },
    
    # --- Schiff-Inventar ---
    "ship_locker": {
        "id": "ship_locker", 
        "name": "Spind", 
        "aliases": ["schrank"], 
        "location": "ship_quarters", 
        "type": TYPE_CONTAINER, 
        "weight": float('inf'), # Fest verbaut
        "is_open": False,
        "desc": "Hier bewahrst du deine Ausrüstung auf."
    },
    "bed": {
        "id": "bed", 
        "name": "Koje", 
        "aliases": ["bett"], 
        "location": "ship_quarters", 
        "type": TYPE_SURFACE, 
        "weight": float('inf'), # Fest verbaut
        "desc": "Nicht sehr bequem, aber deins."
    }
}
