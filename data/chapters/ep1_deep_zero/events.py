# narratrix_engine/data/chapters/ep1_arrival/events.py
from engine.constants import *

QUESTS = {
    "noise_pollution": {
        "title": "Lärmbelästigung",
        "desc": "Finde und deaktiviere den defekten Wartungsbot 'Rusty'.",
        "stages": {
            0: "Dr. Sato hat Kopfschmerzen. Finde die Lärmquelle.",
            1: "Der Bot ist abgeschaltet. Melde dich bei Sato.",
            2: "Abgeschlossen."
        },
        "current_stage": 0
    }
}

NARRATIVE_MATRIX = [
    {
        "id": "intro_sequence",
        "trigger": "time",
        "trigger_time": 0,
        "once": True,
        "description": "Die Andockklammern lösen sich mit einem metallischen Ächzen. Dein Shuttle, die 'Charon', hat dich sicher abgesetzt.",
        "effects": [
            {"type": "message", "message": "C.O.R.E. (Headset): 'Willkommen, Dr. Thorne. Dr. Sato erwartet Sie im Inner Ring. Folgen Sie den grünen Markierungen.'"}
        ]
    }
]

EVENTS = [
    # --- QUEST START ---
    {
        "id": "quest_start_rusty",
        "trigger": "manual", # Via Dialog
        "quest_start": "noise_pollution",
        "effects": [
            {"type": "learn", "fact": "quest_started"},
            {"type": "set_npc_state", "npc": "sato", "value": "waiting"}
        ]
    },

    # --- DER LÄRM (Kernmechanik) ---
    {
        "id": "rusty_noise_loop",
        "trigger": "time",
        "trigger_time": 0,
        "repeat": True, # Feuert jeden Tick
        "origin_id": "room_outer_waste",
        "condition": {"type": "knowledge", "value": "rusty_dead", "not": True}, # Stoppt wenn Rusty tot
        "sound_msg": "Ein mechanisches KRK-KLONG. Metall auf Metall.",
        "volume": 2.0 # Sehr laut, weit hörbar
    },

    # --- ABSCHALTEN ---
    {
        "id": "rusty_shutdown",
        "trigger": "manual", # Via Item Use
        "effects": [
            {"type": "learn", "fact": "rusty_dead"},
            {"type": "set_npc_state", "npc": "rusty", "value": "disabled"},
            {"type": "update_object", "target": "rusty", "updates": {"desc": "Ein stiller Haufen Metallschrott."}},
            {"type": "set_npc_state", "npc": "sato", "value": "grateful"},
            {"type": "quest_update", "quest_update": {"id": "noise_pollution", "stage": 1}},
            {"type": "message", "message": "KLACK. Der Bot sackt zusammen. Endlich Stille."}
        ]
    },

    # --- ENDE ---
    {
        "id": "tutorial_end",
        "trigger": "manual",
        "effects": [
            {"type": "quest_update", "quest_update": {"id": "noise_pollution", "stage": 2}},
            {"type": "message", "message": "Du hast deine Ausrüstung erhalten."},
            {"type": "game_over", "reason": "TUTORIAL ABGESCHLOSSEN - Einleitung in Szene 2..."}
        ]
    }
]