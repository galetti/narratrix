# data/modules/deep_zero/chapters/ep1_deep_zero/events.py
from __future__ import annotations

from engine.schema import EventData, QuestDefinitionData

QUESTS: dict[str, QuestDefinitionData] = {
    "noise_pollution": {
        "title": "Lärmbelästigung",
        "desc": "Finde und deaktiviere den defekten Wartungsbot 'Rusty'.",
        "stages": {
            0: "Dr. Sato hat Kopfschmerzen. Finde die Lärmquelle.",
            1: "Der Bot ist abgeschaltet. Melde dich bei Sato.",
            2: "Abgeschlossen.",
        },
        "completion_stage": 2,
    }
}

NARRATIVE_MATRIX: list[EventData] = [
    {
        "id": "intro_sequence",
        "trigger": "time",
        "trigger_time": 0,
        "description": "Die Andockklammern lösen sich mit einem metallischen Ächzen. Dein Shuttle, die 'Charon', hat dich sicher abgesetzt.",
        "effects": [
            {
                "type": "message",
                "log_type": "character",
                "message": "C.O.R.E. (Headset): 'Willkommen, Dr. Thorne. Dr. Sato erwartet Sie im Inner Ring. Folgen Sie den grünen Markierungen.'",
            }
        ],
    }
]

EVENTS: list[EventData] = [
    {
        "id": "quest_start_rusty",
        "trigger": "manual",
        "quest_start": "noise_pollution",
        "effects": [
            {"type": "learn", "fact": "ep1_quest_started"},
            {"type": "set_npc_state", "npc": "sato", "value": "waiting"},
        ],
    },
    {
        "id": "rusty_noise_loop",
        "trigger": "time",
        "trigger_time": 0,
        "repeat": True,
        "origin_id": "room_outer_waste",
        "condition": {"type": "knowledge", "value": "rusty_dead", "not": True},
        "sound_msg": "Ein mechanisches KRK-KLONG. Metall auf Metall.",
        "volume": 2.0,
    },
    {
        "id": "rusty_shutdown",
        "trigger": "manual",
        "effects": [
            {"type": "quest_start", "id": "noise_pollution"},
            {"type": "learn", "fact": "rusty_dead"},
            {"type": "set_npc_state", "npc": "rusty", "value": "disabled"},
            {"type": "update_object", "target": "rusty", "updates": {"desc": "Ein stiller Haufen Metallschrott."}},
            {"type": "set_npc_state", "npc": "sato", "value": "grateful"},
            {"type": "quest_update", "quest_update": {"id": "noise_pollution", "stage": 1}},
            {"type": "message", "message": "KLACK. Der Bot sackt zusammen. Endlich Stille."},
        ],
    },
    {
        "id": "tutorial_end",
        "trigger": "manual",
        "effects": [
            {"type": "quest_complete", "id": "noise_pollution"},
            {"type": "message", "message": "Du hast deine Ausrüstung erhalten und betrittst den Habitat-Sektor."},
            {
                "type": "load_chapter",
                "chapter": "data.modules.deep_zero.chapters.ep2_habitat_sector.config",
            },
        ],
    },
]
