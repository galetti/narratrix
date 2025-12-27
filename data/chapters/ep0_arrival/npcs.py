# Fiona wird eingeführt. Aris und Val sind entspannt.

NPCS = [
    {
        "id": "npc_fiona", "name": "Fiona", "aliases": ["biologin", "fiona"], "is_global": False,
        "start_loc": "medbay", "location": "medbay",
        "initial_state": "working",
        "states": {
            "working": {
                "behavior": {"movement_chance": 10, "affinity": ["medbay"]},
                "visuals": {"img": "face_fiona_happy", "desc": "Eine junge Frau mit wilden roten Haaren und einem Laborkittel.", "personality": "Quirlig"}, # 
                "dialogue": {
                    "greeting": "Oh, hallo! Du bist der neue Ingenieur, oder? Ich bin Fiona!",
                    "frucht": "Ist sie nicht faszinierend? Aber ich kriege das Gewicht nicht bestimmt, die Waage spinnt.",
                    "waage": "Kannst du mir helfen? Leg die Frucht mal drauf, vielleicht klappt es bei dir.",
                    "gewicht": {"condition": {"type": "item_location", "item": "alien_fruit", "location": "scale"}, "text": "0.35 kg? Perfekt! Danke dir!", "effect": {"type": "learn", "fact": "fiona_helped"}}
                }
            },
            "dinner": {
                "behavior": {"movement_chance": 0, "affinity": ["cantina"]},
                "visuals": {"img": "face_fiona_happy", "desc": "Sie isst herzhaft."},
                "dialogue": {"greeting": "Das Essen ist besser als sein Ruf!"}
            }
        }
    },
    # Wir müssen Aris und Val hier "überschreiben" oder anpassen, da sie in Common panisch/verletzt sind.
    # Da Common geladen wird, nutzen wir hier denselben ID, um den Zustand zu setzen.
    # ACHTUNG: Der StoryLoader merged Listen. Wir haben dann evtl. 2 Aris-Einträge wenn wir nicht aufpassen.
    # BESSER: Wir definieren Aris und Val in Ep0 NICHT neu, sondern setzen ihren Startzustand im GameState oder per Event.
    # Da das Mergen komplex ist, ist es einfacher, für Ep0 lokale Versionen zu haben, die Common "überdecken" (wenn wir IDs nutzen würden)
    # Aber da wir Listen addieren, haben wir Duplikate.
    
    # LÖSUNG: Ep0 NPCs sind nur Fiona. Aris und Val kommen aus Common.
    # ABER: Aris ist in Common "panic". Wir müssen ihn auf "relaxed" setzen.
    # Das machen wir über ein "Init Event" in der Matrix!
]