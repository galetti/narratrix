# narratrix_engine/data/chapters/ep2_habitat_sector/items.py
from __future__ import annotations

from engine.constants import (
    ATTR_ALIASES,
    ATTR_DESC,
    ATTR_ID,
    ATTR_NAME,
    ATTR_WEIGHT,
    LOC_INVENTORY,
    LOC_VOID,
    TYPE_CONTAINER,
    TYPE_FIXTURE,
    TYPE_ITEM,
    TYPE_SURFACE,
)
from engine.schema import ObjectData, RecipeData

ITEMS: dict[str, ObjectData] = {
    # --- STARTING INVENTORY (Übernommen aus Episode 1) ---
    "tool_omni": {
        ATTR_ID: "tool_omni",
        ATTR_NAME: "Omni-Tool v1",
        ATTR_DESC: "Das Standard-Werkzeug für Wartung und Systemkalibrierung. Dr. Sato hat es dir überlassen.",
        ATTR_ALIASES: ["omni", "omnitool", "omni-tool", "werkzeug"],
        "location": LOC_INVENTORY,
        "type": TYPE_ITEM,
        "is_tool": True,
        ATTR_WEIGHT: 0.5,
    },
    "keycard_quarters": {
        ATTR_ID: "keycard_quarters",
        ATTR_NAME: "Quartierschlüssel",
        ATTR_DESC: "Eine autorisierte ID-Karte für Quartier 4B im Habitat-Trakt.",
        ATTR_ALIASES: ["karte", "keycard", "schlüssel", "quartierschlüssel", "id-karte"],
        "location": LOC_INVENTORY,
        "type": TYPE_ITEM,
        ATTR_WEIGHT: 0.1,
    },
    "parents_photo": {
        ATTR_ID: "parents_photo",
        ATTR_NAME: "Foto der Eltern",
        ATTR_DESC: "Ein kleines, etwas abgegriffenes Foto aus alten Tagen auf der Erde.",
        ATTR_ALIASES: ["foto", "bild", "eltern"],
        "location": LOC_INVENTORY,
        "type": TYPE_ITEM,
        ATTR_WEIGHT: 0.0,
    },

    # --- HABITAT-SCHLEUSE ---
    "airlock_door": {
        ATTR_ID: "airlock_door",
        ATTR_NAME: "Schleusenschott",
        ATTR_DESC: "Ein schweres Überdruck-Schott mit Dichtlippen aus Silikon. Es steht offen.",
        ATTR_ALIASES: ["schott", "tür", "schleusentür", "schleusenschott"],
        "location": "quarters_airlock",
        "type": TYPE_FIXTURE,
        "linked_exit": "east",
        "is_open": True,
    },
    "disinfection_scanner": {
        ATTR_ID: "disinfection_scanner",
        ATTR_NAME: "Dekontaminations-Scanner",
        ATTR_DESC: "Ein Deckenbogen mit UV-Sensoren zur Neutralisierung organischer Sporen.",
        ATTR_ALIASES: ["scanner", "bogen", "uv-scanner", "dekontaminations-scanner"],
        "location": "quarters_airlock",
        "type": TYPE_FIXTURE,
    },

    # --- GEMEINSCHAFTSLOUNGE ---
    "dispenser": {
        ATTR_ID: "dispenser",
        ATTR_NAME: "Nährstoff-Spender",
        ATTR_DESC: "Ein Lebensmittel-Automat für synthetische Riegel und Elektrolytgetränke.",
        ATTR_ALIASES: ["spender", "automat", "nährstoff-spender", "essensautomat"],
        "location": "living_commons",
        "type": TYPE_CONTAINER,
        "is_open": True,
    },
    "ration_pack": {
        ATTR_ID: "ration_pack",
        ATTR_NAME: "Notration",
        ATTR_DESC: "Ein vakuumverpackter Proteinriegel mit Zitrusgeschmack.",
        ATTR_ALIASES: ["ration", "notration", "riegel", "proteinriegel", "essen"],
        "location": "dispenser",
        "type": TYPE_ITEM,
        ATTR_WEIGHT: 0.2,
    },
    "couch": {
        ATTR_ID: "couch",
        ATTR_NAME: "Sitzbank",
        ATTR_DESC: "Eine geschwungene modulare Polsterbank im 70er-Jahre-Retro-Design.",
        ATTR_ALIASES: ["bank", "sofa", "couch", "sitzbank", "polster"],
        "location": "living_commons",
        "type": TYPE_FIXTURE,
    },
    "information_screen": {
        ATTR_ID: "information_screen",
        ATTR_NAME: "Info-Bildschirm",
        ATTR_DESC: "Der Terminalbildschirm flackert rot: 'WARNUNG: Druckabfall in Biosphäre 2. Manuelle Inspektion erforderlich.'",
        ATTR_ALIASES: ["bildschirm", "monitor", "terminal", "info-bildschirm", "anzeige"],
        "location": "living_commons",
        "type": TYPE_FIXTURE,
    },

    # --- QUARTIER 4B (THORNE) ---
    "cabin_door": {
        ATTR_ID: "cabin_door",
        ATTR_NAME: "Quartiertür",
        ATTR_DESC: "Die Schiebetür zu Quartier 4B. Das Schloss leuchtet grün für Thorne.",
        ATTR_ALIASES: ["tür", "schiebetür", "quartiertür", "zimmertür"],
        "location": "crew_cabin_thorne",
        "type": TYPE_FIXTURE,
        "linked_exit": "north",
        "is_open": True,
    },
    "bunk_bed": {
        ATTR_ID: "bunk_bed",
        ATTR_NAME: "Schlafkoje",
        ATTR_DESC: "Eine eingebaute Koje mit straffer Decke und Magnetkissen.",
        ATTR_ALIASES: ["bett", "koje", "schlafkoje", "matratze"],
        "location": "crew_cabin_thorne",
        "type": TYPE_FIXTURE,
    },
    "terminal_desk": {
        ATTR_ID: "terminal_desk",
        ATTR_NAME: "Schreibtisch",
        ATTR_DESC: "Eine schmale Arbeitsplatte aus gebürstetem Leichtmetall.",
        ATTR_ALIASES: ["tisch", "schreibtisch", "arbeitsplatte"],
        "location": "crew_cabin_thorne",
        "type": TYPE_SURFACE,
        "is_open": True,
    },
    "audio_diary": {
        ATTR_ID: "audio_diary",
        ATTR_NAME: "Audio-Tagebuch",
        ATTR_DESC: "Ein handlicher Diktier-Chip. Die letzte Aufnahme stammt von deiner Vorgängerin Dr. Aris.",
        ATTR_ALIASES: ["tagebuch", "audiolog", "audio-tagebuch", "chip", "aufnahme"],
        "location": "terminal_desk",
        "type": TYPE_ITEM,
        ATTR_WEIGHT: 0.1,
    },
    "locker": {
        ATTR_ID: "locker",
        ATTR_NAME: "Wandspind",
        ATTR_DESC: "Ein magnetisch verriegelter Metallschrank für persönliche Ausrüstung.",
        ATTR_ALIASES: ["spind", "schrank", "wandspind", "locker"],
        "location": "crew_cabin_thorne",
        "type": TYPE_CONTAINER,
        "is_open": True,
    },
    "sealant_tape": {
        ATTR_ID: "sealant_tape",
        ATTR_NAME: "Dichtungsband",
        ATTR_DESC: "Hitzebeständiges Nanopolymer-Band für Druckleitungen und Notfallreparaturen.",
        ATTR_ALIASES: ["band", "dichtungsband", "tape", "reparaturband", "polymerband"],
        "location": "locker",
        "type": TYPE_ITEM,
        "is_tool": True,
        ATTR_WEIGHT: 0.3,
    },

    # --- BIOSPHÄRE & FILTERANLAGEN ---
    "hydroponic_tanks": {
        ATTR_ID: "hydroponic_tanks",
        ATTR_NAME: "Algentanks",
        ATTR_DESC: "Große Zylinder aus Acrylglas, in denen grün leuchtende Spirulina-Kulturen für Sauerstoff sorgen.",
        ATTR_ALIASES: ["tanks", "algentanks", "zylinder", "algen"],
        "location": "hydroponics_bay",
        "type": TYPE_FIXTURE,
        "level": 0,
    },
    "filtration_unit": {
        ATTR_ID: "filtration_unit",
        ATTR_NAME: "Filteranlage",
        ATTR_DESC: "Die zentrale Umwälzpumpe für den biologischen Wasserkreislauf der Station.",
        ATTR_ALIASES: ["filter", "filteranlage", "pumpe", "umwälzpumpe"],
        "location": "hydroponics_bay",
        "type": TYPE_FIXTURE,
        "level": 0,
    },
    "catwalk_ladder": {
        ATTR_ID: "catwalk_ladder",
        ATTR_NAME: "Service-Leiter",
        ATTR_DESC: "Eine feuerverzinkte Leiter, die hinauf zur Überdruckbühne auf Ebene 1 führt.",
        ATTR_ALIASES: ["leiter", "service-leiter", "trittstufen", "stufen"],
        "location": "hydroponics_bay",
        "type": TYPE_FIXTURE,
        "climbable": True,
        "target_elevation": 1,
    },
    "steam_pipe": {
        ATTR_ID: "steam_pipe",
        ATTR_NAME: "Dampfleitung",
        ATTR_DESC: "Eine isolierte Hochdruckleitung auf Ebene 1. An der Schweißnaht entweicht zischend heißer Dampf.",
        ATTR_ALIASES: ["leitung", "dampfleitung", "rohr", "dampfrohr", "überdruckleitung"],
        "location": "hydroponics_bay",
        "type": TYPE_FIXTURE,
        "level": 1,
    },
    "pressure_valve": {
        ATTR_ID: "pressure_valve",
        ATTR_NAME: "Überdruckventil",
        ATTR_DESC: "Ein massives rotes Bypass-Ventil auf Ebene 1. Der Stellmotor klemmt und benötigt eine Kalibrierung.",
        ATTR_ALIASES: ["ventil", "überdruckventil", "handrad", "bypass", "stellmotor"],
        "location": "hydroponics_bay",
        "type": TYPE_FIXTURE,
        "level": 1,
    },

    # --- BELOHNUNG & REZEPT-ERGEBNISSE ---
    "core_access_chip": {
        ATTR_ID: "core_access_chip",
        ATTR_NAME: "Reaktorkern-Zugangschip",
        ATTR_DESC: "Ein codierter Sicherheitschip mit Freigabe für den Reaktor- und Hauptantriebssektor.",
        ATTR_ALIASES: ["chip", "zugangschip", "reaktorchip", "freigabechip"],
        "location": LOC_VOID,  # Von Dr. Vance als Belohnung
        "type": TYPE_ITEM,
        ATTR_WEIGHT: 0.1,
    },
}

COMBINATIONS: list[RecipeData] = [
    # 1. Ventil mit Omni-Tool entlasten / kalibrieren
    {
        "verb": "use",
        "items": ["tool_omni", "pressure_valve"],
        "condition": {"type": "knowledge", "value": "valve_calibrated", "not": True},
        "message": (
            "Du setzt den Interface-Sensor des Omni-Tools an den Stellmotor des Ventils. "
            "Ein rhythmischer Impuls löst die mechanische Blockade. Das rote Handrad rotiert mit einem satten Klacken."
        ),
        "effects": [
            {"type": "trigger_event", "id": "event_valve_calibrated"},
        ],
    },

    # 2. Dampfleitung mit Dichtungsband abdichten
    {
        "verb": "use",
        "items": ["sealant_tape", "steam_pipe"],
        "condition": {"type": "knowledge", "value": "steam_fixed", "not": True},
        "message": (
            "Du wickelst mehrere Lagen des hitzebeständigen Nanopolymer-Bands fest um die Schweißnaht. "
            "Das Polymer verschmilzt unter der Hitze sofort zu einem gasdichten Schild. Das Zischen verstummt vollständig!"
        ),
        "effects": [
            {"type": "trigger_event", "id": "event_steam_sealed"},
        ],
    },
]
