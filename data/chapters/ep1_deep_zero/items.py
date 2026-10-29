# narratrix_engine/data/chapters/ep1_arrival/items.py
from __future__ import annotations

from engine.constants import (
    ATTR_ALIASES,
    ATTR_DESC,
    ATTR_ID,
    ATTR_NAME,
    ATTR_WEIGHT,
    LOC_INVENTORY,
    LOC_VOID,
    TYPE_FIXTURE,
    TYPE_ITEM,
)
from engine.schema import ObjectData, RecipeData

ITEMS: dict[str, ObjectData] = {
    # --- TOOLS ---
    "tool_wrench": {
        ATTR_ID: "tool_wrench",
        ATTR_NAME: "Rohrzange",
        ATTR_DESC: "Ein schweres Werkzeug aus Karbonstahl. Lag bei Dr. Sato.",
        ATTR_ALIASES: ["zange", "rohrzange", "werkzeug", "wrench"],
        "location": "room_inner_corridor_north",
        "type": TYPE_ITEM,
        "is_tool": True,
        "damage": 5,
        ATTR_WEIGHT: 1.5,
    },

    # --- REWARDS ---
    "keycard_quarters": {
        ATTR_ID: "keycard_quarters",
        ATTR_NAME: "Quartierschlüssel",
        ATTR_DESC: "Eine ID-Karte für dein Zimmer.",
        ATTR_ALIASES: ["karte", "keycard", "schlüssel", "quartierschlüssel"],
        "location": LOC_VOID,  # Gibt Sato später
        "type": TYPE_ITEM,
        ATTR_WEIGHT: 0.1,
    },
    "tool_omni": {
        ATTR_ID: "tool_omni",
        ATTR_NAME: "Omni-Tool v1",
        ATTR_DESC: "Das Standard-Werkzeug für alles. Hat einen Scanner und Interface-Port.",
        ATTR_ALIASES: ["omni", "omnitool", "omni-tool", "scanner"],
        "location": LOC_VOID,
        "type": TYPE_ITEM,
        "is_tool": True,
        ATTR_WEIGHT: 0.5,
    },

    # --- ENVIRONMENT ---
    "ladder": {
        ATTR_ID: "ladder",
        ATTR_NAME: "Wartungsleiter",
        ATTR_DESC: "Eine ölige Leiter an der Wand, die hinauf zum offenen Wartungsschacht (Ebene 2) führt.",
        ATTR_ALIASES: ["leiter", "wartungsleiter", "sprossen"],
        "location": "room_outer_waste",
        "type": TYPE_FIXTURE,
        "climbable": True,
        "target_elevation": 2,
    },
    "maintenance_shaft": {
        ATTR_ID: "maintenance_shaft",
        ATTR_NAME: "Wartungsschacht",
        ATTR_DESC: (
            "Ein enger Wartungsschacht auf Ebene 2. Direkt im Einstieg steckt der defekte "
            "Wartungsbot 'Rusty' fest, schlägt gegen das Schottblech und blockiert den weiteren Durchgang."
        ),
        ATTR_ALIASES: ["schacht", "wartungsschacht", "öffnung", "wartungsschächten", "lüftungsschacht"],
        "location": "room_outer_waste",
        "type": TYPE_FIXTURE,
        "level": 2,
        "climbable": True,
        "target_elevation": 2,
    },
    "trash_compactor": {
        ATTR_ID: "trash_compactor",
        ATTR_NAME: "Schrottpresse",
        ATTR_DESC: "Eine massive hydraulische Presse für Stationsabfälle. Sie ist momentan im Standby.",
        ATTR_ALIASES: ["presse", "schrottpresse", "müllpresse"],
        "location": "room_outer_waste",
        "type": TYPE_FIXTURE,
        "level": 0,
    },
    "parents_photo": {
        ATTR_ID: "parents_photo",
        ATTR_NAME: "Foto der Eltern",
        ATTR_DESC: "Ein altes analoges Foto.",
        ATTR_ALIASES: ["foto", "bild", "eltern"],
        "location": LOC_INVENTORY,  # Start Item
        "type": TYPE_ITEM,
        ATTR_WEIGHT: 0.0,
    },
}

COMBINATIONS: list[RecipeData] = [
    # Den Bot ausschalten
    {
        "verb": "use",  # "Benutze Zange mit Rusty"
        "items": ["tool_wrench", "rusty"],
        "condition": {"type": "knowledge", "value": "rusty_dead", "not": True},
        "message": "Du rammst die Zange in den Not-Aus-Schalter. Funken sprühen.",
        "effects": [
            {"type": "trigger_event", "id": "rusty_shutdown"},
        ],
    },
    # Alternative: Schlagen
    {
        "verb": "break",  # "Zerstöre Rusty mit Zange"
        "items": ["tool_wrench", "rusty"],
        "condition": {"type": "knowledge", "value": "rusty_dead", "not": True},
        "message": "Mit einem lauten Scheppern triffst du das Chassis.",
        "effects": [
            {"type": "trigger_event", "id": "rusty_shutdown"},
        ],
    },
]
