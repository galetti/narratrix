# data/common/rooms.py
# Layer 1: Räume, die immer existieren (z.B. das Spielerschiff "Kestrel")

COMMON_ROOMS = {
    "ship_cockpit": {
        "id": "ship_cockpit", "name": "Kestrel: Cockpit", "map_x": 0, "map_y": 0,
        "desc": "Dein Schiff. Klein, aber schnell. Durch das Fenster siehst du Sterne.",
        "exits": {"south": "ship_quarters", "out": "hub"}, # 'out' wird im Merge evtl. überschrieben oder verlinkt
        "img": "ship_cockpit_default" # Platzhalter
    },
    "ship_quarters": {
        "id": "ship_quarters", "name": "Kestrel: Quartier", "map_x": 0, "map_y": 1,
        "desc": "Ein Bett, ein Spind, ein Tisch. Dein Zuhause.",
        "exits": {"north": "ship_cockpit"},
        "img": "ship_quarters_default"
    }
}
