# narratrix_engine/data/chapters/ep1_arrival/items.py
from engine.constants import *

if 'TYPE_FIXTURE' not in globals(): TYPE_FIXTURE = "fixture"

ITEMS = {
    # --- TOOLS ---
    "tool_wrench": {
        ATTR_ID: "tool_wrench",
        ATTR_NAME: "Rohrzange",
        ATTR_DESC: "Ein schweres Werkzeug aus Karbonstahl. Lag bei Dr. Sato.",
        "location": "room_inner_corridor_north",
        "type": TYPE_ITEM,
        "is_tool": True,
        "damage": 5,
        ATTR_WEIGHT: 1.5
    },
    
    # --- REWARDS ---
    "item_keycard_quarters": {
        ATTR_ID: "keycard_quarters",
        ATTR_NAME: "Quartierschlüssel",
        ATTR_DESC: "Eine ID-Karte für dein Zimmer.",
        "location": LOC_VOID, # Gibt Sato später
        "type": TYPE_ITEM,
        ATTR_WEIGHT: 0.1
    },
    "tool_omni": {
        ATTR_ID: "tool_omni",
        ATTR_NAME: "Omni-Tool v1",
        ATTR_DESC: "Das Standard-Werkzeug für alles. Hat einen Scanner und Interface-Port.",
        "location": LOC_VOID,
        "type": TYPE_ITEM,
        "is_tool": True,
        ATTR_WEIGHT: 0.5
    },

    # --- ENVIRONMENT ---
    "ladder": {
        ATTR_ID: "ladder",
        ATTR_NAME: "Wartungsleiter",
        ATTR_DESC: "Eine ölige Leiter, die in den Schacht führt.",
        "location": "room_outer_waste",
        "type": TYPE_FIXTURE,
        "climbable": True,
        "target_elevation": 2
    },
    "parents_photo": {
        ATTR_ID: "photo_parents",
        ATTR_NAME: "Foto der Eltern",
        ATTR_DESC: "Ein altes analoges Foto.",
        "location": LOC_INVENTORY, # Start Item
        "type": TYPE_ITEM,
        ATTR_WEIGHT: 0.0
    }
}

COMBINATIONS = [
    # Den Bot ausschalten
    {
        "verb": "use", # "Benutze Zange mit Rusty"
        "items": ["tool_wrench", "rusty"],
        "message": "Du rammst die Zange in den Not-Aus-Schalter. Funken sprühen.",
        "effect": [
            {"type": "trigger_event", "id": "rusty_shutdown"}
        ]
    },
    # Alternative: Schlagen
    {
        "verb": "break", # "Zerstöre Rusty mit Zange"
        "items": ["tool_wrench", "rusty"],
        "message": "Mit einem lauten Scheppern triffst du das Chassis.",
        "effect": [
            {"type": "trigger_event", "id": "rusty_shutdown"}
        ]
    }
]