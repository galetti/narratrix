from engine.constants import *

ROOMS = {
    "ship_cockpit": {
        "name": "Cockpit",
        "desc": "Rauchschwaden ziehen träge durch die enge Kabine. Die Frontscheibe ist ein Netz aus Rissen. Nur das Notlicht taucht alles in ein pulsierendes Rot.",
        "exits": {
            "east": "ship_corridor"  # Statt "out"
        },
        "tags": ["start"],
        "img": "cockpit_ruined"
    },
    "ship_corridor": {
        "name": "Korridor",
        "desc": "Ein schmaler Verbindungsgang. Funken regnen von einer abgerissenen Leitung. Der Boden ist mit Schutt bedeckt. Nach Norden geht es zur Werkstatt, im Süden liegt die verriegelte Schleuse zu den Quartieren.",
        "exits": {
            "west": "ship_cockpit", # Statt "in"
            "north": "ship_workshop",
            "south": "crew_quarters" 
        },
        "img": "corridor_dark"
    },
    "ship_workshop": {
        "name": "Werkstatt",
        "desc": "Regale sind umgestürzt, Werkzeug liegt verstreut. In der Ecke steht eine demoliert wirkende Ladestation. Ein Lüftungsgitter an der Wand im Osten wurde aufgebogen – ein enger Schacht führt hinein.",
        "exits": {
            "south": "ship_corridor",
            "east": "maint_shaft_1" # Statt "in"
        },
        "img": "workshop"
    },
    
    # --- DAS LABYRINTH (Linearisiert für Kompass) ---
    # Wir nutzen Osten als "Tiefer in den Schacht" Richtung
    "maint_shaft_1": {
        "name": "Wartungsschacht A",
        "desc": "Eng. Dunkel. Es riecht nach altem Öl und Ozon. Du musst kriechen. Der Boden ist eiskalt.",
        "exits": {
            "west": "ship_workshop", # Zurück
            "east": "maint_junction" # Vorwärts
        },
        "img": "shaft_dark"
    },
    "maint_junction": {
        "name": "Verteilerknoten",
        "desc": "Hier treffen mehrere Röhren aufeinander. Ein Wirrwarr aus Kabeln hängt von der Decke. Es ist stockfinster. Du hörst Tropfen fallen. Irgendwoher weht ein eisiger Zug.",
        "exits": {
            "west": "maint_shaft_1", # Zurück
            "north": "maint_dead_end", # Statt "left"
            "south": "maint_shaft_2"  # Statt "right"
        },
        "img": "shaft_junction"
    },
    "maint_dead_end": {
        "name": "Sackgasse",
        "desc": "Der Schacht endet an einem massiven Lüfter, der sich langsam und quietschend dreht. Hier geht es nicht weiter.",
        "exits": {
            "south": "maint_junction" # Zurück
        }
    },
    "maint_shaft_2": {
        "name": "Wartungsschacht B",
        "desc": "Der Gang wird noch enger. Kondenswasser tropft dir in den Nacken. Im Osten ist eine Luke.",
        "exits": {
            "north": "maint_junction", # Zurück
            "east": "maint_shaft_3" # Statt "forward", blockiert durch Luke
        }
    },
    "maint_shaft_3": {
        "name": "Vertikaler Schacht",
        "desc": "Eine Leiter führt nach unten. Unten schimmert Licht.",
        "exits": {
            "west": "maint_shaft_2", # Zurück (eigentlich oben/seitlich)
            "down": "crew_quarters_vent"
        }
    },
    
    # --- ZIEL ---
    "crew_quarters_vent": {
        "name": "Lüftungsauslass",
        "desc": "Du blickst durch ein Gitter in den Vorraum der Quartiere.",
        "exits": {
            "up": "maint_shaft_3",
            "south": "crew_quarters" # Statt "out"
        }
    },
    "crew_quarters": {
        "name": "Vorraum Quartiere",
        "desc": "Die Luft hier ist stickig und kalt. Es ist totenstill. Im Norden ist die Bio-Schleuse (von dieser Seite unverschlossen), im Norden auch der Lüftungsschacht.",
        "exits": {
            "north": "ship_corridor", # Bio-Schleuse (jetzt von innen offen?)
            # Rückweg durch Lüftung ist optional, lassen wir hier mal weg für Fokus
        },
        "img": "quarters_hall"
    }
}