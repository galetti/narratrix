# data/common/npcs.py
# Layer 1: Die permanente Crew (Aris & K.A.R.L.)
# Val wurde entfernt, da sie nun handlungsspezifisch für Episode 1 ist.

COMMON_NPCS = [
    {
        "id": "npc_aris", "name": "Aris", "aliases": ["chief", "aris"], "is_global": True,
        "start_loc": "cantina", "location": "cantina", 
        "movement_chance": 40, "affinity": ["cantina", "reactor"],
        "state": "panic", "img": "face_aris_tired", "personality": "Gestresst", "desc": "Er zittert.",
        "dialogue": {
            "panic": {
                "greeting": "Verdammt! Ich brauche einen Stim!",
                "stim": {"text": "Misch Pulver und Wasser!"},
                "kaffee": {"condition": {"type": "knowledge", "value": "received_stim_caf"}, "text": "Danke.", "effect": {"type": "set_state", "value": "focused"}}
            },
            "focused": {
                "movement_chance": 20, "img": "face_aris_alert", "greeting": "Wir müssen das Schiff retten.",
                "chip": {"condition": {"type": "knowledge", "value": "received_access_chip"}, "text": "Ich starte K.A.R.L. neu!", "effect": [{"type": "move_npc", "target": "hub"}, {"type": "set_state", "value": "hacking"}, {"type": "set_npc_state", "npc": "K.A.R.L.", "value": "online"}]}
            },
            "hacking": {"movement_chance": 0, "greeting": "Nicht jetzt!", "default": "Keine Zeit!"}
        }
    },
    {
        "id": "npc_karl", "name": "K.A.R.L.", "aliases": ["ki"], "is_global": True,
        "start_loc": "hub", "location": "hub", "affinity": ["hub"], "movement_chance": 0,
        "state": "offline", "img": "face_ai_glitch", "personality": "Roboter", "desc": "Flackert.",
        "dialogue": {
            "offline": {"greeting": "Systemfehler."},
            "online": {"img": "face_ai_calm", "greeting": "Systeme online. Kestrel ist startklar. Wir warten auf Ihren Befehl."}
        }
    }
]
