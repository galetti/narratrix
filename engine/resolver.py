from engine.constants import *

class ResolutionError(Exception):
    """Custom Exception für fehlgeschlagene Auflösung, mit Grund."""
    def __init__(self, message, reason_code="unknown"):
        super().__init__(message)
        self.reason_code = reason_code

class Resolver:
    """
    Hilfsklasse zum Auflösen von Text zu Spielobjekten.
    Zentralisiert die Suchlogik und Disambiguierung.
    """

    @staticmethod
    def clean_args(args):
        ignore = ["in", "im", "an", "am", "auf", "mit", "bei", "zu", "nach", "den", "die", "das", "dem", "der", "einen", "eine", "ein"]
        return [w for w in args if w.lower() not in ignore]

    @staticmethod
    def normalize_term(text):
        """Ersetzt Bindestriche und Unterstriche durch Leerzeichen für flexibleres Matching."""
        return text.lower().replace("-", " ").replace("_", " ").strip()

    @staticmethod
    def _collect_candidates(game, location_filter):
        """Sammelt Kandidaten basierend auf dem Filter. Zentrale Logik für alle Suchen."""
        candidates = []
        
        # Hilfsfunktion für Container-Inhalt
        def add_contents_of(container_list, check_open=True):
            for obj in container_list:
                # Wir schauen in Container und auf Surfaces
                if obj.get('type') in [TYPE_CONTAINER, TYPE_SURFACE]:
                    # Bei Surfaces immer, bei Containern nur wenn offen (oder check_open=False)
                    if not check_open or obj.get('type') == TYPE_SURFACE or obj.get('is_open', True):
                        contents = [o for o in game.objects.values() if o['location'] == obj[ATTR_ID]]
                        candidates.extend(contents)

        # 1. Sammle Basis-Listen
        room_objs = [o for o in game.objects.values() if o['location'] == game.location]
        inv_objs = [o for o in game.objects.values() if o['location'] == LOC_INVENTORY]

        if location_filter == FILTER_ROOM:
            candidates.extend(room_objs)
            
        elif location_filter == FILTER_INVENTORY:
            candidates.extend(inv_objs)
            # Auch im Inventar schauen wir in offene Container (z.B. Becher)
            add_contents_of(inv_objs, check_open=True)
            
        elif location_filter == FILTER_RECURSIVE:
            # Alles im Raum + Inhalt (Surface/Offen) + Inventar + Inhalt
            candidates.extend(room_objs)
            add_contents_of(room_objs, check_open=True)
            
            candidates.extend(inv_objs)
            add_contents_of(inv_objs, check_open=True)
            
        else: # Default (Raum + Inventar, flach)
            candidates.extend(room_objs)
            candidates.extend(inv_objs)
            
        return candidates

    @staticmethod
    def resolve_target(game, search_words, location_filter=None, verb='unknown'):
        if not search_words: 
            return None 
        
        # Normalisierter Suchstring (z.B. "stim pulver")
        search_query = Resolver.normalize_term(" ".join(search_words))
        
        # 1. Existenz-Check (Gibt es das Wort überhaupt im Spiel?)
        anywhere_match = False
        for obj in game.objects.values():
             # Auch Namen und Aliases normalisieren
             obj_name = Resolver.normalize_term(obj[ATTR_NAME])
             aliases = [Resolver.normalize_term(a) for a in obj.get(ATTR_ALIASES, [])]
             
             if search_query in obj_name or any(search_query in a for a in aliases):
                 anywhere_match = True
                 break
        
        if not anywhere_match:
            raise ResolutionError(f"Ich weiß nicht, was ein '{search_query}' ist.", "unknown_word")

        # 2. Kandidaten am aktuellen Ort sammeln
        candidates = Resolver._collect_candidates(game, location_filter)

        # 3. Filtern nach Name/Alias
        matches = []
        for cand in candidates:
            cand_name = Resolver.normalize_term(cand[ATTR_NAME])
            cand_aliases = [Resolver.normalize_term(a) for a in cand.get(ATTR_ALIASES, [])]
            
            if search_query in cand_name or any(search_query in a for a in cand_aliases):
                if cand not in matches:
                    matches.append(cand)
        
        # 4. Ergebnis & Fehlerbehandlung
        if len(matches) == 0:
            if location_filter == FILTER_INVENTORY:
                 raise ResolutionError(f"Du hast kein '{search_query}' dabei.", "not_in_inventory")
            else:
                 raise ResolutionError(f"Ich sehe hier kein '{search_query}'.", "not_here")
        
        if len(matches) == 1: 
            return matches[0]
        
        # 5. Disambiguierung (Mehrere Treffer)
        names = [m[ATTR_NAME] for m in matches]
        game.log('info', f"Meinst du: {', '.join(names)}?")
        
        game.disambiguation = {
            'verb': verb,
            'candidates': matches,
            'original_args': search_words
        }
        return None

    @staticmethod
    def find_mentioned_npc(game, words):
        query = Resolver.normalize_term(" ".join(words))
        local_npcs = [n for n in game.npcs if n['location'] == game.location]
        for npc in local_npcs:
            n_name = Resolver.normalize_term(npc[ATTR_NAME])
            n_aliases = [Resolver.normalize_term(a) for a in npc.get(ATTR_ALIASES, [])]
            
            if n_name in query or any(alias in query for alias in n_aliases): return npc
        return None