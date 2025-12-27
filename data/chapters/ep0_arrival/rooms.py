# data/chapters/ep0_arrival/rooms.py
# Layer 2: Lokale Räume für Episode 0 (Intakt)

ROOMS = {
    "hub": {
        "id": "hub", "name": "Zentraler Hub", "map_x": 0, "map_y": 0,
        "desc": "Der Hauptbereich der Station. Hell erleuchtet, sauber und geschäftig. Das {terminal} zeigt normale Betriebsdaten. K.A.R.L.s Hologramm leuchtet ruhig blau und begrüßt Vorbeigehende.",
        "exits": {"north": "bridge", "east": "reactor", "south": "cantina", "west": "medbay"},
        "img": "scifi_hub_clean" 
    },
    "bridge": {
        "id": "bridge", "name": "Kommandobrücke", "map_x": 0, "map_y": -1,
        # Val ist ein NPC, sie sollte NICHT in der statischen Beschreibung stehen, 
        # es sei denn, sie bewegt sich nie (was in Ep0 'relaxed' aber möglich ist).
        # Besser: Wir entfernen sie hier auch, damit es konsistent ist.
        "desc": "Der Blick durch das Sichtfenster zeigt die Sterne. Alle Konsolen blinken in beruhigendem Grün.",
        "exits": {"south": "hub"},
        "img": "scifi_bridge_clean"
    },
    "cantina": {
        "id": "cantina", "name": "Messe", "map_x": 0, "map_y": 1,
        "desc": "Es ist warm hier und duftet nach Kaffee und Synthetik-Essen. Tische laden zum Verweilen ein. Der {replicator} an der Wand ist betriebsbereit.",
        "exits": {"north": "hub"},
        "img": "scifi_mess_clean" 
    },
    "reactor": {
        "id": "reactor", "name": "Reaktorkern", "map_x": 1, "map_y": 0,
        # FIX: Aris entfernt. Er ist ein dynamischer NPC.
        "desc": "Ein sanftes, rhythmisches Wummern erfüllt den Raum. Der {core} arbeitet präzise. Es ist warm, aber nicht unangenehm.",
        "exits": {"west": "hub", "down": "maintenance"},
        "img": "scifi_reactor_clean" 
    },
    "maintenance": {
        "id": "maintenance", "name": "Wartungstunnel", "map_x": 1, "map_y": 1,
        "tags": ["common_dock"], 
        "desc": "Selbst hier ist es erstaunlich aufgeräumt. Werkzeuge hängen an den Wänden. Die Luftschleuse zur Kestrel ist fest verriegelt.",
        "exits": {"up": "reactor"},
        "img": "scifi_tunnel_clean" 
    },
    "medbay": {
        "id": "medbay", "name": "Krankenstation", "map_x": -1, "map_y": 0,
        # Fiona ist auch ein NPC. Raus damit aus der Static Desc.
        "desc": "Steril und weiß. Auf dem {med_table} stehen diverse Instrumente und eine {scale}. Pflanzenproben stehen in den Regalen.",
        "exits": {"east": "hub"},
        "img": "scifi_medbay_clean" 
    }
}