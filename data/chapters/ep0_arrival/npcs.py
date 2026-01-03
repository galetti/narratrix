NPCS = [
    {
        "id": "npc_aris",
        "name": "ARIS",
        "location": "ship_workshop", # Erstmal inaktiv
        "state": "offline",
        "desc": "Eine kastenförmige Drohne. Ihre Linsen sind dunkel.",
        "aliases": ["drohne", "roboter", "bot"],
        "states": {
            "offline": {
                "visuals": {"desc": "Die Drohne rührt sich nicht. Sie braucht wohl Strom."},
                "dialogue": {}
            },
            "online": {
                "visuals": {"desc": "ARIS schwebt leise summend in der Luft."},
                "behavior": {"roam": True}, # Kann herumlaufen
                "dialogue": {
                    "greeting": "Systemstart... Diagnose... Oh. Hallo.",
                    "status": "Meine Sensoren melden kritische Schäden am Schiff.",
                    "schiff": "Dies ist die Kestrel. Oder was davon übrig ist."
                }
            }
        }
    }
]