# data/common/npcs.py
# Layer 1: Die permanente Crew (Aris & K.A.R.L.)

COMMON_NPCS = [
    {
        "id": "npc_aris", 
        "name": "Aris", 
        "aliases": ["chief", "aris"], 
        "is_global": True,
        "start_loc": "cantina", 
        "location": "cantina", 
        
        "initial_state": "panic",
        "states": {
            "panic": {
                "behavior": {
                    "movement_chance": 40, 
                    "affinity": ["cantina", "reactor"],
                    "route": []
                },
                "visuals": {
                    "img": "face_aris_tired", 
                    "desc": "Er zittert.",
                    "personality": "Gestresst"
                },
                "dialogue": {
                    "greeting": "Verdammt! Ich brauche einen Stim!",
                    "stim": {"text": "Misch Pulver und Wasser!"},
                    "kaffee": {"condition": {"type": "knowledge", "value": "received_stim_caf"}, "text": "Danke.", "effect": {"type": "set_state", "value": "focused"}}
                }
            },
            "focused": {
                "behavior": {
                    "movement_chance": 80, 
                    "affinity": ["cantina", "reactor"],
                    "route": ["cantina", "hub", "reactor", "maintenance", "reactor", "hub"], 
                    "route_behavior": "loop"
                },
                "visuals": {
                    "img": "face_aris_alert", 
                    "desc": "Er wirkt ruhig und kompetent.",
                    "personality": "Kompetent"
                },
                "dialogue": {
                    "greeting": "Wir müssen das Schiff retten.",
                    "chip": {"condition": {"type": "knowledge", "value": "received_access_chip"}, "text": "Ich starte K.A.R.L. neu!", "effect": [{"type": "move_npc", "target": "hub"}, {"type": "set_state", "value": "hacking"}, {"type": "set_npc_state", "npc": "K.A.R.L.", "value": "online"}]}
                }
            },
            "hacking": {
                "behavior": {
                    "movement_chance": 0,
                    "affinity": ["hub"],
                    "route": []
                },
                "visuals": {
                    "img": "face_aris_alert",
                    "desc": "Er tippt wild auf dem Terminal herum.",
                    "personality": "Fokussiert"
                },
                "dialogue": {
                    "greeting": "Nicht jetzt!", 
                    "default": "Keine Zeit!"
                }
            }
        }
    },
    {
        "id": "npc_karl", 
        "name": "K.A.R.L.", 
        "aliases": ["ki"], 
        "is_global": True,
        "start_loc": "hub", 
        "location": "hub", 
        
        # Migration auf neue Struktur
        "initial_state": "offline",
        "states": {
            "offline": {
                "behavior": {
                    "movement_chance": 0,
                    "affinity": ["hub"],
                    "route": []
                },
                "visuals": {
                    "img": "face_ai_glitch",
                    "desc": "Das Hologramm flackert rot und verzerrt.",
                    "personality": "Roboter (Defekt)"
                },
                "dialogue": {
                    "greeting": "S-S-Systemfehler. Bitte Root-Chip einlegen."
                }
            },
            "online": {
                "behavior": {
                    "movement_chance": 0, # Als Hologramm stationär
                    "affinity": ["hub"],
                    "route": []
                },
                "visuals": {
                    "img": "face_ai_calm",
                    "desc": "Das Hologramm leuchtet ruhig blau.",
                    "personality": "Hilfsbereit, sarkastisch"
                },
                "dialogue": {
                    "greeting": "Systeme online. Kestrel ist startklar. Wir warten auf Ihren Befehl."
                }
            }
        }
    }
]
