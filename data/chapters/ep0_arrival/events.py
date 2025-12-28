# data/chapters/ep0_arrival/events.py

NARRATIVE_MATRIX = [
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
    {
        "id": "evt_dinner_call",
        "trigger": "time", "trigger_time": 30,
        "title": "Durchsage",
        "origin_id": "hub",
        "description": "K.A.R.L.s Stimme erklingt sanft: 'Achtung Crew, das Abendessen wird in der Messe serviert. Heute: Curry.'",
        "sound_msg": "Ein angenehmer Gong.",
        "effects": [
            {"type": "set_npc_state", "npc": "Fiona", "value": "dinner"}
        ]
    },
    {
        "id": "evt_dinner_move",
        "trigger": "relative", "parent_id": "evt_dinner_call", "delay": 1,
        "title": "Versammlung",
        "description": "Die Gänge füllen sich mit Leben. Alle gehen zur Kantine.",
    },
    {
        "id": "evt_sleep",
        "trigger": "time", "trigger_time": 60,
        "title": "Müdigkeit",
        "description": "Es war ein langer Tag. Du solltest zurück auf dein Schiff gehen und schlafen. (Gehe ins Bett / Kestrel Quartier)",
        "sound_msg": "Das Licht wird automatisch gedimmt."
    },
    {
        "id": "evt_explosion",
        "trigger": "relative", "parent_id": "evt_sleep", "delay": 15,
        "title": "KATASTROPHE",
        "origin_id": "ship_quarters",
        "description": "Ein gewaltiger, ohrenbetäubender Knall reißt dich aus dem Schlaf! Alarm-Sirenen heulen los. Die Station bebt heftig.",
        "sound_msg": "EXPLOSION!",
        "type": "chapter_switch",
        "target_chapter": "ep1_station"
    }
]