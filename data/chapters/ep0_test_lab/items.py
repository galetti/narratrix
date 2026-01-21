# narratrix_engine/data/chapters/ep0_test_lab/items.py
from engine.constants import *

if 'TYPE_FIXTURE' not in globals():
    TYPE_FIXTURE = "fixture"

ITEMS = {
    "red_key": {
        ATTR_ID: "red_key",
        ATTR_NAME: "roter Schlüssel",
        ATTR_DESC: "Ein kleiner Schlüssel mit rotem Griff.",
        ATTR_ALIASES: ["schlüssel", "rot", "key"],
        "location": "test_chamber",
        "type": TYPE_ITEM,
        ATTR_WEIGHT: 1,
        "level": 0 # Am Boden
    },
    "blue_key": {
        ATTR_ID: "blue_key",
        ATTR_NAME: "blauer Schlüssel",
        ATTR_DESC: "Ein schwerer Schlüssel aus blauem Metall.",
        ATTR_ALIASES: ["schlüssel", "blau", "key"],
        "location": "test_chamber",
        "type": TYPE_ITEM,
        ATTR_WEIGHT: 1,
        "level": 0
    },
    "noisy_machine": {
        ATTR_ID: "noisy_machine",
        ATTR_NAME: "Lärmmaschine",
        ATTR_DESC: "Eine Maschine, die Krach macht.",
        "location": "lower_deck",
        "type": TYPE_FIXTURE,
        "state": "off"
    },
    
    # NEU: Hohes Regal und unerreichbares Item
    "high_shelf": {
        ATTR_ID: "high_shelf",
        ATTR_NAME: "hohes Regal",
        ATTR_DESC: "Ein sehr hohes Lagerregal an der Wand. Die oberste Ablage ist auf Ebene 2.",
        ATTR_ALIASES: ["regal", "shelf"],
        "location": "test_chamber",
        "type": TYPE_FIXTURE,
        "climbable": True, # Man kann drauf klettern!
        "target_elevation": 2 # Klettern bringt einen auf Ebene 2
    },
    "access_card": {
        ATTR_ID: "access_card",
        ATTR_NAME: "Zugangskarte",
        ATTR_DESC: "Eine weiße Plastikkarte mit Magnetstreifen.",
        ATTR_ALIASES: ["karte", "card", "zugang"],
        "location": "test_chamber", # Im Raum...
        "type": TYPE_ITEM,
        "level": 2, # ...aber weit oben!
        ATTR_WEIGHT: 0.1
    },

    # NEU: Werkzeug mit Reichweite
    "grabber": {
        ATTR_ID: "grabber",
        ATTR_NAME: "Greifzange",
        ATTR_DESC: "Eine lange Stange mit einem Greifmechanismus am Ende.",
        ATTR_ALIASES: ["zange", "greifer", "stange"],
        "location": "central_hub",
        "type": TYPE_ITEM,
        "is_tool": True,
        "reach": 2, # Kann 2 Ebenen überbrücken
        ATTR_WEIGHT: 1.5
    },

    # Ressourcen
    "scrap_metal_1": {
        ATTR_ID: "scrap_metal",
        ATTR_NAME: "Metallschrott",
        ATTR_DESC: "Verrostete Metallteile.",
        ATTR_ALIASES: ["schrott", "metall", "scrap"],
        "location": "lower_deck",
        "type": TYPE_ITEM,
        "is_resource": True,
        "count": 3,
        ATTR_WEIGHT: 0.5 
    },
    "scrap_metal_2": {
        ATTR_ID: "scrap_metal", 
        ATTR_NAME: "Metallschrott",
        ATTR_DESC: "Ein einzelnes Stück Metall.",
        ATTR_ALIASES: ["schrott", "metall", "scrap"],
        "location": "upper_deck",
        "type": TYPE_ITEM,
        "is_resource": True,
        "count": 1,
        ATTR_WEIGHT: 0.5
    },
    "wire_coil": {
        ATTR_ID: "wire",
        ATTR_NAME: "Kupferkabel",
        ATTR_DESC: "Eine Spule mit Draht.",
        ATTR_ALIASES: ["kabel", "draht", "wire"],
        "location": "central_hub",
        "type": TYPE_ITEM,
        "is_resource": True,
        "count": 2,
        ATTR_WEIGHT: 0.2
    },
    
    "workbench": {
        ATTR_ID: "workbench",
        ATTR_NAME: "Werkbank",
        ATTR_DESC: "Eine robuste Werkbank mit Schraubstock.",
        ATTR_ALIASES: ["bank", "tisch"],
        "location": "lower_deck",
        "type": TYPE_FIXTURE
    },
    
    "improvised_shiv": {
        ATTR_ID: "shiv",
        ATTR_NAME: "Improvisiertes Messer",
        ATTR_DESC: "Ein geschärftes Stück Metall mit Kabel umwickelt.",
        ATTR_ALIASES: ["messer", "dolch", "shiv"],
        "location": LOC_VOID, 
        "type": TYPE_ITEM,
        ATTR_WEIGHT: 1,
        "damage": 2
    }
}

COMBINATIONS = [
    {
        "verb": "use", 
        "items": ["scrap_metal", "workbench"], 
        "ingredients": {"scrap_metal": 2, "wire": 1}, 
        "station": "workbench", 
        "spawn_item": "shiv", 
        "message": "Du schleifst das Metall und wickelst den Draht als Griff darum. Fertig ist das Messer."
    }
]