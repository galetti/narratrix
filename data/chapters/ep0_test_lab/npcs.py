# narratrix_engine/data/chapters/ep0_test_lab/npcs.py
from __future__ import annotations

from engine.constants import ATTR_ALIASES, ATTR_DESC, ATTR_NAME
from engine.schema import NPCData

NPCS: list[NPCData] = [
    {
        "id": "runner_bot",
        ATTR_NAME: "Läufer-Bot",
        ATTR_DESC: "Ein kleiner Sicherheitsroboter auf Rädern mit blinkenden akustischen Sensoren.",
        ATTR_ALIASES: ["bot", "roboter", "läufer", "läufer-bot", "wache"],
        "location": "upper_deck",
        "state": "idle",
        "behavior_id": "guard",
        "speed": 2.0,
        "waypoints": ["upper_deck", "central_hub", "lower_deck", "central_hub"],
        "waypoint_index": 0,
        "dialogue": {
            "idle": {
                "greeting": "Beep boop. Sicherheitspatrouille aktiv.",
                "lauf": {
                    "label": "Geh zur Testkammer!",
                    "text": "Verstanden. Ändere Route zur Testkammer.",
                    "effect": {
                        "type": "move_npc",
                        "npc": "runner_bot",
                        "target": "test_chamber",
                    },
                },
                "status": {
                    "label": "Statusbericht",
                    "text": (
                        "Systeme nominal. Akustische Sensoren aktiv. "
                        "Bei Maschinenlärm im Unterdeck untersuche ich sofort die Quelle."
                    ),
                },
            }
        },
    },
    {
        "id": "shy_drone",
        ATTR_NAME: "Scheue Wartungsdrohne",
        ATTR_DESC: "Eine schwebende Diagnose-Drohne mit flackerndem Akku. Sie weicht hektisch zurück, wenn man ihr zu nahe kommt.",
        ATTR_ALIASES: ["drohne", "wartungsdrohne", "diagnose-drohne", "scheue"],
        "location": "upper_deck",
        "state": "skittish",
        "behavior_id": "fearful",
        "speed": 1.0,
        "states": {
            "skittish": {
                "visuals": {
                    "desc": "Eine schwebende Diagnose-Drohne mit fast leerem Akku. Sie zittert nervös.",
                },
                "behavior": {"behavior_id": "fearful"},
                "dialogue": {
                    "greeting": "Fiep! (Die Drohne weicht scheu zurück. Ihre Akku-Anzeige blinkt rot.)",
                    "calm": {
                        "label": "Beruhige dich, kleine Drohne.",
                        "text": "Bzzz... Niedrige Spannung... Brauche Energiezelle...",
                    },
                    "feed_cell": {
                        "hidden": True,
                        "condition": "received_energy_cell",
                        "text": (
                            "Zirr-Piep! (Die Drohne absorbiert die Energiezelle und projiziert "
                            "einen Kalibrierungscode an die Wand: 'Tresor-Waage: 1.50 kg Eichgewicht + "
                            "1.00 kg blauer Schlüssel = 2.50 kg. Resonanz-Frequenz übertragen!')"
                        ),
                        "effect": [
                            {"type": "learn", "fact": "knows_resonance_tuning"},
                            {"type": "set_npc_state", "npc": "shy_drone", "value": "friendly"},
                            {
                                "type": "quest_update",
                                "quest_update": {"id": "core_calibration", "stage": 2},
                            },
                        ],
                    },
                },
            },
            "friendly": {
                "visuals": {
                    "desc": "Die Wartungsdrohne summt zufrieden mit voll aufgeladenem Kern.",
                },
                "behavior": {"behavior_id": "idle"},
                "dialogue": {
                    "greeting": "Piep-Summ! (Die Drohne schwebt zutraulich neben dir.)",
                    "tip": {
                        "label": "Hast du noch einen Hinweis zum Resonanz-Kern?",
                        "text": (
                            "Projektion: 'Nach Öffnung des Tresors muss der beschädigte Resonanz-Kern "
                            "erst mit einem Werkzeug repariert werden, bevor er ins Zentral-Terminal passt.'"
                        ),
                    },
                },
            },
        },
    },
]
