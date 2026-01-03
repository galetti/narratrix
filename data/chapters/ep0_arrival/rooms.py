from engine.constants import *

ROOMS = {
    "ship_cockpit": {
        "name": "Cockpit der Kestrel",
        "desc": "Rauch hängt in der Luft. Die Konsolen sind dunkel, bis auf ein schwaches Flackern der Notbeleuchtung. Durch die gesplitterte Frontscheibe siehst du nur Schwärze.",
        "exits": {
            "out": "ship_corridor" # Tür ist aber verschlossen (siehe items)
        },
        "tags": ["start"],
        "img": "cockpit_ruined"
    },
    "ship_corridor": {
        "name": "Korridor",
        "desc": "Ein enger Gang. Kabel hängen von der Decke. Der Boden ist mit Trümmern bedeckt.",
        "exits": {
            "in": "ship_cockpit",
            "north": "ship_workshop"
        },
        "img": "corridor_dark"
    },
    "ship_workshop": {
        "name": "Werkstatt",
        "desc": "Hier wurde früher repariert. Jetzt herrscht Chaos. Eine Werkbank steht an der Wand, halb begraben unter Ersatzteilen.",
        "exits": {
            "south": "ship_corridor"
        },
        "img": "workshop"
    }
}