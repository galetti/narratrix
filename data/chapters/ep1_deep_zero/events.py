# narratrix_engine/data/chapters/ep1_deep_zero/events.py
from engine.constants import *

# Globale Variable: daily_tasks_done wird über Knowledge-Flags simuliert
# Wir nutzen Flags: task_vent_done, task_coffee_done, task_relay_done

QUESTS = {
    "daily_routine": {
        "title": "Tagesroutine",
        "desc": "Erledige deine Aufgaben auf der Station.",
        "stages": {
            0: "Bringe die Lüftung zum Schweigen, besorge Kaffee und warte auf Anweisungen.",
            1: "Aufgaben erledigt: 1/3",
            2: "Aufgaben erledigt: 2/3",
            3: "Alle Aufgaben erledigt. Melde dich im Kontrollraum zur Übergabe."
        },
        "current_stage": 0
    }
}

NARRATIVE_MATRIX = [
    # Start
    {
        "id": "intro_wakeup",
        "trigger": "location",
        "location": "room_quarters_aris",
        "once": True,
        "description": "Der Wecker summt. 07:00 Uhr Bordzeit. Ein weiterer Tag in der Leere."
    }
]

EVENTS = [
    # --- ATMOSPHÄRE ---
    {
        "id": "vent_rattle",
        "trigger": "time",
        "trigger_time": 0,
        "repeat": True,
        "origin_id": "room_quarters_aris",
        "sound_msg": "Ein nerviges, rhythmisches Klappern aus der Lüftung.",
        "condition": {"type": "knowledge", "value": "task_vent_done", "not": True} # Stoppt wenn repariert
    },
    {
        "id": "sato_mumbling",
        "trigger": "time",
        "trigger_time": 2, # Nach 2 Minuten
        "once": True,
        "origin_id": "room_corridor_quarters",
        "sound_msg": "Schritte und ein leises Selbstgespräch. Jemand murmelt über 'falsche Messwerte'."
    },
    {
        "id": "sato_move_to_mess",
        "trigger": "time",
        "trigger_time": 5,
        "once": True,
        "effects": [
            {"type": "move_npc", "npc": "sato", "target": "room_mess"},
            {"type": "set_npc_state", "npc": "sato", "value": "coffee_craving"}
        ]
    },
    
    # --- AUFGABEN FORTSCHRITT ---
    {
        "id": "task_vent_done",
        "trigger": "manual", # Wird vom Item/Combination getriggert
        "effects": [
            {"type": "learn", "fact": "task_vent_done"},
            {"type": "trigger_event", "id": "check_daily_progress"}
        ]
    },
    {
        "id": "task_coffee_done",
        "trigger": "manual",
        "effects": [
            {"type": "learn", "fact": "task_coffee_done"},
            {"type": "set_npc_state", "npc": "sato", "value": "coffee_happy"},
            {"type": "trigger_event", "id": "check_daily_progress"}
        ]
    },
    {
        "id": "task_relay_done",
        "trigger": "manual",
        "effects": [
            {"type": "learn", "fact": "task_relay_done"},
            {"type": "trigger_event", "id": "check_daily_progress"}
        ]
    },
    
    # --- PROGRESS CHECKER ---
    # Prüft, ob alle 3 Tasks erledigt sind. Da EventManager komplexe Conditions limitiert unterstützt,
    # machen wir es hier über Kaskaden oder wir nutzen die Quest-Logik.
    # Vereinfachung: Wir nutzen 'complex' condition
    {
        "id": "check_daily_progress",
        "trigger": "complex",
        "repeat": True, # Prüft jedes Mal wenn getriggert
        "conditions": [
            {"type": "knowledge", "value": "task_vent_done"},
            {"type": "knowledge", "value": "task_coffee_done"},
            {"type": "knowledge", "value": "task_relay_done"},
            {"type": "knowledge", "value": "evening_started", "not": True}
        ],
        "operator": "AND",
        "effects": [
            {"type": "learn", "fact": "evening_started"},
            {"type": "message", "message": "DURCHSAGE: 'Schichtende in 15 Minuten. Dr. Thorne, bitte zur Übergabe in den Kontrollraum.'"},
            {"type": "set_npc_state", "npc": "sato", "value": "evening"},
            {"type": "move_npc", "npc": "sato", "target": "room_control"},
            {"type": "quest_update", "quest_update": {"id": "daily_routine", "stage": 3}}
        ]
    },

    # --- CORE DURCHSAGE (Mittags) ---
    {
        "id": "core_announcement",
        "trigger": "time",
        "trigger_time": 20, # Später am Tag
        "origin_id": "room_corridor_main", # Lautsprecher
        "sound_msg": "C.O.R.E.: 'Wartungsauftrag 404. Emitter-Relais Drift. Bitte manuell nachjustieren.'",
        "description": "Die Stimme von C.O.R.E. hallt durch die Gänge."
    },

    # --- FINALE (Der Bruch) ---
    {
        "id": "finale_klong",
        "trigger": "location",
        "location": "room_control",
        "condition": {"type": "knowledge", "value": "evening_started"},
        "once": True,
        "description": "Du betrittst den Kontrollraum. Die Beleuchtung ist gedimmt. Sato wartet bereits.",
        "effects": [
            {"type": "message", "message": "Sato: 'Lass uns die Daten abzeichnen.'"},
            # Wir warten kurz, dann...
            {"type": "trigger_event", "id": "finale_sound_delayed"}
        ]
    },
    {
        "id": "finale_sound_delayed",
        "trigger": "manual", # Könnte über Timer gelöst werden, hier direkt
        # Simulieren wir Zeitverzögerung durch 'wait' im Kopf des Spielers?
        # Wir machen es als Folgemessage.
        "description": "Du tippst den Status ein. Ein Monitor flackert: 0.0004 -> 9.9999 -> 0.0004.\nSato lacht: 'Glitch. Wir brauchen neue Hardware.'",
        "effects": [
             {"type": "trigger_event", "id": "the_sound"}
        ]
    },
    {
        "id": "the_sound",
        "trigger": "manual",
        "origin_id": "exterior_hull",
        "sound_msg": "Ein schweres, metallisches KLONG. Als hätte etwas Gewaltiges gegen die Außenhülle geschlagen.",
        "volume": 2.0, # Sehr laut!
        "effects": [
            {"type": "message", "message": "Sato hört auf zu lachen. Er wird bleich.\nSato: 'Aris... wir sind im Vakuum. Was zur Hölle erzeugt Schall an der Außenhülle?'"},
            {"type": "game_over", "reason": "ENDE SZENE 1 - FORTSETZUNG FOLGT"}
        ]
    }
]