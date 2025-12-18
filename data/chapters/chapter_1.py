# data/chapters/chapter_1.py
# Enthält ALLE Daten für Kapitel 1 (Räume, Items, NPCs, Events)
# Keine externen Importe aus data/rooms.py etc. mehr!

from engine.constants import (
    TYPE_ITEM, TYPE_CONTAINER, TYPE_SURFACE, TYPE_SCENERY,
    STATE_NORMAL, STATE_BROKEN, STATE_SABOTAGED,
    MATTER_SOLID, MATTER_LIQUID,
    ATTR_MOVABLE, LOC_VOID
)

CHAPTER_META = {
    "chapter_title": "Kapitel 1: Das Erwachen",
    "chapter_id": 1,
    "start_room": "hub"
}

# --- RÄUME ---
ROOMS = {
    "hub": {
        "name": "Zentraler Hub",
        "desc": "Das Herz der Station. Ein großes Haupt-Terminal dominiert die Mitte. K.A.R.L.s Hologramm flackert.",
        "exits": {"north": "bridge", "east": "reactor", "south": "cantina", "west": "medbay"},
        "img": "scifi_hub"
    },
    "cantina": {
        "name": "Kantine",
        "desc": "Umgestürzte Tische und der Geruch von verbranntem Synthetik-Fleisch.",
        "exits": {"north": "hub", "down": "maintenance"},
        "img": "scifi_cantina"
    },
    "bridge": {
        "name": "Kommandobrücke",
        "desc": "Funken sprühen aus den Konsolen. Der Kommandosessel des Commanders ist umgestürzt.",
        "exits": {"south": "hub"},
        "img": "scifi_bridge"
    },
    "reactor": {
        "name": "Reaktorraum",
        "desc": "Ein unheimliches blaues Glühen erfüllt den Raum. Das Summen ist ohrenbetäubend.",
        "exits": {"west": "hub"},
        "img": "scifi_reactor"
    },
    "medbay": {
        "name": "Krankenstation",
        "desc": "Verwüstet. Ein leerer Medizin-Schrank steht offen.",
        "exits": {"east": "hub"},
        "img": "scifi_medbay"
    },
    "maintenance": {
        "name": "Wartungsschacht",
        "desc": "Eng, dunkel und dampfig. Rohre verlaufen überall.",
        "exits": {"up": "cantina"},
        "img": "scifi_maintenance"
    }
}

# --- ITEMS ---
ITEMS = {
    # SCENERY
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
        "id": "chair", "name": "Kommandosessel", "aliases": ["sessel", "stuhl"],
        "location": "bridge", "type": TYPE_SCENERY, "movable": False, 
        "desc": "Blutspuren an der Lehne.",
        "weight": 15.0
    },
    "med_cabinet": {
        "id": "med_cabinet", "name": "Medizin-Schrank", "aliases": ["schrank"], 
        "location": "medbay", "type": TYPE_CONTAINER, "movable": False, "is_open": True, 
        "desc": "Geplündert.",
        "weight": 50.0, "capacity": 20.0
    },
    "scale": {
        "id": "scale", "name": "Präzisionswaage", "aliases": ["waage"],
        "location": "medbay", "type": TYPE_SCENERY, "movable": False,
        "desc": "Eine digitale Waage für Medikamente. Benutze sie 'mit' einem Gegenstand.",
        "weight": 2.0
    },

    # MOVABLE ITEMS
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
        "tool_type": "repair"
    },
    "crowbar": {
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

# --- NPCS ---
NPCS = [
    {
        "id": "karl",
        "name": "K.A.R.L.",
        "aliases": ["karl", "ki", "hologramm"],
        "location": "hub",
        "img": "char_karl", # Platzhalter für Bild
        "desc": "Die Stations-KI. Sein Avatar flackert besorgniserregend.",
        "state": "default",
        "personality": "Logisch, Panisch",
        "dialogue": {
            "default": {
                "greeting": "Commander! Status kritisch. Reaktor bei 98%.",
                "reaktor": {"text": "Wir müssen ihn kühlen! Finden Sie Kühlmittel!", "effect": {"type": "learn", "fact": "mission_coolant"}},
                "status": "Lebenserhaltung ausgefallen. Schilde bei 0%.",
                "received_access_chip": { # Spezielle Reaktion auf Item
                    "text": "Danke! Ich starte den Reboot... Zugriff gewährt!",
                    "effect": {"type": "unlock_door", "value": "bridge_door"} # Beispiel Effekt
                }
            }
        }
    },
    {
        "id": "val",
        "name": "Val",
        "aliases": ["val", "offizier"],
        "location": "bridge",
        "img": "char_val",
        "desc": "Deine erste Offizierin. Sie hält sich die Seite.",
        "state": "injured",
        "dialogue": {
            "injured": {
                "greeting": "Hrrgh... Bericht...",
                "status": "Mir geht es gut... kümmern Sie sich um das Schiff.",
                "received_medikit": {
                    "text": "Ah... das ist besser. Danke, Commander.",
                    "effect": [
                        {"type": "set_state", "value": "healthy"},
                        {"type": "learn", "fact": "val_healed"}
                    ]
                }
            },
            "healthy": {
                "greeting": "Bereit zum Dienst, Commander.",
                "status": "Systeme fahren hoch."
            }
        }
    }
]

# --- EVENTS ---
NARRATIVE_MATRIX = [
    {
        "id": "event_intro",
        "trigger": {"type": "location", "value": "hub"},
        "action": {"type": "log", "value": "ALARM: REAKTOR-INSTABILITÄT DETEKTIERT."},
        "once": True
    },
    {
        "id": "event_meltdown_warning",
        "trigger": {"type": "time_ge", "value": 500}, # Ab Minute 500
        "action": {"type": "log", "value": "WARNUNG: Kernschmelze in T-minus 10 Minuten."},
        "once": True
    }
]

# --- REZEPTE ---
COMBINATIONS = [
    {
        "items": ["mug", "hot_water"], 
        "result": "hot_water", 
        "message": "Du füllst das heiße Wasser in den Becher.",
        "keep_items": True 
    },
    {
        "items": ["stim_powder", "hot_water"], 
        "result": "stim_caf", 
        "message": "Das Pulver löst sich zischend im Wasser auf. Es wird zu Stim-Caf."
    },
    {
        "items": ["coolant_canister", "patch_kit"], 
        "result": "sealed_coolant", 
        "message": "Du klebst das Leck mit dem Dichtmittel zu. Es scheint zu halten."
    },
    {
        "items": ["med_gel", "bandage"],
        "result": "medikit", 
        "message": "Du präparierst einen sterilen Verband mit dem Gel."
    }
]
