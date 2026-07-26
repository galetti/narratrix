# narratrix_engine/data/chapters/ep0_test_lab/npcs.py
from engine.constants import *

NPCS = [
    {
        "id": "runner_bot",
        ATTR_NAME: "Läufer-Bot",
        ATTR_DESC: "Ein kleiner Roboter auf Rädern mit blinkenden Lichtern.",
        "location": "upper_deck",
        "state": "idle",
        
        # KI Konfiguration
        "behavior_id": "guard",  # Nutzt den Behavior Tree 'guard' (Patrouille + Wache)
        "speed": 2.0,            # Ziemlich schnell (2 Räume pro Minute)
        
        # Patrouillen-Route
        "waypoints": ["upper_deck", "central_hub", "lower_deck", "central_hub"],
        "waypoint_index": 0,

        "dialogue": {
            "idle": {
                "greeting": "Beep boop. Sicherheitspatrouille aktiv.",
                "lauf": {
                    "label": "Geh zur Testkammer!",
                    "text": "Verstanden. Ändere Route zur Testkammer.",
                    # Override via Effect: Schickt ihn weg, aber KI wird danach versuchen,
                    # wieder zur Patrouille zurückzukehren (da 'target_location' gelöscht wird bei Ankunft).
                    "effect": {
                        "type": "move_npc",
                        "npc": "runner_bot",
                        "target": "test_chamber"
                    }
                },
                "status": {
                    "label": "Statusbericht",
                    "text": "Systeme nominal. Sensoren aktiv. Ich höre alles."
                }
            }
        }
    }
]
