# data/chapters/ep0_arrival/events.py

NARRATIVE_MATRIX = [
    # --- 1. START (Tick 0) ---
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
            {"type": "set_npc_state", "npc": "Aris", "value": "dinner"}, # NEU: Aris geht auch essen
            {"type": "set_npc_state", "npc": "Val", "value": "dinner"}   # NEU: Val auch
        ]
    },
    
    # --- 3. BETTRUHE (Tick 60-100) ---
    {
        "id": "evt_night_mode",
        "trigger": "time", "trigger_time": 60,
        "title": "Nachtzyklus",
        "origin_id": "hub",
        "description": "Die Hauptbeleuchtung wird gedimmt. Die Station geht in den Nachtmodus. Du gähnst. Zeit fürs Bett in der Kestrel.",
        "sound_msg": "Lüfter fahren herunter.",
        "effects": [
            {"type": "set_npc_state", "npc": "Fiona", "value": "night_conspiracy"}, # Fiona schleicht weg
            {"type": "set_npc_state", "npc": "Aris", "value": "sleeping"},
            {"type": "set_npc_state", "npc": "Val", "value": "sleeping"}
        ]
    },
    
    # --- 4. DAS ERWACHEN (Bedingt oder Zeit) ---
    {
        "id": "evt_wakeup_noise_bed",
        # Variante A: Spieler ist brav im Bett
        "trigger": "condition", 
        "condition": {"type": "location", "value": "ship_quarters"},
        "title": "Störung",
        "origin_id": "ship_quarters", 
        "description": "Ein metallisches Schaben reißt dich aus dem Schlaf. Es kommt aus dem Wartungstunnel direkt unter dem Dock.",
        "sound_msg": "Klong. Klong.",
        # Blockiert Trigger B
        "effects": [{"type": "learn", "fact": "woke_up_in_bed"}]
    },
    {
        "id": "evt_wakeup_forced",
        # Variante B: Spieler trödelt -> Zwangsschlaf bei Tick 100
        "trigger": "time", "trigger_time": 100,
        "title": "Erschöpfung",
        "description": "Du bist vor Erschöpfung eingeschlafen... und schreckst hoch.",
        "sound_msg": "Klong. Klong.",
        "condition": {"type": "knowledge", "negate": True, "value": "woke_up_in_bed"} # Nur wenn A nicht passiert ist (Logic TODO: Negate support)
        # Da wir negate nicht haben, lassen wir es parallel laufen oder setzen trigger_time hoch.
    },
    
    # --- 5. KONFRONTATION (Relativ zu Erwachen) ---
    {
        "id": "evt_conspiracy",
        # Passiert kurz nach dem Aufwachen (wir nehmen A als Anchor, da B spät ist)
        "trigger": "relative", "parent_id": "evt_wakeup_noise_bed", "delay": 5,
        "type": "conversation",
        "origin_id": "maintenance", 
        "actors": ["Fiona", "Unbekannt"],
        "content": [
            {"speaker": "Fiona", "text": "Ich habe die Proben. Aber das war so nicht abgemacht!"},
            {"speaker": "Unbekannt", "text": "Der Zeitplan wurde geändert. Gib mir den Behälter."},
            {"speaker": "Fiona", "text": "Nein! Das destabilisiert den Kern! Sie werden alle sterben!"},
            {"speaker": "Unbekannt", "text": "Das ist einkalkuliert. Gib es her."},
            {"speaker": "Fiona", "text": "Hilfe! Aris! Irgendjem... (Geräusch eines Kampfes)"}
        ],
        "sound_msg": "Gedämpfte Stimmen und Schritte."
    },
    
    # --- 6. FINALE (Relativ zu Konfrontation) ---
    {
        "id": "evt_explosion",
        "trigger": "relative", "parent_id": "evt_conspiracy", "delay": 5,
        "title": "KATASTROPHE",
        "origin_id": "reactor",
        "description": "Ein gewaltiger Knall erschüttert das Schiff! Alarm-Sirenen heulen los. Die Station kippt seitlich weg. Alles wird schwarz.",
        "sound_msg": "EXPLOSION!",
        "type": "chapter_switch",
        "target_chapter": "ep1_station"
    }
]