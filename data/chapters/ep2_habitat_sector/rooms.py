# narratrix_engine/data/chapters/ep2_habitat_sector/rooms.py
from __future__ import annotations

from engine.constants import ATTR_DESC, ATTR_ID, ATTR_NAME
from engine.schema import RoomData

ROOMS: dict[str, RoomData] = {
    # 1. Zugangsschleuse zum Wohnbereich
    "quarters_airlock": {
        ATTR_ID: "quarters_airlock",
        ATTR_NAME: "Habitat-Schleuse",
        ATTR_DESC: (
            "Eine kompakte Dekontaminations-Schleuse am Eingang des Wohnsektors. "
            "Ein {disinfection_scanner} summt leise über dem Eingang. "
            "Das massive {airlock_door} führt nach Osten in die Gemeinschaftslounge."
        ),
        "exits": {
            "east": "living_commons",
        },
        "acoustics": {
            "living_commons": 0.6,
        },
    },

    # 2. Gemeinschaftsbereich / Lounge
    "living_commons": {
        ATTR_ID: "living_commons",
        ATTR_NAME: "Gemeinschaftslounge",
        ATTR_DESC: (
            "Ein runder Aufenthaltsraum mit warmer Beleuchtung. An der Wand steht ein {dispenser} "
            "für Rationen und eine abgenutzte {couch}. Ein flackernder {information_screen} "
            "zeigt Statusberichte der Station. Ein Gang nach Süden führt zu den Mannschaftsquartieren, "
            "während ein zweiflügeliges Schott nach Norden in die Biosphäre leitet."
        ),
        "exits": {
            "west": "quarters_airlock",
            "north": "hydroponics_bay",
            "south": "crew_cabin_thorne",
        },
        "acoustics": {
            "quarters_airlock": 0.6,
            "hydroponics_bay": {"transmission": 0.75, "direction_text": "aus dem Biosphären-Trakt"},
            "crew_cabin_thorne": 0.4,
        },
    },

    # 3. Persönliches Quartier
    "crew_cabin_thorne": {
        ATTR_ID: "crew_cabin_thorne",
        ATTR_NAME: "Quartier 4B (Thorne)",
        ATTR_DESC: (
            "Ein schmuckloses, funktionales Einzelquartier. An der Wand steht eine schmale {bunk_bed}. "
            "Gegenüber befindet sich ein {terminal_desk} mit Leseleuchte und ein metallener {locker} "
            "für persönliche Gegenstände. Die {cabin_door} führt zurück nach Norden in die Lounge."
        ),
        "exits": {
            "north": "living_commons",
        },
        "acoustics": {
            "living_commons": 0.4,
        },
    },

    # 4. Biosphäre & Filteranlagen (mit oberer Ebene)
    "hydroponics_bay": {
        ATTR_ID: "hydroponics_bay",
        ATTR_NAME: "Biosphäre & Filteranlage",
        ATTR_DESC: (
            "Ein feuchter, warmer Hallentrakt voller üppiger Pflanzen und leuchtender {hydroponic_tanks}. "
            "In der Mitte brummt die zentrale {filtration_unit}. "
            "Eine gelbe {catwalk_ladder} führt hinauf zur Überdruckbühne auf Ebene 1, "
            "wo eine zischende {steam_pipe} und ein massives {pressure_valve} verbaut sind. "
            "Ein Durchgang führt nach Süden zurück zur Lounge."
        ),
        "exits": {
            "south": "living_commons",
        },
        "acoustics": {
            "living_commons": {"transmission": 0.75, "direction_text": "hinter der Biosphären-Tür"},
        },
    },
}
