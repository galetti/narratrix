# narratrix_engine/data/chapters/ep0_test_lab/rooms.py
from __future__ import annotations

from engine.constants import ATTR_DESC, ATTR_ID, ATTR_NAME
from engine.schema import RoomData

ROOMS: dict[str, RoomData] = {
    "central_hub": {
        ATTR_ID: "central_hub",
        ATTR_NAME: "Zentraler Test-Hub",
        ATTR_DESC: (
            "Der zentrale Knotenpunkt des modularen Narratrix-Testlabors. "
            "Leuchtende {sector_signs} weisen den Weg in die verschiedenen Mechanik-Sektoren. "
            "In der Mitte des Raums steht das {central_terminal}. "
            "Nach Westen führt die {anteroom_door} in den Akustik-Sektor."
        ),
        "img": "hub_main",
        "exits": {
            "north": "test_chamber",
            "east": "dialogue_lab",
            "west": "briefing_anteroom",
            "up": "upper_deck",
            "down": "lower_deck",
        },
        "acoustics": {
            "upper_deck": 0.8,
        },
        "_editor": {"x": 0, "y": 0, "z": 0},
    },
    "test_chamber": {
        ATTR_ID: "test_chamber",
        ATTR_NAME: "Physiklabor: Aggregatzustände & Hitze",
        ATTR_DESC: (
            "Ein steriler Testraum für physikalische Aggregatzustände, Schmelzprozesse und Höhenreichweite. "
            "Ein {high_shelf} ragt in die Höhe. Am Boden dampft eine {coolant_pool} und der glühende {thermal_furnace} erhitzt den Raum. "
            "Im {hazard_locker} lagern Testbehälter. "
            "Nach Osten führt ein massives {security_door} zum angeschlossenen Wiegerätsel-Sektor."
        ),
        "img": "lab_white",
        "exits": {
            "south": "central_hub",
            "east": "vault_room",
        },
        "_editor": {"x": 0, "y": -150, "z": 0},
    },
    "vault_room": {
        ATTR_ID: "vault_room",
        ATTR_NAME: "Physiklabor: Präzisions-Wiegetest",
        ATTR_DESC: (
            "Eine schallisolierte Kammer zur Demonstration von Waagenkalibrierung und Gewichtssensorik. "
            "In der Wand ist der {resonance_vault} eingelassen, daneben steht eine hochpräzise {precision_scale}."
        ),
        "exits": {
            "west": "test_chamber",
        },
        "_editor": {"x": 150, "y": -150, "z": 0},
    },
    "briefing_anteroom": {
        ATTR_ID: "briefing_anteroom",
        ATTR_NAME: "Akustiksektor: Schalldämpfung & Türen",
        ATTR_DESC: (
            "Ein Prüfraum zur Demonstration von Raumakustik, Wanddämpfung und Türblockaden. "
            "An der Wand flackern {briefing_consoles}. "
            "Nach Norden führt die schwere {soundproof_door} zur schallundurchlässigen Testkammer. "
            "Durch die {anteroom_door} gelangt man nach Osten zurück in den zentralen Hub."
        ),
        "exits": {
            "east": "central_hub",
            "north": "soundproof_office",
        },
        "_editor": {"x": -150, "y": 0, "z": 0},
    },
    "soundproof_office": {
        ATTR_ID: "soundproof_office",
        ATTR_NAME: "Akustiksektor: Schallisolierte Kammer (Abhörszenario)",
        ATTR_DESC: (
            "Ein abhörsicherer Raum mit 100% Schalldämpfung zur Simulation verdeckter Gespräche und Belauschung. "
            "In der Mitte steht ein {conference_table}."
        ),
        "exits": {
            "south": "briefing_anteroom",
        },
        "acoustics": {
            "briefing_anteroom": 0.0,
            "central_hub": 0.0,
        },
        "_editor": {"x": -150, "y": -150, "z": 0},
    },
    "upper_deck": {
        ATTR_ID: "upper_deck",
        ATTR_NAME: "Kletterparcours: Höhenebenen & Drohnen-KI",
        ATTR_DESC: (
            "Ein erhöhter Testlaufsteg auf Ebene 1 zur Demonstration von Klettermechaniken, Höhenunterschieden "
            "und fliehendem Drohnen-Verhalten. Durch das Gitter blickst du auf den zentralen Hub hinab."
        ),
        "img": "deck_upper",
        "exits": {
            "down": "central_hub",
        },
        "acoustics": {
            "central_hub": 0.8,
        },
        "_editor": {"x": 0, "y": 0, "z": 1},
    },
    "lower_deck": {
        ATTR_ID: "lower_deck",
        ATTR_NAME: "Maschinendeck: Lärmsimulation & Werkbank",
        ATTR_DESC: (
            "Ein funktioneller Werkstattbereich unterhalb des Hubs. "
            "Hier demonstrieren die {noisy_machine} weitreichende Schallemissionen und die {workbench} das Handwerkssystem."
        ),
        "img": "deck_lower",
        "exits": {
            "up": "central_hub",
        },
        "_editor": {"x": 0, "y": 0, "z": -1},
    },
    "dialogue_lab": {
        ATTR_ID: "dialogue_lab",
        ATTR_NAME: "Gesprächslabor: Dialogbäume & Wissensaustausch",
        ATTR_DESC: (
            "Ein schallgedämpfter Kommunikationsraum zur Verifikation von Verzweigungsdialogen, Stimmungszuständen und Faktenabfragen. "
            "An der Wand befindet sich die {dialogue_console}."
        ),
        "exits": {
            "west": "central_hub",
        },
        "_editor": {"x": 150, "y": 0, "z": 0},
    },
}
