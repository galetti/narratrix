# data/modules/deep_zero/chapters/ep1_deep_zero/npcs.py
from __future__ import annotations

from engine.constants import ATTR_ALIASES, ATTR_DESC, ATTR_NAME
from engine.schema import NPCData

NPCS: list[NPCData] = [
    {
        "id": "sato",
        ATTR_NAME: "Dr. Sato",
        ATTR_DESC: "Der Chefingenieur. Er hat Öl im Gesicht und wirkt gestresst.",
        ATTR_ALIASES: ["sato", "dr", "doktor", "chefingenieur", "ingenieur"],
        "location": "room_inner_corridor_north",
        "level": 0,
        "state": "working",
        "behavior_id": "idle",
        "personality": "Overworked, gruff but fair chief engineer who hates unnecessary noise and respects competence.",
        "dialogue": {
            "working": {
                "greeting": "Ah, der Neue. Der Mann, der Neutrinos flüstern hören kann.",
                "problem": {
                    "label": "Was gibt es?",
                    "text": "Wir haben einen alten Bot, 'Rusty'. Navigations-Chip durchgebrannt. Er macht einen Höllenlärm in den Schächten. Ich kriege kein Auge zu.",
                    "effect": {"type": "trigger_event", "id": "quest_start_rusty"},
                },
                "solution": {
                    "label": "Ich kümmere mich darum.",
                    "text": "Du bist der Experte für Wellen. Finde ihn und schalte ihn ab. Hier nimm meine Zange, die liegt da irgendwo.",
                    "condition": "ep1_quest_started",
                },
            },
            "waiting": {
                "greeting": "Hörst du das? Immer noch Krach. Finde diesen Bot!",
                "default": "Such in den Wartungsschächten. Folge dem Lärm.",
            },
            "grateful": {
                "greeting": "Himmlische Ruhe. Gute Arbeit, Thorne.",
                "reward": {
                    "label": "Bericht erstatten",
                    "text": "Vielleicht bist du doch zu gebrauchen. Hier ist dein Zimmerschlüssel und ein Omni-Tool. Auf zum Habitat-Sektor!",
                    "effect": [
                        {"type": "receive_item", "item": "keycard_quarters"},
                        {"type": "receive_item", "item": "tool_omni"},
                        {"type": "trigger_event", "id": "tutorial_end"},
                    ],
                },
            },
        },
    },
    {
        "id": "rusty",
        ATTR_NAME: "Rusty (MK-1 Bot)",
        ATTR_DESC: "Ein kastenförmiger Roboter im Eingang des Wartungsschachts. Er fährt immer wieder gegen die Wand. Sein Status-Licht blinkt rot.",
        ATTR_ALIASES: ["rusty", "bot", "roboter", "mk-1", "wartungsbot"],
        "location": "room_outer_waste",
        "level": 2,
        "state": "malfunction",
        "behavior_id": "idle",
        "toughness": 1,
        "dialogue": {
            "malfunction": {
                "greeting": "BEEP. FEHLER. BEEP. NAVIGATION OFF-LINE.",
                "default": "SYSTEM CRITICAL.",
            },
            "disabled": {
                "greeting": "(Keine Reaktion)",
                "default": "Der Bot ist abgeschaltet.",
            },
        },
    },
]
