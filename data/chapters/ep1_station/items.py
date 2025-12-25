# data/chapters/ep1_station/items.py
from engine.constants import *

ITEMS = {
    # --- SCENERY (Unbeweglich = Unendlich schwer) ---
    "terminal": {
        "id": "terminal", "name": "Haupt-Terminal", "aliases": ["computer", "screen", "mainframe"], 
        "location": "hub", "type": TYPE_SURFACE, 
        "weight": float('inf'), 
        "desc": "Zeigt hunderte Fehlermeldungen. Tippe 'hack' für eine Prognose."
    },
    "replicator": {
        "id": "replicator", "name": "Nahrungs-Replikator", "aliases": ["automat", "spender", "replikator"], 
        "location": "cantina", "type": TYPE_SURFACE, "state": STATE_BROKEN,
        "weight": float('inf'),
        "desc": "Er scheint nur noch heißes Wasser zu produzieren."
    },
    "core": {
        "id": "core", "name": "Reaktorkern", "aliases": ["kern", "reaktor"], 
        "location": "reactor", "state": STATE_BROKEN, "type": TYPE_SCENERY, 
        "weight": float('inf'),
        "desc": "Er steht kurz vor der Schmelze.", "temp": 800
    },
    "vent": {
        "id": "vent", "name": "Druckventil", "aliases": ["ventil", "rohr"], 
        "location": "maintenance", "state": STATE_NORMAL, "type": TYPE_SCENERY, 
        "weight": float('inf'),
        "desc": "Es zischt leise.", "temp": 70
    },
    "chair": {
        "id": "chair", "name": "Kommandosessel", "location": "bridge", "type": TYPE_SURFACE, 
        "weight": 45.0, 
        "desc": "Blutspuren an der Lehne."
    },
    "med_cabinet": {
        "id": "med_cabinet", "name": "Medizin-Schrank", "aliases": ["schrank"], "location": "medbay", "type": TYPE_CONTAINER, 
        "weight": float('inf'), 
        "is_open": True, "desc": "Geplündert."
    },
    "airlock_control": {
        "id": "airlock_control", "name": "Luftschleusen-Steuerung", "aliases": ["steuerung", "panel"],
        "location": "maintenance", "type": TYPE_SURFACE, 
        "weight": float('inf'),
        "desc": "Kontrolliert den Zugang zum Dock."
    },
    "scale": {
        "id": "scale", "name": "Präzisionswaage", "aliases": ["waage"], 
        "location": "medbay", "type": TYPE_SURFACE, 
        "weight": 2.0, 
        "desc": "Eine digitale Waage. Du kannst Dinge darauf legen."
    },

    # --- ITEMS (Beweglich) ---
    "stim_powder": {
        "id": "stim_powder", "name": "Stim-Pulver", "aliases": ["pulver", "kaffee", "koffein"], 
        "location": "terminal", "type": TYPE_ITEM, "matter": MATTER_SOLID, 
        "weight": 0.1, 
        "desc": "Militärisches Aufputschmittel. Trocken."
    },
    "mug": {
        "id": "mug", "name": "Isolier-Becher", "aliases": ["becher", "tasse"], 
        "location": "replicator", "type": TYPE_CONTAINER, "matter": MATTER_SOLID, "is_open": True, 
        "weight": 0.3, 
        "desc": "Ein leerer Becher."
    },
    "hot_water": {
        "id": "hot_water", "name": "Heißes Wasser", "aliases": ["wasser"], 
        "location": "replicator", "type": TYPE_ITEM, "matter": MATTER_LIQUID, "temp": 95,
        "weight": 0.2,
        "desc": "Kochend."
    },
    "stim_caf": {
        "id": "stim_caf", "name": "Stim-Caf", "aliases": ["kaffee", "getränk"], 
        "location": LOC_VOID, "type": TYPE_ITEM, "matter": MATTER_LIQUID, "temp": 90,
        "weight": 0.2,
        "desc": "Starkes Zeug."
    },
    "coolant_canister": {
        "id": "coolant_canister", "name": "Kühlmittel-Kanister", "aliases": ["kanister", "kühlmittel"], 
        "location": "maintenance", "type": TYPE_ITEM, "matter": MATTER_SOLID,
        "weight": 15.0, 
        "desc": "Schwer und kalt. Aber er hat ein Leck."
    },
    "sealed_coolant": {
        "id": "sealed_coolant", "name": "Versiegelter Kanister", "aliases": ["kanister", "kühlmittel"], 
        "location": LOC_VOID, "type": TYPE_ITEM, "matter": MATTER_SOLID,
        "weight": 15.1,
        "desc": "Dicht versiegelt und einsatzbereit."
    },
    "patch_kit": {
        "id": "patch_kit", "name": "Reparatur-Kit", "aliases": ["tape", "kit", "werkzeug"], 
        "location": "bridge", "type": TYPE_ITEM, "matter": MATTER_SOLID, 
        "weight": 0.5,
        "desc": "Universelles Dichtmittel."
    },
    "med_gel": {
        "id": "med_gel", "name": "Bio-Gel", "aliases": ["gel", "medizin"], "location": "med_cabinet", "type": TYPE_ITEM, "matter": MATTER_LIQUID, 
        "weight": 0.1,
        "desc": "Regenerativ."
    },
    "bandage": {
        "id": "bandage", "name": "Verband", "aliases": ["mull"], "location": "med_cabinet", "type": TYPE_ITEM, "matter": MATTER_SOLID, 
        "weight": 0.05,
        "desc": "Steril."
    },
    "medikit": {
        "id": "medikit", "name": "Notfall-Verband", "aliases": ["medikit", "verband"], "location": LOC_VOID, "type": TYPE_ITEM, "matter": MATTER_SOLID, 
        "weight": 0.15,
        "desc": "Einsatzbereit."
    },
    "access_chip": {
        "id": "access_chip", "name": "Root-Chip", "aliases": ["chip", "karte"], "location": LOC_VOID, "type": TYPE_ITEM, "matter": MATTER_SOLID, 
        "weight": 0.01,
        "desc": "Level 5 Zugang."
    },
    "scrap_metal": {
        "id": "scrap_metal", "name": "Metallschrott", "aliases": ["schrott", "metall"], "location": "maintenance", "type": TYPE_ITEM, "matter": MATTER_SOLID, 
        "weight": 2.5,
        "desc": "Ein Stück verbogenes Metall."
    },
    "crowbar": {
        "id": "crowbar", "name": "Brecheisen", "aliases": ["eisen", "hebel"], "location": LOC_VOID, "type": TYPE_ITEM, "matter": MATTER_SOLID, 
        "weight": 2.4,
        "desc": "Ein improvisiertes Brecheisen."
    },
    "strange_rock": {
        "id": "strange_rock", "name": "Dichter Stein", "aliases": ["stein", "brocken"], 
        "location": "medbay", "type": TYPE_ITEM, "matter": MATTER_SOLID,
        "weight": 100.0, 
        "desc": "Ein faustgroßer Stein, der aber unmöglich schwer ist."
    }
}

COMBINATIONS = [
    {
        "items": ["mug", "hot_water"], 
        "result": "hot_water", 
        # Hier nehmen wir an, dass der Replikator unendlich Wasser gibt, daher verbrauchen wir die Quelle NICHT.
        # Das Resultat (neues Wasser) landet im Becher.
        "consume": [], 
        "message": "Du füllst das heiße Wasser in den Becher."
    },
    {
        "items": ["stim_powder", "hot_water"], 
        "result": "stim_caf", 
        # Beide werden verbraucht, um den Kaffee zu erzeugen
        "consume": ["stim_powder", "hot_water"], 
        "message": "Das Pulver löst sich zischend im Wasser auf. Es wird zu Stim-Caf."
    },
    {
        "items": ["coolant_canister", "patch_kit"], 
        "tools": ["multitool"],
        "result": "sealed_coolant", 
        # FIX: Der kaputte Kanister MUSS verbraucht werden, da er durch den ganzen ersetzt wird!
        "consume": ["coolant_canister", "patch_kit"], 
        "message": "Mit Hilfe des Multitools klebst du das Leck mit dem Dichtmittel zu. Es scheint zu halten."
    },
    {
        "items": ["med_gel", "bandage"],
        "result": "medikit", 
        "consume": ["med_gel", "bandage"],
        "message": "Du präparierst einen sterilen Verband mit dem Gel."
    },
    {
        "items": ["scrap_metal"],
        "tools": ["multitool"],
        "result": "crowbar",
        "consume": ["scrap_metal"],
        "message": "Du biegst das Metall mit dem Multitool zurecht und fertigst ein grobes Brecheisen an."
    }
]
