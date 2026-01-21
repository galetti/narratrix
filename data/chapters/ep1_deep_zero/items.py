# narratrix_engine/data/chapters/ep1_deep_zero/items.py
from engine.constants import *

if 'TYPE_FIXTURE' not in globals(): TYPE_FIXTURE = "fixture"

ITEMS = {
    # --- QUARTIER ---
    "tablet": {
        ATTR_ID: "tablet",
        ATTR_NAME: "Tablet",
        ATTR_DESC: "Dein persönliches Datapad. Ein Riss zieht sich über das Display.",
        "location": "room_quarters_aris",
        "type": TYPE_ITEM,
        ATTR_WEIGHT: 0.5,
        "readable": True,
        "content": "NEWS: Erde feiert 10 Jahre Gravitations-Vertrag.\nMAIL VON SATO: 'Pokerabend fällt aus, muss Sensoren schrubben. Sorry!'"
    },
    "ventilation": {
        ATTR_ID: "ventilation",
        ATTR_NAME: "Lüftungsgitter",
        ATTR_DESC: "Ein Standard-Lüftungsgitter. Es klappert nervtötend.",
        "location": "room_quarters_aris",
        "type": TYPE_FIXTURE,
        "state": "rattling"
    },
    "tool_scanner": {
        ATTR_ID: "tool_scanner",
        ATTR_NAME: "Handscanner",
        ATTR_DESC: "Ein Diagnose-Gerät für technische Defekte.",
        "location": "room_quarters_aris", # Im Schrank (vereinfacht: im Raum)
        "type": TYPE_ITEM,
        "is_tool": True,
        ATTR_WEIGHT: 1
    },
    "tool_screwdriver": {
        ATTR_ID: "tool_screwdriver",
        ATTR_NAME: "Schraubendreher",
        ATTR_DESC: "Ein einfacher Kreuzschlitz.",
        "location": "room_corridor_quarters", # Liegt im Flur rum
        "type": TYPE_ITEM,
        "is_tool": True,
        ATTR_WEIGHT: 0.2
    },

    # --- MESSE ---
    "coffee_machine": {
        ATTR_ID: "coffee_machine",
        ATTR_NAME: "Kaffeemaschine",
        ATTR_DESC: "Modell 'WakeUp 3000'. Die rote Wartungslampe leuchtet.",
        "location": "room_mess",
        "type": TYPE_FIXTURE,
        "state": "broken"
    },
    "junk_box": {
        ATTR_ID: "junk_box",
        ATTR_NAME: "Kramkiste",
        ATTR_DESC: "Eine Kiste mit Ersatzteilen.",
        "location": "room_mess",
        "type": TYPE_CONTAINER,
        "is_open": True
    },
    "spare_seal": {
        ATTR_ID: "spare_seal",
        ATTR_NAME: "Dichtungsring",
        ATTR_DESC: "Ein neuer Gummiring.",
        "location": "junk_box",
        "type": TYPE_ITEM,
        ATTR_WEIGHT: 0.1
    },
    "water_ration": {
        ATTR_ID: "water_ration",
        ATTR_NAME: "Wasser-Ration",
        ATTR_DESC: "Ein Beutel trinkbares Wasser.",
        "location": "room_mess",
        "type": TYPE_ITEM,
        "is_resource": True,
        "count": 5
    },
    "coffee_cup": {
        ATTR_ID: "coffee_cup",
        ATTR_NAME: "Tasse Kaffee",
        ATTR_DESC: "Dampfend heißer, schwarzer Kaffee.",
        "location": LOC_VOID,
        "type": TYPE_ITEM,
        ATTR_WEIGHT: 0.2
    },

    # --- WARTUNG ---
    "emitter_relay": {
        ATTR_ID: "emitter_relay",
        ATTR_NAME: "Emitter-Relais",
        ATTR_DESC: "Ein wichtiger Teil der Kommunikation. Es driftet ab.",
        "location": "room_corridor_main",
        "type": TYPE_FIXTURE,
        "level": 2, # Hoch oben!
        "state": "drift"
    },
    "ladder_mobile": {
        ATTR_ID: "ladder_mobile",
        ATTR_NAME: "Wartungsleiter",
        ATTR_DESC: "Eine fahrbare Leiter.",
        "location": "room_corridor_main",
        "type": TYPE_FIXTURE,
        "climbable": True,
        "target_elevation": 2,
        # Wenn man sie zum Relais schiebt (vereinfacht: sie steht schon da)
    }
}

COMBINATIONS = [
    # Task 1: Lüftung reparieren
    {
        "verb": "use",
        "items": ["tool_screwdriver", "ventilation"],
        "effect": [
            {"type": "update_object", "target": "ventilation", "updates": {"state": "silent", "desc": "Das Gitter sitzt fest. Endlich Ruhe."}},
            {"type": "trigger_event", "id": "task_vent_done"}
        ],
        "message": "Du ziehst die Schrauben fest. Das Klappern hört auf."
    },
    # Task 2: Kaffeemaschine reparieren
    {
        "verb": "fix",
        "items": ["coffee_machine"], # Benötigt Werkzeug im Inv? Logik im Handler.
        # Hier nutzen wir 'use' seal with machine
    },
    {
        "verb": "use",
        "items": ["spare_seal", "coffee_machine"],
        "ingredients": {"spare_seal": 1},
        "message": "Du tauscht die Dichtung aus. Die Wartungslampe wird grün.",
        "effect": {"type": "update_object", "target": "coffee_machine", "updates": {"state": "fixed"}}
    },
    {
        "verb": "use",
        "items": ["water_ration", "coffee_machine"],
        "ingredients": {"water_ration": 1},
        "station": "coffee_machine",
        "spawn_item": "coffee_cup",
        "message": "Die Maschine gurgelt und produziert frischen Kaffee.",
        "effect": {"type": "trigger_event", "id": "task_coffee_done"}
    },
    # Task 3: Relais kalibrieren
    {
        "verb": "use",
        "items": ["tool_scanner", "emitter_relay"],
        "message": "Du scannst das Relais und gleichst die Frequenzen ab. Drift korrigiert.",
        "effect": [
            {"type": "update_object", "target": "emitter_relay", "updates": {"state": "calibrated", "desc": "Das Relais arbeitet im grünen Bereich."}},
            {"type": "trigger_event", "id": "task_relay_done"}
        ]
    }
]