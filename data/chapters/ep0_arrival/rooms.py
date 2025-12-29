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
        "desc": "Commander Val steht am großen Sichtfenster und betrachtet die Sterne. Alle Konsolen blinken in beruhigendem Grün.",
        "exits": {"south": "hub"},
        "img": "scifi_bridge_clean" 
    },
    "cantina": {
        "id": "cantina", "name": "Messe", "map_x": 0, "map_y": 1,
        "desc": "Es ist warm hier und duftet nach Kaffee und Synthetik-Essen. Tische laden zum Verweilen ein. Der {replicator} an der Wand ist betriebsbereit.",
        "exits": {"north": "hub", "south": "crew_quarters"}, # Ausgang nach Süden hinzugefügt
        "img": "scifi_mess_clean" 
    },
    # NEU: Mannschaftsquartiere
    "crew_quarters": {
        "id": "crew_quarters", 
        "name": "Mannschaftsquartiere", 
        "map_x": 0, "map_y": 2, # Südlich der Kantine (0, 1)
        "desc": "Ein langer Koridor mit persönlichen Schlafkabinen für die Stations-Crew. Es ist ruhig und privat hier. Ein paar persönliche Gegenstände liegen herum.",
        "exits": {"north": "cantina"},
        "img": "scifi_quarters_clean" # 
    },
    "reactor": {
        "id": "reactor", "name": "Reaktorkern", "map_x": 1, "map_y": 0,
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
        "desc": "Steril und weiß. Auf dem {med_table} stehen diverse Instrumente und eine {scale}. Pflanzenproben stehen in den Regalen.",
        "exits": {"east": "hub"},
        "acoustics": {
            "hub": 0.2
        },
        "img": "scifi_medbay_clean" 
    }
}