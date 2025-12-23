# data/chapters/ep1_station/rooms.py
# Layer 2: Lokale Räume für Episode 1

ROOMS = {
    "hub": {
        "id": "hub", 
        "name": "Zentraler Hub", 
        "map_x": 0, "map_y": 0,
        "desc": "Das Herz der Station. Rotes Notlicht pulsiert. Ein großes {terminal} dominiert die Mitte. K.A.R.L.s Hologramm flackert und wirft verzerrte Schatten.",
        "exits": {"north": "bridge", "east": "reactor", "south": "cantina", "west": "medbay"},
        "img": "scifi_hub"
    },
    "bridge": {
        "id": "bridge", "name": "Kommandobrücke", "map_x": 0, "map_y": -1,
        "desc": "Funken sprühen aus den zerstörten Konsolen. Der Blick durch das Sichtfenster zeigt den Ereignishorizont des Schwarzen Lochs - ein Wirbel aus Licht und Dunkelheit. Der {chair} des Commanders ist umgestürzt.",
        "exits": {"south": "hub"},
        "img": "scifi_bridge"
    },
    "cantina": {
        "id": "cantina", "name": "Messe", "map_x": 0, "map_y": 1,
        "desc": "Es riecht nach Ozon und verbranntem Plastik. Tische sind umgeworfen. Ein {replicator} an der Wand raucht vor sich hin.",
        "exits": {"north": "hub"},
        "img": "scifi_mess"
    },
    "reactor": {
        "id": "reactor", "name": "Reaktorkern", "map_x": 1, "map_y": 0,
        "desc": "Eine Wand aus Hitze schlägt dir entgegen. Der {core} pulsiert in einem ungesunden Violett. Warnsirenen heulen.",
        "exits": {"west": "hub", "down": "maintenance"},
        "img": "scifi_reactor"
    },
    "maintenance": {
        "id": "maintenance", "name": "Wartungstunnel", "map_x": 1, "map_y": 1,
        "tags": ["common_dock"],
        "desc": "Eng, laut und voller Dampf. Hier ist ein {vent}, der aggressiv zischt. Am Boden liegt verbogenes {scrap_metal}. Rostige Rohre führen zu einer massiven Schott-Tür im Osten, der {airlock_control}.",
        "exits": {"up": "reactor"},
        "img": "scifi_tunnel"
    },
    "medbay": {
        "id": "medbay", "name": "Krankenstation", "map_x": -1, "map_y": 0,
        "desc": "Verwüstet. Glasscherben bedecken den Boden. Ein leerer {med_cabinet} steht offen. Es riecht steril und nach Eisen.",
        "exits": {"east": "hub"},
        "img": "scifi_medbay"
    }
}
