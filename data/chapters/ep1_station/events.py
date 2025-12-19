# data/chapters/ep1_station/events.py
# Layer 2: Lokale Narrative Matrix

NARRATIVE_MATRIX = [
    # --- Bestehende Events ---
    {
        "id": "evt_meltdown_warning",
        "trigger": "time", "trigger_time": 20,
        "title": "Kritische Temperatur",
        "origin_id": "reactor",
        "description": "Die Warnleuchten im Reaktorraum springen auf Rot. Die Abschirmung singt.",
        "sound_msg": "Ein ansteigendes, hohes Fiepen der Turbinen.",
        "target_obj_id": "core", "penalty": 20,
        "fail_text": "Strahlungslecks in Sektor 4.",
        "success_text": "Die Kühlung stabilisiert sich (vorerst)."
    },
    {
        "id": "evt_val_death",
        "trigger": "relative", "parent_id": "evt_meltdown_warning", "delay": 20,
        "title": "Bio-Monitor Alarm",
        "origin_id": "bridge",
        "description": "Ein flaches Piepen ertönt von der Bio-Monitor-Konsole. Val's Signal ist kritisch.",
        "sound_msg": "Ein durchdringender medizinischer Alarmton.",
        "target_obj_id": "val_body"
    },
    
    # --- NEU: Das Finale (Die Flucht) ---
    {
        "id": "evt_karl_ready",
        "trigger": "condition",
        # Feuert, sobald Aris den Chip installiert hat
        "condition": {"type": "knowledge", "value": "karl_online"},
        "title": "K.A.R.L. Status",
        "origin_id": "hub",
        "description": "K.A.R.L.s Stimme dröhnt durch die Station: 'Antrieb online. Notfall-Startsequenz initiiert. T-Minus 5 Minuten bis Separation. Alle Mann an Bord.'",
        "sound_msg": "Eine synthetische Durchsage hallt durch die Gänge."
    },
    {
        "id": "evt_launch",
        "trigger": "relative", "parent_id": "evt_karl_ready", "delay": 5, # 5 Minuten (Ticks) Zeitfenster
        "title": "Start der Kestrel",
        "origin_id": "ship_cockpit",
        "description": "Die Andockklammern sprengen sich ab. Mit einem gewaltigen Ruck zünden die Triebwerke und das Schiff schießt in den Weltraum.",
        "sound_msg": "Das ohrenbetäubende Grollen startender Triebwerke.",
        # Anmerkung: Wenn der Spieler hier nicht im 'ship_cockpit' ist, hat er den Flug verpasst.
    },
    {
        "id": "evt_station_destruction",
        "trigger": "relative", "parent_id": "evt_launch", "delay": 5, # 5 Minuten nach Start
        "title": "Ereignishorizont",
        "origin_id": "reactor",
        "description": "Die Station gibt den Gravitationskräften nach und implodiert. Alles wird schwarz.",
        "sound_msg": "Ein knirschendes Bersten von Metall.",
        "target_obj_id": "core", 
        "penalty": 1000, # Tötet jeden, der noch auf der Station ist (Game Over)
        "fail_text": "Signal verloren."
    }
]
