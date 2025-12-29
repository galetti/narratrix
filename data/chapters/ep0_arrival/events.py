# data/chapters/ep0_arrival/events.py

NARRATIVE_MATRIX = [
    # --- 1. SETUP (Tick 0) ---
    {
        "id": "evt_ep0_init",
        "trigger": "time", "trigger_time": 0,
        "title": "Ankunft",
        "origin_id": "ship_cockpit",
        "description": "Die Kestrel ist sicher angedockt. Du nimmst deinen Rucksack. Zeit, die Crew zu begrüßen und dich auf der Station zu melden.",
        "sound_msg": "Das sanfte Summen der Station.",
        "effects": [
            {"type": "set_npc_state", "npc": "Aris", "value": "relaxed"},
            {"type": "set_npc_state", "npc": "Val", "value": "relaxed"},
            {"type": "set_npc_state", "npc": "K.A.R.L.", "value": "service"}
        ]
    },
    
    # --- 2. ABENDESSEN (Tick 30) ---
    {
        "id": "evt_dinner_call",
        "trigger": "time", "trigger_time": 30,
        "title": "Durchsage",
        "origin_id": "hub",
        "description": "K.A.R.L.s Stimme erklingt sanft: 'Achtung Crew, das Abendessen wird in der Messe serviert. Heute: Curry.'",
        "sound_msg": "Ein angenehmer Gong.",
        "effects": [
            {"type": "set_npc_state", "npc": "Fiona", "value": "dinner"},
            # Aris und Val gehen per Affinity zur Kantine, da 'relaxed' Cantina als Affinity hat
        ]
    },
    
    # --- 3. DIE NACHT (Tick 60) ---
    {
        "id": "evt_night_mode",
        "trigger": "time", "trigger_time": 60,
        "title": "Nachtzyklus",
        "origin_id": "hub",
        "description": "Die Hauptbeleuchtung wird gedimmt. Die Station geht in den Nachtmodus. Du solltest dich aufs Ohr hauen (gehe ins Bett / Kestrel Quartier).",
        "sound_msg": "Lüfter fahren herunter.",
        "effects": [
            # Aris und Val gehen in die Quartiere schlafen
            {"type": "set_npc_state", "npc": "Aris", "value": "sleeping"},
            {"type": "set_npc_state", "npc": "Val", "value": "sleeping"},
            
            # Fiona schleicht sich weg (Conspiracy)
            {"type": "set_npc_state", "npc": "Fiona", "value": "night_conspiracy"} 
        ]
    },
    
    # --- 4. DAS ERWACHEN (Tick 80) ---
    {
        "id": "evt_wakeup_noise",
        "trigger": "time", "trigger_time": 80,
        "title": "Störung",
        "origin_id": "ship_quarters", 
        "description": "Ein metallisches Schaben reißt dich aus dem Halbschlaf. Es kommt von draußen, aus dem Wartungstunnel.",
        "sound_msg": "Klong. Klong.",
    },
    
    # --- 5. DIE VERSCHWÖRUNG (Tick 85) ---
    {
        "id": "evt_conspiracy",
        "trigger": "time", "trigger_time": 85,
        "type": "conversation",
        "origin_id": "maintenance", 
        "actors": ["Fiona", "Unbekannt"],
        "content": [
            {"speaker": "Fiona", "text": "Ich habe die Proben. Aber das war so nicht abgemacht!"},
            {"speaker": "Unbekannt", "text": "Der Zeitplan wurde geändert. Gib mir den Behälter."},
            {"speaker": "Fiona", "text": "Nein! Das destabilisiert den Kern! Sie werden alle sterben!"},
            {"speaker": "Unbekannt", "text": "Das ist einkalkuliert. Gib es her, oder ich hole es mir."},
            {"speaker": "Fiona", "text": "Hilfe! Aris! Irgendjem... (Geräusch eines Kampfes)"}
        ],
        "sound_msg": "Gedämpfte Stimmen und Schritte."
    },
    
    # --- 6. KATASTROPHE (Tick 100) ---
    {
        "id": "evt_explosion",
        "trigger": "time", "trigger_time": 100,
        "title": "KATASTROPHE",
        "origin_id": "reactor",
        "description": "Ein gewaltiger Knall erschüttert das Schiff! Alarm-Sirenen heulen los. Die Station kippt seitlich weg.",
        "sound_msg": "EXPLOSION!",
        "effects": [
            # Eventuell Flags setzen oder Inventar bereinigen wenn nötig
        ],
        "type": "chapter_switch",
        "target_chapter": "ep1_station"
    }
]