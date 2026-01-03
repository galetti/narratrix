from engine.constants import *

ITEMS = {
    # --- SCENERY (Intakt) ---
    "terminal": {
        "id": "terminal", "name": "Info-Terminal", "aliases": ["computer"], 
        "location": "hub", "type": TYPE_SURFACE, "weight": float('inf'), 
        "desc": "Zeigt den Dienstplan: 19:00 Abendessen."
    },
    "replicator": {
        "id": "replicator", "name": "Nahrungs-Replikator", "aliases": ["automat"], 
        "location": "cantina", "type": TYPE_SURFACE, "weight": float('inf'),
        "desc": "Er summt leise. Das Display zeigt: 'Menü des Tages: Curry-Reis'."
    },
    "core": {
        "id": "core", "name": "Reaktorkern", "aliases": ["kern"], "location": "reactor", "type": TYPE_SCENERY, "weight": float('inf'),
        "desc": "Er leuchtet in einem beruhigenden Blau. Die Temperaturanzeige ist im grünen Bereich.", "temp": 35
    },
    "med_table": {
        "id": "med_table", "name": "Labortisch", "aliases": ["tisch"], "location": "medbay", "type": TYPE_SURFACE, "weight": float('inf'), 
        "desc": "Ein sauberer Arbeitstisch voller Petrischalen und Notizen."
    },
    
    # --- ITEMS (Rätsel & Fluff) ---
    "scale": {
        "id": "scale", "name": "Präzisionswaage", "aliases": ["waage"], "location": "med_table", "type": TYPE_SURFACE, "weight": 2.0, 
        "is_scale": True, # NEU: Generic Property
        "desc": "Eine digitale Waage. Fiona nutzt sie für ihre Proben."
    },
    "alien_fruit": {
        "id": "alien_fruit", "name": "Xeno-Frucht", "aliases": ["frucht", "obst", "probe"], "location": "medbay", "type": TYPE_ITEM, "weight": 0.35, "matter": MATTER_SOLID,
        "desc": "Eine seltsam leuchtende Frucht. Sie riecht nach Zimt und Ozon."
    },
    "gift": {
        "id": "gift", "name": "Schachtel Pralinen", "aliases": ["pralinen", "geschenk", "schokolade"], "location": "ship_quarters", "type": TYPE_ITEM, "weight": 0.5, "matter": MATTER_SOLID,
        "desc": "Echte belgische Schokolade. Ein seltenes Luxusgut hier draußen. Perfekt als Gastgeschenk."
    },
    "curry": {
        "id": "curry", "name": "Schüssel Curry", "aliases": ["essen", "curry", "reis"], "location": LOC_VOID, "type": TYPE_ITEM, "weight": 0.4, "matter": MATTER_SOLID,
        "desc": "Es dampft und riecht überraschend gut."
    }
}

COMBINATIONS = [
    {
        "items": ["replicator"],
        "tools": ["id_card"], 
        "result": "curry",
        "consume": [], 
        "message": "Der Replikator piept fröhlich und materialisiert eine dampfende Schüssel Curry."
    }
]