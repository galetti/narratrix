from engine.constants import *

ITEMS = {
    # SCENERY
    "terminal": {
        "id": "terminal", "name": "Info-Terminal", "aliases": ["computer"], 
        "location": "hub", "type": TYPE_SURFACE, "weight": float('inf'), 
        "desc": "Zeigt den Dienstplan: 19:00 Abendessen."
    },
    "replicator": {
        "id": "replicator", "name": "Nahrungs-Replikator", "aliases": ["automat"], 
        "location": "cantina", "type": TYPE_SURFACE, "weight": float('inf'),
        "desc": "Er bietet 'Standard-Menü A' an."
    },
    "core": {
        "id": "core", "name": "Reaktorkern", "aliases": ["kern"], "location": "reactor", "type": TYPE_SCENERY, "weight": float('inf'),
        "desc": "Läuft mit 98% Effizienz.", "temp": 40
    },
    "med_table": {
        "id": "med_table", "name": "Labortisch", "aliases": ["tisch"], "location": "medbay", "type": TYPE_SURFACE, "weight": float('inf'), 
        "desc": "Ein sauberer Arbeitstisch."
    },
    
    # ITEMS
    "scale": {
        "id": "scale", "name": "Präzisionswaage", "aliases": ["waage"], "location": "med_table", "type": TYPE_SURFACE, "weight": 2.0, 
        "desc": "Eine digitale Waage. Fiona nutzt sie für ihre Proben."
    },
    "alien_fruit": {
        "id": "alien_fruit", "name": "Xeno-Frucht", "aliases": ["frucht", "obst"], "location": "medbay", "type": TYPE_ITEM, "weight": 0.35, "matter": MATTER_SOLID,
        "desc": "Eine seltsam leuchtende Frucht. Fiona untersucht sie."
    },
    "gift": {
        "id": "gift", "name": "Schachtel Pralinen", "aliases": ["pralinen", "geschenk"], "location": "ship_quarters", "type": TYPE_ITEM, "weight": 0.5, "matter": MATTER_SOLID,
        "desc": "Ein Mitbringsel von der Erde für die Crew."
    }
}

COMBINATIONS = [
    # Hier könnte man die Pralinen an jemanden geben -> Dialog-Trigger
]