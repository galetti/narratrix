from engine.constants import (
    TYPE_ITEM, TYPE_CONTAINER, TYPE_SURFACE, TYPE_SCENERY,
    STATE_NORMAL, STATE_BROKEN, STATE_SABOTAGED,
    MATTER_SOLID, MATTER_LIQUID,
    ATTR_MOVABLE, LOC_VOID
)

ITEMS = {
    # --- SCENERY (Möbel & Feste Objekte) ---
    "terminal": {
        "id": "terminal", "name": "Haupt-Terminal", "aliases": ["computer", "screen", "mainframe"], 
        "location": "hub", "type": TYPE_SURFACE, "movable": False, 
        "desc": "Zeigt hunderte Fehlermeldungen. Tippe 'hack' für eine Prognose.",
        "weight": 100.0
    },
    "replicator": {
        "id": "replicator", "name": "Nahrungs-Replikator", "aliases": ["automat", "spender", "replikator"], 
        "location": "cantina", "type": TYPE_SURFACE, "movable": False, "state": STATE_BROKEN,
        "desc": "Er scheint nur noch heißes Wasser zu produzieren.",
        "weight": 50.0
    },
    "core": {
        "id": "core", "name": "Reaktorkern", "aliases": ["kern", "reaktor"], 
        "location": "reactor", "state": STATE_BROKEN, "type": TYPE_SCENERY, "movable": False, 
        "desc": "Er steht kurz vor der Schmelze.", "temp": 800,
        "weight": 1000.0
    },
    "vent": {
        "id": "vent", "name": "Druckventil", "aliases": ["ventil", "rohr"], 
        "location": "maintenance", "state": STATE_NORMAL, "type": TYPE_SCENERY, "movable": False, 
        "desc": "Es zischt leise.", "temp": 70,
        "weight": 10.0
    },
    "chair": {
        "id": "chair", "name": "Kommandosessel", "location": "bridge", "type": TYPE_SCENERY, "movable": False, 
        "desc": "Blutspuren an der Lehne.",
        "weight": 15.0
    },
    "med_cabinet": {
        "id": "med_cabinet", "name": "Medizin-Schrank", "aliases": ["schrank"], 
        "location": "medbay", "type": TYPE_CONTAINER, "movable": False, "is_open": True, 
        "desc": "Geplündert.",
        "weight": 50.0, "capacity": 20.0
    },

    # --- ITEMS (Beweglich) ---
    "player_pda": { # War im Original evtl. nicht drin, aber für Logik wichtig
        "id": "player_pda", "name": "Datapad", "aliases": ["pda", "tablet"],
        "location": "inventory", "type": TYPE_ITEM, "movable": True,
        "desc": "Dein persönliches Terminal.",
        "weight": 0.5
    },
    "stim_powder": {
        "id": "stim_powder", "name": "Stim-Pulver", "aliases": ["pulver", "kaffee", "koffein"], 
        "location": "terminal", "type": TYPE_ITEM, "movable": True, "matter": MATTER_SOLID, 
        "desc": "Militärisches Aufputschmittel. Trocken.",
        "weight": 0.1
    },
    "mug": {
        "id": "mug", "name": "Isolier-Becher", "aliases": ["becher", "tasse"], 
        "location": "replicator", "type": TYPE_CONTAINER, 
        "movable": True, "matter": MATTER_SOLID, "is_open": True, 
        "desc": "Ein leerer Becher.",
        "weight": 0.2, "capacity": 0.5
    },
    "hot_water": {
        "id": "hot_water", "name": "Heißes Wasser", "aliases": ["wasser"], 
        "location": "replicator", "type": TYPE_ITEM, "movable": True, "matter": MATTER_LIQUID, "temp": 95,
        "desc": "Kochend.",
        "weight": 0.3
    },
    "stim_caf": {
        "id": "stim_caf", "name": "Stim-Caf", "aliases": ["kaffee", "getränk"], 
        "location": LOC_VOID, "type": TYPE_ITEM, "movable": True, "matter": MATTER_LIQUID, "temp": 90,
        "desc": "Starkes Zeug.",
        "weight": 0.3
    },
    "coolant_canister": {
        "id": "coolant_canister", "name": "Kühlmittel-Kanister", "aliases": ["kanister", "kühlmittel"], 
        "location": "maintenance", 
        "type": TYPE_ITEM, "movable": True, "matter": MATTER_SOLID,
        "desc": "Schwer und kalt. Aber er hat ein Leck.",
        "weight": 5.0
    },
    "sealed_coolant": {
        "id": "sealed_coolant", "name": "Versiegelter Kanister", "aliases": ["kanister", "kühlmittel"], 
        "location": LOC_VOID, 
        "type": TYPE_ITEM, "movable": True, "matter": MATTER_SOLID,
        "desc": "Dicht versiegelt und einsatzbereit.",
        "weight": 5.1
    },
    "patch_kit": {
        "id": "patch_kit", "name": "Reparatur-Kit", "aliases": ["tape", "kit", "werkzeug"], 
        "location": "bridge", "type": TYPE_ITEM, "movable": True, "matter": MATTER_SOLID, 
        "desc": "Universelles Dichtmittel.",
        "weight": 1.0,
        "tool_type": "repair" # Wichtig für fix() Logik
    },
    "crowbar": { # Hinzugefügt für break() Logik, falls im Original nicht vorhanden
        "id": "crowbar", "name": "Brecheisen", "aliases": ["eisen"],
        "location": "maintenance", "type": TYPE_ITEM, "movable": True,
        "desc": "Solider Stahl.", "weight": 2.5, "tool_type": "force"
    },
    "med_gel": {
        "id": "med_gel", "name": "Bio-Gel", "aliases": ["gel", "medizin"], "location": "med_cabinet", "type": TYPE_ITEM, "movable": True, "matter": MATTER_LIQUID, "desc": "Regenerativ.",
        "weight": 0.5
    },
    "bandage": {
        "id": "bandage", "name": "Verband", "aliases": ["mull"], "location": "med_cabinet", "type": TYPE_ITEM, "movable": True, "matter": MATTER_SOLID, "desc": "Steril.",
        "weight": 0.1
    },
    "medikit": {
        "id": "medikit", "name": "Notfall-Verband", "aliases": ["medikit", "verband"], "location": LOC_VOID, "type": TYPE_ITEM, "movable": True, "matter": MATTER_SOLID, "desc": "Einsatzbereit.",
        "weight": 0.6
    },
    "access_chip": {
        "id": "access_chip", "name": "Root-Chip", "aliases": ["chip", "karte"], "location": LOC_VOID, "type": TYPE_ITEM, "movable": True, "matter": MATTER_SOLID, "desc": "Level 5 Zugang.",
        "weight": 0.05
    }
}

COMBINATIONS = [
    # 1. Wasser in Becher füllen
    {
        "items": ["mug", "hot_water"], 
        "result": "hot_water", # Trick: Wasser landet im Becher durch Logik, oder wir erzeugen vollen Becher
        # Da perform_combine() Logik Result erzeugt: Wir müssten eigentlich ein Item "mug_full" haben.
        # Vereinfachung: Wir nutzen das existierende System.
        # Da hot_water LIQUID ist und mug CONTAINER, sollte 'put' genutzt werden.
        # Aber für Crafting Logik:
        "message": "Du füllst das heiße Wasser in den Becher.",
        "keep_items": True 
    },
    # 2. Pulver in das Wasser (im Becher?)
    # Wir brauchen eine ID für "Wasser im Becher". Das ist komplex.
    # Einfacher: Pulver + Heißes Wasser -> Stim Caf
    {
        "items": ["stim_powder", "hot_water"], 
        "result": "stim_caf", 
        "message": "Das Pulver löst sich zischend im Wasser auf. Es wird zu Stim-Caf."
    },
    # 3. Kanister flicken
    {
        "items": ["coolant_canister", "patch_kit"], 
        "result": "sealed_coolant", 
        "message": "Du klebst das Leck mit dem Dichtmittel zu. Es scheint zu halten."
    },
    # 4. Medikit basteln
    {
        "items": ["med_gel", "bandage"],
        "result": "medikit", 
        "message": "Du präparierst einen sterilen Verband mit dem Gel."
    }
]
