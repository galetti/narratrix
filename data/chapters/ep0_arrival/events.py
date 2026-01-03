MATRIX = [
    # --- START ---
    {
        "id": "start_game",
        "trigger": "time",
        "trigger_time": 0,
        "title": "Kapitel 0: Ankunft",
        "description": "Erwachen. Schmerz. Du liegst auf dem Boden des Cockpits.",
        "quest_start": "q_tutorial",
        "sound_msg": "Ein tiefes Ächzen von Metall."
    },
    
    # --- TÜR ÖFFNEN (Trigger) ---
    {
        "id": "door_opened",
        "trigger": "condition",
        "condition": {"type": "npc_state", "npc": "obj_cockpit_door", "state": "open"}, # Wenn Tür offen ist (Status check via Object attr müsste man mappen, hier vereinfacht via Event wenn man 'open' nutzt)
        # Besser: Wir prüfen, ob der Spieler den Raum verlassen hat (Location Check)
    },
    {
        "id": "left_cockpit",
        "trigger": "condition",
        "condition": {"type": "location", "value": "ship_corridor"},
        "quest_update": {"id": "q_tutorial", "stage": 2},
        "message": "Der Korridor liegt vor dir.",
        "once": True
    },
    
    # --- ARIS AKTIVIEREN (Crafting Erfolg Trigger) ---
    # Das wird eher über das Crafting-Rezept gelöst, aber wir können auf den State reagieren
    {
        "id": "aris_online",
        "trigger": "condition",
        "condition": {"type": "npc_state", "npc": "ARIS", "state": "online"},
        "quest_update": {"id": "q_tutorial", "stage": 10},
        "description": "ARIS erwacht zum Leben. Blaue Lichter flackern auf.",
        "once": True
    }
]