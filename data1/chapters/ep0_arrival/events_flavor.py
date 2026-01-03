# data/chapters/ep1_station/events_flavor.py
# Atmosphärische Events für Episode 1

FLAVOR_MATRIX = [
    {
        "id": "amb_creak",
        "trigger": "time", "trigger_time": 15,
        "title": "Strukturelle Belastung",
        "origin_id": "hub",
        "description": "Ein tiefes Ächzen geht durch das Metall der Station, als ob ein riesiges Tier atmen würde.",
        "sound_msg": "Ein metallisches Knarren."
    },
    {
        "id": "amb_flicker",
        "trigger": "time", "trigger_time": 35,
        "title": "Energie-Schwankung",
        "origin_id": "hub",
        "description": "Das Licht flackert kurz und taucht alles in Dunkelheit, bevor die Notbeleuchtung wieder anspringt.",
        "sound_msg": "Ein elektrisches Summen."
    },
    {
        "id": "amb_quake",
        "trigger": "time", "trigger_time": 60,
        "title": "Gravitations-Welle",
        "origin_id": "reactor",
        "description": "Der Boden bebt heftig unter deinen Füßen. Tassen fallen von Tischen.",
        "sound_msg": "Ein tiefes Grollen."
    }
]
