NARRATIVE_MATRIX = [
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
        "title": "Lebenszeichen Erloschen",
        "origin_id": "bridge",
        "description": "Ein flaches Piepen ertönt von der Bio-Monitor-Konsole. Commander Val regt sich nicht mehr.",
        "sound_msg": "Ein durchdringender medizinischer Alarmton.",
        "target_obj_id": "val_body"
    }
]