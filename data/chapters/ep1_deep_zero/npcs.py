# narratrix_engine/data/chapters/ep1_arrival/npcs.py
from engine.constants import *

NPCS = [
    {
        "id": "sato",
        ATTR_NAME: "Dr. Sato",
        ATTR_DESC: "Der Chefingenieur. Er hat Öl im Gesicht und wirkt gestresst.",
        "location": "room_inner_corridor_north",
        "state": "working",
        "dialogue": {
            "working": {
                "greeting": "Ah, der Neue. Der Mann, der Neutrinos flüstern hören kann.",
                "problem": {
                    "label": "Was gibt es?",
                    "text": "Wir haben einen alten Bot, 'Rusty'. Navigations-Chip durchgebrannt. Er macht einen Höllenlärm in den Schächten. Ich kriege kein Auge zu.",
                    "effect": {"type": "trigger_event", "id": "quest_start_rusty"}
                },
                "solution": {
                    "label": "Ich kümmere mich darum.",
                    "text": "Du bist der Experte für Wellen. Finde ihn und schalte ihn ab. Hier nimm meine Zange, die liegt da irgendwo.",
                    "condition": "quest_started" # Nur wenn Quest aktiv
                }
            },
            "waiting": {
                "greeting": "Hörst du das? Immer noch Krach. Finde diesen Bot!",
                "default": "Such in den Wartungsschächten. Folge dem Lärm."
            },
            "grateful": {
                "greeting": "Himmlische Ruhe. Gute Arbeit, Thorne.",
                "reward": {
                    "label": "Bericht erstatten",
                    "text": "Vielleicht bist du doch zu gebrauchen. Hier ist dein Zimmerschlüssel und ein Omni-Tool.",
                    "effect": [
                        {"type": "receive_item", "item": "keycard_quarters"},
                        {"type": "receive_item", "item": "tool_omni"},
                        {"type": "trigger_event", "id": "tutorial_end"}
                    ]
                }
            }
        }
    },
    {
        "id": "rusty",
        ATTR_NAME: "Rusty (MK-1 Bot)",
        ATTR_DESC: "Ein kastenförmiger Roboter. Er fährt immer wieder gegen die Wand. Sein Status-Licht blinkt rot.",
        "location": "room_outer_waste",
        "level": 2, # ER IST OBEN! Man muss klettern.
        "state": "malfunction",
        "behavior_id": "idle", # Bewegt sich nicht weg
        "toughness": 1,
        "dialogue": {
            "malfunction": {
                "greeting": "BEEP. FEHLER. BEEP. NAVIGATION OFF-LINE.",
                "default": "SYSTEM CRITICAL."
            },
            "disabled": {
                "greeting": "(Keine Reaktion)",
                "default": "Der Bot ist abgeschaltet."
            }
        }
    }
]