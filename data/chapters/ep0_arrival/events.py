# data/chapters/ep0_arrival/events.py

MATRIX = [
    # --- START EVENTS ---
    {
        "id": "intro_sequence",
        "trigger": "time",
        "trigger_time": 0,
        "origin_id": "ship_cockpit",
        "title": "Erwachen",
        "description": "Dein Kopf dröhnt. Warnleuchten pulsieren rhythmisch im Takt deiner Kopfschmerzen. Der Geruch von verbranntem Ozon liegt in der Luft.",
        "sound_msg": "Alarmsirenen in der Ferne.",
        "quest_update": {"id": "q_main_survival", "stage": 1} # Startet die Quest
    },
    
    # --- QUEST FORTSCHRITT: Cockpit verlassen ---
    {
        "id": "leave_cockpit_trigger",
        "trigger": "condition",
        "condition": {"type": "location", "value": "ship_corridor"}, # Wenn Spieler im Korridor ist
        "description": "Du lässt das zerstörte Cockpit hinter dir. Der Korridor ist dunkel und kalt.",
        "quest_update": {"id": "q_main_survival", "stage": 2}, # Update auf Stufe 2
        "once": True
    },

    # --- EXISTIERENDE EVENTS (Beispiel) ---
    {
        "id": "oxygen_warning",
        "trigger": "time",
        "trigger_time": 15,
        "message": "WARNUNG: Sauerstoffreserve bei 80%."
    }
]