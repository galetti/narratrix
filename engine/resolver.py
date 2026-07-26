# narratrix_engine/engine/resolver.py
from engine.constants import *
import difflib

class ResolutionError(Exception):
    def __init__(self, message):
        super().__init__(message)

class AmbiguityError(Exception):
    """
    Wird geworfen, wenn ein Begriff nicht eindeutig ist.
    Bubbles up zum ActionDispatcher, um den Kontext zu erhalten.
    """
    def __init__(self, candidates, query_words):
        self.candidates = candidates
        self.query_words = query_words 

class Resolver:
    """
    Hilfsklasse zum Auflösen von Text zu Spielobjekten.
    Zentralisiert die Suchlogik und Disambiguierung.
    Includes Performance-Optimizations (Lazy Loading).
    """

    @staticmethod
    def clean_args(args):
        ignore = ["in", "im", "an", "am", "auf", "mit", "bei", "zu", "nach", "den", "die", "das", "dem", "der", "einen", "eine", "ein"]
        return [w for w in args if w.lower() not in ignore]

    @staticmethod
    def normalize_term(text):
        return text.lower().replace("-", " ").replace("_", " ").strip()

    @staticmethod
    def _collect_candidates(game, location_filter):
        """Sammelt Kandidaten basierend auf dem Filter."""
        candidates = []
        
        # Hilfsfunktion für Container-Inhalt
        visited_containers = set()

        def add_contents_of(container_list, check_open=True):
            for obj in container_list:
                if obj.get('type') in [TYPE_CONTAINER, TYPE_SURFACE]:
                    obj_id = obj.get(ATTR_ID)
                    if obj_id in visited_containers:
                        continue
                    visited_containers.add(obj_id)
                    if not check_open or obj.get('type') == TYPE_SURFACE or obj.get('is_open', True):
                        contents = [o for o in game.objects.values() if o['location'] == obj[ATTR_ID]]
                        candidates.extend(contents)
                        add_contents_of(contents, check_open)

        # Basis-Listen (Listen-Comprehensions sind in Python sehr schnell)
        room_objs = [o for o in game.objects.values() if o['location'] == game.location]
        inv_objs = [o for o in game.objects.values() if o['location'] == LOC_INVENTORY]
        room_npcs = [n for n in game.npcs if n['location'] == game.location]

        if location_filter == FILTER_ROOM:
            candidates.extend(room_objs)
            candidates.extend(room_npcs)
            add_contents_of(room_objs, check_open=True)
            
        elif location_filter == FILTER_INVENTORY:
            candidates.extend(inv_objs)
            add_contents_of(inv_objs, check_open=True)
            
        elif location_filter == FILTER_RECURSIVE:
            candidates.extend(room_objs)
            candidates.extend(room_npcs)
            add_contents_of(room_objs, check_open=True)
            candidates.extend(inv_objs)
            add_contents_of(inv_objs, check_open=True)
            
        else:
            candidates.extend(room_objs)
            candidates.extend(inv_objs)
            candidates.extend(room_npcs)
            
        return candidates

    @staticmethod
    def resolve_target(game, search_words, location_filter=None, verb='unknown'):
        if not search_words: 
            return None 
        
        # 1. Schneller Pfad: Lokale Suche OHNE Autokorrektur
        search_query = Resolver.normalize_term(" ".join(search_words))
        candidates = Resolver._collect_candidates(game, location_filter)
        
        exact_matches = []
        substring_matches = []
        
        # 1a. Exakter Match oder Substring Match (Lokal)
        for cand in candidates:
            cand_name = Resolver.normalize_term(cand[ATTR_NAME])
            cand_aliases = [Resolver.normalize_term(a) for a in cand.get(ATTR_ALIASES, [])]
            
            # Priorität: Exakter Match
            if search_query == cand_name or search_query in cand_aliases:
                if cand not in exact_matches: exact_matches.append(cand)
            # Sekundär: Substring Match (nur wenn wir noch keine exakten Matches haben oder sammeln wollen)
            elif search_query in cand_name or any(search_query in a for a in cand_aliases):
                if cand not in substring_matches: substring_matches.append(cand)
        
        matches = exact_matches or substring_matches
        if matches:
            if len(matches) == 1: return matches[0]
            raise AmbiguityError(matches, search_words)

        # 2. Langsamer Pfad: Autokorrektur & Globale Suche
        # Wird nur ausgeführt, wenn der Spieler sich vertippt hat oder Quatsch eingibt.
        
        # Globale Begriffsliste aufbauen (Teuer!)
        known_terms = set()
        for obj in game.objects.values():
             known_terms.add(Resolver.normalize_term(obj[ATTR_NAME]))
             for a in obj.get(ATTR_ALIASES, []): known_terms.add(Resolver.normalize_term(a))
        
        for npc in game.npcs:
             known_terms.add(Resolver.normalize_term(npc[ATTR_NAME]))
             for a in npc.get(ATTR_ALIASES, []): known_terms.add(Resolver.normalize_term(a))
             
        # Difflib Fuzzy Match
        corrected_query = None
        fuzzy_matches = difflib.get_close_matches(search_query, list(known_terms), n=1, cutoff=0.7)
        
        if fuzzy_matches:
            corrected_query = fuzzy_matches[0]
            # Jetzt suchen wir mit dem korrigierten Begriff erneut in den LOKALEN Kandidaten
            for cand in candidates:
                cand_name = Resolver.normalize_term(cand[ATTR_NAME])
                cand_aliases = [Resolver.normalize_term(a) for a in cand.get(ATTR_ALIASES, [])]
                
                if corrected_query in cand_name or any(corrected_query in a for a in cand_aliases):
                    if cand not in matches: matches.append(cand)
        
        # 3. Ergebnis Auswertung
        if len(matches) == 0:
            error_msg = f"Ich sehe hier kein '{search_query}'."
            if not corrected_query:
                # Es gab nicht mal einen ähnlichen Begriff im ganzen Spiel
                error_msg = f"Ich weiß nicht, was ein '{search_query}' ist."
            elif location_filter == FILTER_INVENTORY:
                error_msg = f"Du hast kein '{corrected_query}' dabei."
            else:
                # Begriff existiert im Spiel, ist aber nicht hier
                error_msg = f"Ich sehe hier kein '{corrected_query}'."

            raise ResolutionError(error_msg)
        
        if len(matches) == 1: 
            return matches[0]
        
        raise AmbiguityError(matches, search_words)

    @staticmethod
    def find_mentioned_npc(game, words):
        """Spezifische NPC Suche für Dialoge."""
        query = Resolver.normalize_term(" ".join(words))
        if not query:
            return None
        local_npcs = [n for n in game.npcs if n['location'] == game.location]
        
        # 1. Schnellsuche
        for npc in local_npcs:
            n_name = Resolver.normalize_term(npc[ATTR_NAME])
            n_aliases = [Resolver.normalize_term(a) for a in npc.get(ATTR_ALIASES, [])]
            if query in n_name or any(query in alias for alias in n_aliases): return npc
        
        # 2. Fuzzy Suche (nur lokal bei NPCs, Dialoge über Distanz gehen eh nicht)
        npc_map = {}
        for npc in local_npcs:
            npc_map[Resolver.normalize_term(npc[ATTR_NAME])] = npc
            for a in npc.get(ATTR_ALIASES, []): npc_map[Resolver.normalize_term(a)] = npc
            
        matches = difflib.get_close_matches(query, list(npc_map.keys()), n=1, cutoff=0.7)
        if matches:
            return npc_map[matches[0]]
            
        return None
