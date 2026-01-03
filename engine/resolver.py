from engine.constants import *
import difflib

class ResolutionError(Exception):
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
        return text.lower().replace("-", " ").replace("_", " ").strip()

    @staticmethod
    def _collect_candidates(game, location_filter):
        """Sammelt Kandidaten basierend auf dem Filter."""
        candidates = []
        
        # Hilfsfunktion für Container-Inhalt
        def add_contents_of(container_list, check_open=True):
            for obj in container_list:
                if obj.get('type') in [TYPE_CONTAINER, TYPE_SURFACE]:
                    if not check_open or obj.get('type') == TYPE_SURFACE or obj.get('is_open', True):
                        contents = [o for o in game.objects.values() if o['location'] == obj[ATTR_ID]]
                        candidates.extend(contents)
                        add_contents_of(contents, check_open)

        # Basis-Listen
        room_objs = [o for o in game.objects.values() if o['location'] == game.location]
        inv_objs = [o for o in game.objects.values() if o['location'] == LOC_INVENTORY]
        
        # NEU: NPCs im Raum als Kandidaten hinzufügen (behandeln wir wie Objekte für Interaktion)
        room_npcs = [n for n in game.npcs if n['location'] == game.location]

        if location_filter == FILTER_ROOM:
            candidates.extend(room_objs)
            candidates.extend(room_npcs) # NPCs sind im Raum
            add_contents_of(room_objs, check_open=True)
            
        elif location_filter == FILTER_INVENTORY:
            candidates.extend(inv_objs)
            add_contents_of(inv_objs, check_open=True)
            
        elif location_filter == FILTER_RECURSIVE:
            # Alles
            candidates.extend(room_objs)
            candidates.extend(room_npcs) # Auch hier NPCs
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
        
        search_query = Resolver.normalize_term(" ".join(search_words))
        
        # 1. Existenz-Check (Global) - Inklusive NPCs!
        known_terms = set()
        for obj in game.objects.values():
             known_terms.add(Resolver.normalize_term(obj[ATTR_NAME]))
             for a in obj.get(ATTR_ALIASES, []): known_terms.add(Resolver.normalize_term(a))
        
        for npc in game.npcs:
             known_terms.add(Resolver.normalize_term(npc[ATTR_NAME]))
             for a in npc.get(ATTR_ALIASES, []): known_terms.add(Resolver.normalize_term(a))
             
        is_known = False
        if any(search_query in term for term in known_terms):
            is_known = True
        
        if not is_known:
            matches = difflib.get_close_matches(search_query, list(known_terms), n=1, cutoff=0.7)
            if not matches:
                raise ResolutionError(f"Ich weiß nicht, was ein '{search_query}' ist.", "unknown_word")
            else:
                search_query = matches[0] # Autocorrect für Suche

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
        
        # Fallback Fuzzy Search Local
        if not matches:
             local_terms = {}
             for cand in candidates:
                 name = Resolver.normalize_term(cand[ATTR_NAME])
                 local_terms[name] = cand
                 for a in cand.get(ATTR_ALIASES, []): local_terms[Resolver.normalize_term(a)] = cand
             
             fuzzy_local = difflib.get_close_matches(search_query, list(local_terms.keys()), n=1, cutoff=0.7)
             if fuzzy_local:
                 matches.append(local_terms[fuzzy_local[0]])

        # 4. Ergebnis
        if len(matches) == 0:
            if location_filter == FILTER_INVENTORY:
                 raise ResolutionError(f"Du hast kein '{search_query}' dabei.", "not_in_inventory")
            else:
                 raise ResolutionError(f"Ich sehe hier kein '{search_query}'.", "not_here")
        
        if len(matches) == 1: 
            return matches[0]
        
        # 5. Disambiguierung
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
        """Spezifische NPC Suche für Dialoge (bleibt erhalten für Direktansprache)."""
        query = Resolver.normalize_term(" ".join(words))
        local_npcs = [n for n in game.npcs if n['location'] == game.location]
        
        for npc in local_npcs:
            n_name = Resolver.normalize_term(npc[ATTR_NAME])
            n_aliases = [Resolver.normalize_term(a) for a in npc.get(ATTR_ALIASES, [])]
            if query in n_name or any(query in alias for alias in n_aliases): return npc
            
        npc_map = {}
        for npc in local_npcs:
            npc_map[Resolver.normalize_term(npc[ATTR_NAME])] = npc
            for a in npc.get(ATTR_ALIASES, []): npc_map[Resolver.normalize_term(a)] = npc
            
        matches = difflib.get_close_matches(query, list(npc_map.keys()), n=1, cutoff=0.7)
        if matches:
            return npc_map[matches[0]]
            
        return None