MATRIX = [
    # --- START ---
    {
        "id": "start_game",
        "trigger": "time",
        "trigger_time": 0,
        "title": "Kapitel 0: Ankunft",
        "description": "Erwachen. Schmerz. Du liegst auf dem Boden des Cockpits.",
        "quest_start": "q_main", # Quest Start
        "sound_msg": "Ein tiefes Ächzen von Metall."
    },
    
    # --- TRIGGER: COCKPIT VERLASSEN ---
    {
        "id": "left_cockpit",
        "trigger": "condition",
        "condition": {"type": "location", "value": "ship_corridor"},
        "quest_update": {"id": "q_main", "stage": 2},
        "description": "Der Korridor ist ein Bild der Zerstörung. Irgendetwas hat dieses Schiff schwer getroffen.",
        "once": True
    },

    # --- TRIGGER: ARIS GEFUNDEN ---
    {
        "id": "found_aris",
        "trigger": "condition",
        "condition": {"type": "location", "value": "ship_workshop"},
        "quest_update": {"id": "q_main", "stage": 3},
        "once": True
    },

    # --- TRIGGER: ARIS ONLINE (wird durch Crafting ausgelöst) ---
    {
        "id": "aris_online",
        "trigger": "manual", # Wird manuell vom Crafting getriggert
        "quest_update": {"id": "q_main", "stage": 4},
        "description": "ARIS' Kopf ruckt nach oben. Seine Optiken fokussieren dich mit beunruhigender Präzision.",
        "effects": [
            # WICHTIG: Hier setzen wir den State explizit über das Event-System
            {"type": "set_npc_state", "npc": "npc_aris", "value": "online"},
            {"type": "set_npc_state", "npc": "ARIS", "value": "online"} # Fallback für Namens-Suche
        ],
        "once": True
    },

    # --- TRIGGER: TÜR UNTERSUCHT ---
    {
        "id": "see_bio_door",
        "trigger": "condition",
        "condition": {"type": "location", "value": "ship_corridor"},
        "effects": [{"type": "learn", "fact": "knows_bio_lock"}],
        "once": True
    },

    # --- TRIGGER: TÜR ÖFFNEN (durch ARIS Dialog) ---
    {
        "id": "unlock_bio_door",
        "trigger": "manual", 
        "description": "ARIS tippt etwas auf seinem internen Interface. Die Bio-Schleuse piept bestätigend und entriegelt sich mit einem schweren Zischen.",
        "effects": [
            {
                "type": "update_object",
                "target": "obj_bio_door",
                "updates": {"is_locked": False, "is_open": True, "desc": "Die Schleuse steht offen. Dahinter liegt Dunkelheit."}
            }
        ]
    },
    
    # --- SCHACHT SEQUENZ ---
    {
        "id": "start_shaft_sequence",
        "trigger": "manual", 
        "description": "ARIS tritt das Lüftungsgitter ein. 'Nach dir', sagt er zynisch. 'Ich muss meine Navigationsdaten kalibrieren.'",
        "effects": [
            {"type": "move_npc", "npc": "npc_aris", "room": "maint_shaft_1"}
        ]
    },
    
    {
        "id": "aris_leaves_junction",
        "trigger": "condition",
        "condition": {"type": "location", "value": "maint_junction"},
        "description": "'Das hier steht auf keinem Plan', murmelt ARIS. 'Bleib hier. Rühr nichts an. Atme flach.' Er verschwindet im rechten Tunnel (Schacht B).",
        "effects": [
            {"type": "move_npc", "npc": "npc_aris", "room": "maint_shaft_2"}, 
            {"type": "trigger_event", "id": "start_waiting_timer"} 
        ],
        "once": True
    },
    
    {
        "id": "wait_1",
        "trigger": "relative",
        "parent_id": "aris_leaves_junction",
        "delay": 15,
        "description": "Die Kälte kriecht dir in die Knochen. Von ARIS keine Spur. Dein Magen knurrt.",
        "sound_msg": "Tropfen. Tropfen. Tropfen."
    },
    {
        "id": "wait_2",
        "trigger": "relative",
        "parent_id": "aris_leaves_junction",
        "delay": 45,
        "description": "Du zitterst am ganzen Körper. War das ein Geräusch? Nein, nur das Setzen des Metalls. Er kommt nicht zurück.",
        "sound_msg": "Metallisches Knacken."
    },
    
    {
        "id": "aris_returns",
        "trigger": "relative",
        "parent_id": "aris_leaves_junction",
        "delay": 60, 
        "title": "Rückkehr",
        "description": "Licht flackert im rechten Tunnel auf. ARIS kriecht rückwärts heraus. 'Der Weg ist blockiert. Aber ich habe die Luke gehackt. Wir können weiter.'",
        "effects": [
            {"type": "move_npc", "npc": "npc_aris", "room": "maint_junction"},
            {"type": "update_object", "target": "obj_maintenance_hatch", "updates": {"is_locked": False, "is_open": True, "desc": "Die Luke steht offen."}}
        ]
    },

    # --- ENDE ---
    {
        "id": "enter_quarters",
        "trigger": "condition",
        "condition": {"type": "location", "value": "crew_quarters"},
        "quest_update": {"id": "q_main", "stage": 10},
        "title": "Kapitel abgeschlossen",
        "description": "Du betrittst den Vorraum der Mannschaftsquartiere. Es ist still. Zu still.",
        "once": True
    }
]