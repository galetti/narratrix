# data/chapters/ep0_arrival/quests.py

QUESTS = {
    "q_main_survival": {
        "title": "Überleben",
        "description": "Du bist in einem Wrack aufgewacht. Finde heraus, wo du bist und sorge für dein Überleben.",
        "stages": {
            "1": "Verschaffe dir einen Überblick. Schau dich um.",
            "2": "Verlasse das Cockpit.",
            "3": "Untersuche die Docking-Station nach Vorräten oder Informationen.",
            "10": "Aufgabe abgeschlossen: Du hast die Station betreten."
        }
    },
    "q_side_fix_comms": {
        "title": "Kommunikation wiederherstellen",
        "description": "Die Funkkonsole sprüht Funken. Vielleicht lässt sie sich reparieren.",
        "stages": {
            "1": "Untersuche die Funkkonsole genauer.",
            "2": "Finde Werkzeug, um die Konsole zu öffnen.",
            "3": "Repariere die Schaltkreise.",
            "10": "Aufgabe erledigt: Die Konsole empfängt wieder Signale."
        }
    }
}