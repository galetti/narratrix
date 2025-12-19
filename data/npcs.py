NPCS = [
    # --- 1. CHIEF ARIS (Kantine) ---
    {
        "name": "Aris", "aliases": ["chief", "aris", "ingenieur"], 
        "start_loc": "cantina", "location": "cantina", 
        "movement_chance": 40, # Sehr aktiv (Panik)
        "affinity": [
            "cantina", 
            "reactor",
            {"target": "reactor", "priority": 10, "condition": {"type": "event_triggered", "id": "evt_meltdown_warning"}}
        ],
        "state": "panic", "img": "face_aris_tired", "personality": "Gestresst",
        "desc": "Er zittert am ganzen Leib.",
        "dialogue": {
            "panic": {
                "greeting": "Verdammt! Ich brauche einen Stim!",
                "stim": {"text": "Misch Pulver und Wasser! Schnell!"},
                "kaffee": {
                    "condition": {"type": "knowledge", "value": "received_stim_caf"},
                    "text": "Ahhh... danke. Mein Kopf wird klar.",
                    "effect": {"type": "set_state", "value": "focused"}
                }
            },
            "focused": {
                "movement_chance": 20, # Normaler Wert, wenn er beruhigt ist
                "desc": "Er wirkt ruhig und kompetent.",
                "img": "face_aris_alert", "personality": "Kompetent",
                "greeting": "Okay, Situation: Der Reaktor schmilzt, und wir brauchen den Root-Chip von Val.",
                "reaktor": "Kühlmittel reicht nicht. Wir brauchen den System-Override.",
                "chip": {
                     "condition": {"type": "knowledge", "value": "received_access_chip"},
                     "text": "Du hast ihn! Ausgezeichnet. Ich renne zum Hub und installiere ihn sofort!",
                     "effect": [
                         {"type": "move_npc", "target": "hub"},    
                         {"type": "learn", "fact": "karl_online"}, 
                         {"type": "set_state", "value": "hacking"},
                         {"type": "set_npc_state", "npc": "K.A.R.L.", "value": "online"}
                     ]
                }
            },
            "hacking": {
                "movement_chance": 0, # Er arbeitet am Terminal, er rennt nicht weg
                "desc": "Er tippt wild auf dem Terminal herum.",
                "img": "face_aris_alert",
                "greeting": "Nicht jetzt! Ich muss K.A.R.L. neu starten. Sprich mit der KI!",
                "default": "Keine Zeit!"
            }
        }
    },
    # --- 2. COMMANDER VAL (Brücke) ---
    {
        "name": "Val", "aliases": ["commander", "frau"], 
        "start_loc": "bridge", "location": "bridge", "affinity": ["bridge"],
        "movement_chance": 10, # Bewegt sich generell wenig
        "state": "injured", "img": "face_val_pain", "personality": "Schmerzerfüllt, Autoritär",
        "desc": "Sie hält sich die Seite. Blut sickert durch ihre Uniform.",
        "dialogue": {
            "injured": {
                "movement_chance": 0, # Kann nicht laufen
                "greeting": "Hrrgh... Bericht...",
                "medikit": {
                    "condition": {"type": "knowledge", "value": "received_medikit"},
                    "text": "Das... hilft. Danke, Crewman.",
                    "effect": {"type": "set_state", "value": "command"}
                }
            },
            "command": {
                # Erbt 10% movement_chance von oben (bleibt meist auf der Brücke)
                "desc": "Sie stützt sich auf die Konsole, wirkt aber gefasst.",
                "img": "face_val_stern", "personality": "Befehlshaber",
                "greeting": "Gute Arbeit. Wir retten dieses Schiff.",
                "chip": {
                    "text": "Hier. Bringen Sie das zu Aris oder setzen Sie es selbst im Hub ein.",
                    "effect": {"type": "receive_item", "item_id": "access_chip"} 
                }
            }
        }
    },
    # --- 3. K.A.R.L. (Hub) ---
    {
        "name": "K.A.R.L.", "aliases": ["ki", "hologramm", "karl"], 
        "start_loc": "hub", "location": "hub", "affinity": ["hub"],
        "movement_chance": 0, # Hologramm bewegt sich nicht physisch
        "state": "offline", "img": "face_ai_glitch", "personality": "Zynisch, Roboter",
        "desc": "Das Hologramm flackert rot und verzerrt.",
        "dialogue": {
            "offline": {
                "greeting": "S-S-Systemfehler. Bitte Root-Chip einlegen."
            },
            "online": {
                "desc": "Das Hologramm leuchtet ruhig blau.",
                "img": "face_ai_calm", "personality": "Hilfsbereit, sarkastisch",
                "greeting": "Willkommen zurück, Crewman. Aris arbeitet an der Stabilisierung."
            }
        }
    }
]
