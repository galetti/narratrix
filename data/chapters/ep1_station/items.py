# data/chapters/ep1_station/items.py
from engine.constants import *

ITEMS = {
    # --- SCENERY ---
    "terminal": {
        "id": "terminal", "name": "Haupt-Terminal", "aliases": ["computer", "screen", "mainframe"], 
        "location": "hub", "type": TYPE_SURFACE, "movable": False, 
        "desc": "Zeigt hunderte Fehlermeldungen. Tippe 'hack' für eine Prognose."
    },
    "replicator": {
        "id": "replicator", "name": "Nahrungs-Replikator", "aliases": ["automat", "spender", "replikator"], 
        "location": "cantina", "type": TYPE_SURFACE, "movable": False, "state": STATE_BROKEN,
        "desc": "Er scheint nur noch heißes Wasser zu produzieren."
    },
    "core": {
        "id": "core", "name": "Reaktorkern", "aliases": ["kern", "reaktor"], 
        "location": "reactor", "state": STATE_BROKEN, "type": TYPE_SCENERY, "movable": False, 
        "desc": "Er steht kurz vor der Schmelze.", "temp": 800
    },
    "vent": {
        "id": "vent", "name": "Druckventil", "aliases": ["ventil", "rohr"], 
        "location": "maintenance", "state": STATE_NORMAL, "type": TYPE_SCENERY, "movable": False, 
        "desc": "Es zischt leise.", "temp": 70
    },
    "chair": {
        "id": "chair", "name": "Kommandosessel", "location": "bridge", "type": TYPE_SURFACE, "movable": False, "desc": "Blutspuren an der Lehne."
    },
    "med_cabinet": {
        "id": "med_cabinet", "name": "Medizin-Schrank", "aliases": ["schrank"], "location": "medbay", "type": TYPE_CONTAINER, "movable": False, "is_open": True, "desc": "Geplündert."
    },

    # --- ITEMS (Lokale Gegenstände) ---
    "stim_powder": {
        "id": "stim_powder", "name": "Stim-Pulver", "aliases": ["pulver", "kaffee", "koffein"], 
        "location": "terminal", "type": TYPE_ITEM, "movable": True, "matter": MATTER_SOLID, 
        "desc": "Militärisches Aufputschmittel. Trocken."
    },
    "mug": {
        "id": "mug", "name": "Isolier-Becher", "aliases": ["becher", "tasse"], 
        "location": "replicator", "type": TYPE_CONTAINER, 
        "movable": True, "matter": MATTER_SOLID, "is_open": True, 
        "desc": "Ein leerer Becher."
    },
    "hot_water": {
        "id": "hot_water", "name": "Heißes Wasser", "aliases": ["wasser"], 
        "location": "replicator", "type": TYPE_ITEM, "movable": True, "matter": MATTER_LIQUID, "temp": 95,
        "desc": "Kochend."
    },
    "stim_caf": {
        "id": "stim_caf", "name": "Stim-Caf", "aliases": ["kaffee", "getränk"], 
        "location": LOC_VOID, "type": TYPE_ITEM, "movable": True, "matter": MATTER_LIQUID, "temp": 90,
        "desc": "Starkes Zeug."
    },
    "coolant_canister": {
        "id": "coolant_canister", "name": "Kühlmittel-Kanister", "aliases": ["kanister", "kühlmittel"], 
        "location": "maintenance", 
        "type": TYPE_ITEM, "movable": True, "matter": MATTER_SOLID,
        "desc": "Schwer und kalt. Aber er hat ein Leck."
    },
    "sealed_coolant": {
        "id": "sealed_coolant", "name": "Versiegelter Kanister", "aliases": ["kanister", "kühlmittel"], 
        "location": LOC_VOID, 
        "type": TYPE_ITEM, "movable": True, "matter": MATTER_SOLID,
        "desc": "Dicht versiegelt und einsatzbereit."
    },
    "patch_kit": {
        "id": "patch_kit", "name": "Reparatur-Kit", "aliases": ["tape", "kit", "werkzeug"], 
        "location": "bridge", "type": TYPE_ITEM, "movable": True, "matter": MATTER_SOLID, 
        "desc": "Universelles Dichtmittel."
    },
    "med_gel": {
        "id": "med_gel", "name": "Bio-Gel", "aliases": ["gel", "medizin"], "location": "med_cabinet", "type": TYPE_ITEM, "movable": True, "matter": MATTER_LIQUID, "desc": "Regenerativ."
    },
    "bandage": {
        "id": "bandage", "name": "Verband", "aliases": ["mull"], "location": "med_cabinet", "type": TYPE_ITEM, "movable": True, "matter": MATTER_SOLID, "desc": "Steril."
    },
    "medikit": {
        "id": "medikit", "name": "Notfall-Verband", "aliases": ["medikit", "verband"], "location": LOC_VOID, "type": TYPE_ITEM, "movable": True, "matter": MATTER_SOLID, "desc": "Einsatzbereit."
    },
    "access_chip": {
        "id": "access_chip", "name": "Root-Chip", "aliases": ["chip", "karte"], "location": LOC_VOID, "type": TYPE_ITEM, "movable": True, "matter": MATTER_SOLID, "desc": "Level 5 Zugang."
    }
}

COMBINATIONS = [
    {
        "items": ["mug", "hot_water"], 
        "result": "hot_water", "consume": [], 
        "message": "Du füllst das heiße Wasser in den Becher."
    },
    {
        "items": ["stim_powder", "hot_water"], 
        "result": "stim_caf", "consume": ["stim_powder", "hot_water"], 
        "message": "Das Pulver löst sich zischend im Wasser auf. Es wird zu Stim-Caf."
    },
    {
        "items": ["coolant_canister", "patch_kit"], 
        "result": "sealed_coolant", "consume": ["coolant_canister"], 
        "message": "Du klebst das Leck mit dem Dichtmittel zu. Es scheint zu halten."
    },
    {
        "items": ["med_gel", "bandage"],
        "result": "medikit", "consume": ["med_gel", "bandage"],
        "message": "Du präparierst einen sterilen Verband mit dem Gel."
    }
]
