# data/modules/deep_zero/chapters/ep2_habitat_sector/npcs.py
from __future__ import annotations

from engine.constants import ATTR_ALIASES, ATTR_DESC, ATTR_NAME
from engine.schema import NPCData

NPCS: list[NPCData] = [
    {
        "id": "dr_vance",
        ATTR_NAME: "Dr. Elena Vance",
        ATTR_DESC: "Die leitende Biosphären-Biologin. Sie trägt einen Schutzanzug und beobachtet nervös die Druckanzeigen.",
        ATTR_ALIASES: ["vance", "dr", "elena", "biologin", "botanikerin", "wissenschaftlerin"],
        "location": "hydroponics_bay",
        "level": 0,
        "state": "panicked",
        "behavior_id": "idle",
        "img": "face_val_pain",
        "personality": "Brilliant, anxious biosphere lead biologist trying to stay composed under pressure.",
        "dialogue": {
            "panicked": {
                "greeting": "Gott sei Dank, jemand ist da! Wir haben einen kritischen Notfall in der Biosphäre!",
                "problem": {
                    "label": "Was ist hier passiert?",
                    "text": (
                        "Eine Überdruckwelle aus dem Kühlsystem! Das Überdruckventil oben auf der Bühne klemmt, "
                        "und die Dampfleitung pfeift aus allen Nähten! Wenn wir den Druck nicht regulieren und das Leck schließen, "
                        "kollabiert der Sauerstoffkreislauf der gesamten Station!"
                    ),
                    "effect": {"type": "trigger_event", "id": "event_quest_start"},
                },
                "solution": {
                    "label": "Ich kümmere mich um Ventil und Leitung.",
                    "text": (
                        "Danke! Klettere über die Service-Leiter auf Ebene 1. Mit deinem Omni-Tool kannst du das Ventil entlasten. "
                        "Für das Leck brauchst du hitzefestes Dichtungsband – in deinem Quartier 4B müsste noch welches im Wandspind liegen!"
                    ),
                    "condition": "ep2_quest_started",
                },
            },
            "waiting": {
                "greeting": "Hörst du das laute Zischen von oben? Der Druck steigt weiter – beeil dich!",
                "default": "Klettere auf Ebene 1, justiere das Überdruckventil mit dem Omni-Tool und versiegele das Leck mit Dichtungsband!",
            },
            "relieved": {
                "greeting": "Unglaublich, Thorne! Die Druckkurve ist wieder im grünen Bereich. Das Zischen hat aufgehört.",
                "reward": {
                    "label": "Status melden",
                    "text": (
                        "Hervorragende Arbeit. Du hast die Lebenshaltung von Deep Zero gerettet. "
                        "Wenn du weiter zum Hauptreaktor musst: Hier ist mein persönlicher Zugangschip. Pass auf dich auf!"
                    ),
                    "effect": [
                        {"type": "receive_item", "item": "core_access_chip"},
                        {"type": "trigger_event", "id": "event_chapter_end"},
                    ],
                },
            },
        },
    },
    {
        "id": "scrubber",
        ATTR_NAME: "Scrubber (MK-2)",
        ATTR_DESC: "Eine flache, scheibenförmige Wartungsdrohne mit rotierenden Bürsten und leisem Summen.",
        ATTR_ALIASES: ["scrubber", "drohne", "bot", "reinigungsbot", "mk-2", "putzbot"],
        "location": "living_commons",
        "level": 0,
        "state": "cleaning",
        "behavior_id": "idle",
        "dialogue": {
            "cleaning": {
                "greeting": "SUMM. BEEP. Status: Lounge-Boden zu 98.4% partikelfrei. Bitte keine Notrationen krümeln.",
                "default": "BEEP. Systembetrieb regulär. Feuchtraum-Reinigung wegen Überdruck-Warnung pausiert.",
            },
        },
    },
]
