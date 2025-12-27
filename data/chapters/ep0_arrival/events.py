# Ep0 Events steuern den Tagesablauf und den Übergang.

NARRATIVE_MATRIX = [
    # --- SETUP EVENTS (Sofort beim Start) ---
    {
        "id": "evt_setup_crew",
        "trigger": "time", "trigger_time": 0, # Sofort
        "title": "Ankunft",
        "origin_id": "ship_cockpit",
        "description": "Die Kestrel ist sicher angedockt. Zeit, die Crew zu begrüßen.",
        "sound_msg": "Das sanfte Summen der Station.",
        # Hier nutzen wir den Effekt, um die Zustände der Global NPCs zu ändern!
        # Wir brauchen einen Mechanismus, um NPC States per Event zu setzen.
        # Da wir das noch nicht haben (nur in Dialogen), fügen wir es dem GameState Tick hinzu?
        # Nein, wir tricksen: Wir nutzen ein 'system' Event oder wir erweitern NPCs in Common um den State 'relaxed'.
    },
    
    # --- ABENDESSEN (Zeitgesteuert) ---
    {
        "id": "evt_dinner_call",
        "trigger": "time", "trigger_time": 30,
        "title": "Durchsage",
        "origin_id": "hub",
        "description": "K.A.R.L.: 'Achtung Crew, das Abendessen wird in der Messe serviert.'",
        "sound_msg": "Ein Gong."
    },
    {
        "id": "evt_dinner_move",
        "trigger": "relative", "parent_id": "evt_dinner_call", "delay": 1,
        "title": "Versammlung",
        # Hier bewegen wir alle NPCs in die Kantine (Dummy Event für Story)
        "description": "Die Gänge füllen sich mit Leben.",
        # In einer echten Engine würden wir hier AI-Ziele setzen.
    },
    
    # --- DAS ENDE DES KAPITELS ---
    {
        "id": "evt_sleep",
        "trigger": "time", "trigger_time": 60,
        "title": "Schlafenszeit",
        "description": "Es war ein langer Tag. Du gehst zurück in dein Quartier auf der Kestrel.",
        "sound_msg": "Das Licht wird gedimmt."
    },
    {
        "id": "evt_explosion",
        "trigger": "relative", "parent_id": "evt_sleep", "delay": 10,
        "title": "KATASTROPHE",
        "origin_id": "ship_quarters",
        "description": "Ein gewaltiger Knall reißt dich aus dem Schlaf! Alarm-Sirenen heulen. Die Station bebt.",
        "sound_msg": "EXPLOSION!",
        
        # DER WECHSEL
        "type": "chapter_switch",
        "target_chapter": "ep1_station"
    }
]