from engine.constants import *
import difflib

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
        
        # Hilfsfunktion für Container-Inhalt (REKURSIV)
        def add_contents_of(container_list, check_open=True):
            for obj in container_list:
                # Wir schauen in Container und auf Surfaces
                if obj.get('type') in [TYPE_CONTAINER, TYPE_SURFACE]:
                    # Bei Surfaces immer, bei Containern nur wenn offen (oder check_open=False)
                    if not check_open or obj.get('type') == TYPE_SURFACE or obj.get('is_open', True):
                        contents = [o for o in game.objects.values() if o['location'] == obj[ATTR_ID]]
                        candidates.extend(contents)
                        # REKURSION: Auch in die gefundenen Objekte reinschauen (z.B. Item auf Waage im Schrank)
                        add_contents_of(contents, check_open)

        # 1. Sammle Basis-Listen
        room_objs = [o for o in game.objects.values() if o['location'] == game.location]
        inv_objs = [o for o in game.objects.values() if o['location'] == LOC_INVENTORY]

        if location_filter == FILTER_ROOM:
            candidates.extend(room_objs)
            add_contents_of(room_objs, check_open=True)
            
        elif location_filter == FILTER_INVENTORY:
            candidates.extend(inv_objs)
            add_contents_of(inv_objs, check_open=True)
            
        elif location_filter == FILTER_RECURSIVE:
            # Alles im Raum (tief) + Inventar (tief)
            candidates.extend(room_objs)
            add_contents_of(room_objs, check_open=True)
            
            candidates.extend(inv_objs)
            add_contents_of(inv_objs, check_open=True)
            
        else: # Default (Raum + Inventar, flach - Fallback, sollte kaum genutzt werden)
            candidates.extend(room_objs)
            candidates.extend(inv_objs)
            
        return candidates

    @staticmethod
    def resolve_target(game, search_words, location_filter=None, verb='unknown'):
        if not search_words: 
            return None 
        
        # Normalisierter Suchstring (z.B. "stim pulver")
        search_query = Resolver.normalize_term(" ".join(search_words))
        
        # 1. Existenz-Check (Global - Gibt es das Wort überhaupt im Spiel?)
        # Dies dient dazu, irrelevante Wörter früh abzufangen ("nimm blablabla")
        known_terms = set()
        for obj in game.objects.values():
             known_terms.add(Resolver.normalize_term(obj[ATTR_NAME]))
             for a in obj.get(ATTR_ALIASES, []): known_terms.add(Resolver.normalize_term(a))
             
        # Exakter Substring-Check im globalen Kontext
        is_known = False
        if any(search_query in term for term in known_terms):
            is_known = True
        
        # Falls nicht bekannt, Fuzzy Check
        if not is_known:
            matches = difflib.get_close_matches(search_query, list(known_terms), n=1, cutoff=0.7)
            if not matches:
                # Wirklich unbekannt
                raise ResolutionError(f"Ich weiß nicht, was ein '{search_query}' ist.", "unknown_word")
            else:
                # Es war ein Tippfehler, wir korrigieren intern für die weitere Suche
                search_query = matches[0]
                # Debug Info (könnte man bei Bedarf aktivieren)
                # print(f"[DEBUG] Autocorrect: {search_words} -> {search_query}")

        # 2. Kandidaten am aktuellen Ort sammeln
        candidates = Resolver._collect_candidates(game, location_filter)

        # 3. Filtern nach Name/Alias (Exakt oder Substring)
        matches = []
        for cand in candidates:
            cand_name = Resolver.normalize_term(cand[ATTR_NAME])
            cand_aliases = [Resolver.normalize_term(a) for a in cand.get(ATTR_ALIASES, [])]
            
            # Check: Query ist Teil des Namens oder eines Alias
            if search_query in cand_name or any(search_query in a for a in cand_aliases):
                if cand not in matches:
                    matches.append(cand)
        
        # Falls keine Matches vor Ort, aber Wort global bekannt war:
        # Prüfen wir, ob Fuzzy Matching vor Ort hilft (falls search_query oben nicht schon fuzzy angepasst wurde)
        if not matches:
             local_terms = {}
             for cand in candidates:
                 name = Resolver.normalize_term(cand[ATTR_NAME])
                 local_terms[name] = cand
                 for a in cand.get(ATTR_ALIASES, []): local_terms[Resolver.normalize_term(a)] = cand
             
             fuzzy_local = difflib.get_close_matches(search_query, list(local_terms.keys()), n=1, cutoff=0.7)
             if fuzzy_local:
                 matches.append(local_terms[fuzzy_local[0]])

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
        
        # Exakter/Substring Check
        for npc in local_npcs:
            n_name = Resolver.normalize_term(npc[ATTR_NAME])
            n_aliases = [Resolver.normalize_term(a) for a in npc.get(ATTR_ALIASES, [])]
            if query in n_name or any(query in alias for alias in n_aliases): return npc
            
        # Fuzzy Check
        npc_map = {}
        for npc in local_npcs:
            npc_map[Resolver.normalize_term(npc[ATTR_NAME])] = npc
            for a in npc.get(ATTR_ALIASES, []): npc_map[Resolver.normalize_term(a)] = npc
            
        matches = difflib.get_close_matches(query, list(npc_map.keys()), n=1, cutoff=0.7)
        if matches:
            return npc_map[matches[0]]
            
        return None