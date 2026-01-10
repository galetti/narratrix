# narratrix_engine/data/chapters/ep0_test_lab/npcs.py
from engine.constants import *

NPCS = [
    {
        "id": "runner_bot",
        ATTR_NAME: "Läufer-Bot",
        ATTR_DESC: "Ein kleiner Roboter auf Rädern.",
        "location": "upper_deck",
        "state": "idle",
        "dialogue": {
            "idle": {
                "greeting": "Beep boop. Ich warte auf Befehle.",
                "lauf": {
                    "label": "Lauf in den Keller!",
                    "text": "Verstanden. Ich begebe mich nach unten.",
                    # TEST: Neues Effekt-System
                    "effect": {
                        "type": "move_npc",
                        "npc": "runner_bot",
                        "target": "lower_deck"
                    }
                },
                "komm": {
                    "label": "Komm her!",
                    "text": "Bin unterwegs.",
                    # TEST: Context-basiertes Target (wo der Spieler ist, nicht hardcoded)
                    # Da move_npc im EffectProcessor 'context_npc' nutzt, 
                    # brauchen wir hier Logik. Aktuell muss target eine ID sein.
                    # Wir schicken ihn zur Zentrale als Test.
                    "effect": {
                        "type": "move_npc",
                        "npc": "runner_bot",
                        "target": "central_hub"
                    }
                }
            }
        },
        "behavior": {
            # Einfaches Verhalten: Wenn er im Lower Deck ist, macht er Lärm
        }
    }
]