# data/chapters/ep1_station/rooms.py
# Layer 2: Lokale Räume für Episode 1

ROOMS = {
    "hub": {
        "id": "hub", 
        "name": "Zentraler Hub", 
        "map_x": 0, "map_y": 0,
        # TAG ENTFERNT: Der Hub ist zu voll
        "desc": "Das Herz der Station. Ein großes {terminal} dominiert die Mitte. K.A.R.L.s Hologramm flackert.",
        "exits": {"north": "bridge", "east": "reactor", "south": "cantina", "west": "medbay"},
        "img": "scifi_hub"
    },
    "bridge": {
        "id": "bridge", "name": "Kommandobrücke", "map_x": 0, "map_y": -1,
        "desc": "Funken sprühen aus den Konsolen. Der {chair} des Commanders ist umgestürzt.",
        "exits": {"south": "hub"},
        "img": "scifi_bridge"
    },
    "cantina": {
        "id": "cantina", "name": "Messe", "map_x": 0, "map_y": 1,
        "desc": "Es riecht nach Ozon. Ein {replicator} an der Wand raucht.",
        "exits": {"north": "hub"},
        "img": "scifi_mess"
    },
    "reactor": {
        "id": "reactor", "name": "Reaktorkern", "map_x": 1, "map_y": 0,
        "desc": "Tödliche Hitze. Der {core} pulsiert violett.",
        "exits": {"west": "hub", "down": "maintenance"},
        "img": "scifi_reactor"
    },
    "maintenance": {
        "id": "maintenance", "name": "Wartungstunnel", "map_x": 1, "map_y": 1,
        "tags": ["common_dock"], # NEU: Hier ist jetzt das Dock
        "desc": "Eng und laut. Hier ist ein {vent}, der zischt. Rostige Rohre führen zu einer massiven Schott-Tür im Osten.",
        "exits": {"up": "reactor"},
        "img": "scifi_tunnel"
    },
    "medbay": {
        "id": "medbay", "name": "Krankenstation", "map_x": -1, "map_y": 0,
        "desc": "Verwüstet. Ein leerer {med_cabinet} steht offen.",
        "exits": {"east": "hub"},
        "img": "scifi_medbay"
    }
}