from engine.constants import *

class Resolver:
    @staticmethod
    def clean_args(args):
        skip_words = ["der", "die", "das", "ein", "eine", "einen", "im", "in", "am", "an"]
        return [w for w in args if w.lower() not in skip_words]

    @staticmethod
    def resolve_target(game, words, location_filter=FILTER_ROOM, verb=None):
        if not words: return None
        
        search_text = " ".join(words).lower()
        candidates = Resolver._collect_candidates(game, location_filter)
        
        # 1. Exakter Match auf ID (Debug/Admin)
        for obj in candidates:
            if obj[ATTR_ID] == search_text: return obj
            
        # 2. Match auf Name
        matches = [o for o in candidates if o.get(ATTR_NAME, "").lower() == search_text]
        if len(matches) == 1: return matches[0]
        
        # 3. Match auf Aliases
        alias_matches = []
        for obj in candidates:
            aliases = [a.lower() for a in obj.get(ATTR_ALIASES, [])]
            if search_text in aliases:
                alias_matches.append(obj)
                
        # Zusammenführen
        all_matches = matches + alias_matches
        
        # Deduplizieren
        unique = []
        seen = set()
        for m in all_matches:
            if m[ATTR_ID] not in seen:
                unique.append(m)
                seen.add(m[ATTR_ID])
                
        if len(unique) == 1: return unique[0]
        if len(unique) > 1:
            # Disambiguierung nötig!
            game.log('info', f"Meinst du: {', '.join([u[ATTR_NAME] for u in unique])}?")
            game.disambiguation = {
                'verb': verb,
                'candidates': unique
            }
            return None
            
        # 4. Fuzzy / Teil-Suche (wenn nichts exaktes gefunden)
        partial_matches = []
        for obj in candidates:
            name = obj.get(ATTR_NAME, "").lower()
            if search_text in name:
                partial_matches.append(obj)
            else:
                for a in obj.get(ATTR_ALIASES, []):
                    if search_text in a.lower():
                        partial_matches.append(obj)
                        break
        
        if len(partial_matches) == 1: return partial_matches[0]
        if len(partial_matches) > 1:
             # Wir nehmen den besten Match oder fragen nach
             # Einfachheit halber: Fragen
             names = list(set([o[ATTR_NAME] for o in partial_matches]))
             game.log('info', f"Meinst du: {', '.join(names)}?")
             return None

        return None

    @staticmethod
    def _collect_candidates(game, location_filter):
        if location_filter == FILTER_INVENTORY:
            return [game.objects[oid] for oid in game.inventory if oid in game.objects]
        
        elif location_filter == FILTER_ROOM: # HIER war der Fehler (konnte FILTER_ROOM nicht finden)
            return [o for o in game.objects.values() if o['location'] == game.location]
            
        elif location_filter == FILTER_RECURSIVE:
            # Alles im Raum + Alles im Inventar + Inhalte offener Container
            # Wir nutzen eine Hilfsfunktion oder Logik hier
            candidates = []
            
            # Inventar
            for oid in game.inventory:
                if oid in game.objects: candidates.append(game.objects[oid])
                
            # Raum (Top Level)
            in_room = [o for o in game.objects.values() if o['location'] == game.location]
            candidates.extend(in_room)
            
            # Rekursion für Container im Scope
            # (Vereinfacht: Wir nehmen einfach ALLE Objekte, deren Location eine der IDs in candidates ist)
            # Eine echte Rekursion wäre besser, aber für den Resolver reicht oft eine flache Hierarchie
            # oder wir verlassen uns darauf, dass der Spieler "nimm Münze" sagt und wir sie finden, auch wenn sie in der Kiste ist.
            
            # Wir machen es etwas breiter: Alle Objekte.
            # Aber filtern später auf Erreichbarkeit im InteractionHandler.
            return list(game.objects.values())
            
        return []

    @staticmethod
    def find_mentioned_npc(game, words):
        if not words: return None
        search = " ".join(words).lower()
        
        # Zuerst im Raum schauen
        local_npcs = [n for n in game.npcs if n['location'] == game.location]
        for npc in local_npcs:
            if search in npc[ATTR_NAME].lower(): return npc
            if search in [a.lower() for a in npc.get(ATTR_ALIASES, [])]: return npc
            
        return None
