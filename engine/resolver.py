from engine.constants import *

class Resolver:
    @staticmethod
    def clean_args(args):
        # "den" hinzugefügt für Fälle wie "gib den verband"
        skip_words = ["der", "die", "das", "ein", "eine", "einen", "im", "in", "am", "an", "den"]
        return [w for w in args if w.lower() not in skip_words]

    @staticmethod
    def resolve_target(game, words, location_filter=FILTER_ROOM, verb=None):
        if not words: return None
        
        # WICHTIG: Arguments bereinigen (entfernt Füllwörter)
        clean_words = Resolver.clean_args(words)
        if not clean_words: return None
        
        search_text = " ".join(clean_words).lower()
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
            game.log('info', f"Meinst du: {', '.join([u[ATTR_NAME] for u in unique])}?")
            game.disambiguation = {
                'verb': verb,
                'candidates': unique
            }
            return None
            
        # 4. Fuzzy / Teil-Suche
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
             names = list(set([o[ATTR_NAME] for o in partial_matches]))
             game.log('info', f"Meinst du: {', '.join(names)}?")
             return None

        return None

    @staticmethod
    def _collect_candidates(game, location_filter):
        if location_filter == FILTER_INVENTORY:
            # FIX: Suche direkt in Objekten nach Location
            return [o for o in game.objects.values() if o.get('location') == LOC_INVENTORY]
        
        elif location_filter == FILTER_ROOM: 
            return [o for o in game.objects.values() if o.get('location') == game.location]
            
        elif location_filter == FILTER_RECURSIVE:
            # Alles (für globale Suche), ABER ohne LOC_VOID
            # Wir wollen nur Objekte finden, die tatsächlich im Spiel "existieren" (Raum, Inventar, Container)
            # und nicht solche, die erst noch gecraftet werden müssen oder gelöscht wurden.
            
            # Strategie: Wir sammeln rekursiv alles ein, was vom Spieler aus erreichbar ist.
            # Das ist sauberer als "alles außer void".
            
            # Startpunkte: Inventar und aktueller Raum
            candidates = []
            visited = set()
            
            # 1. Alles im Inventar
            inventory_items = [o for o in game.objects.values() if o.get('location') == LOC_INVENTORY]
            candidates.extend(inventory_items)
            
            # 2. Alles im Raum
            room_items = [o for o in game.objects.values() if o.get('location') == game.location]
            candidates.extend(room_items)
            
            # IDs merken für Rekursion
            to_process = [o[ATTR_ID] for o in candidates]
            visited.update(to_process)
            
            # 3. Rekursiv Inhalte von Containern finden
            # Wir schauen uns alle Objekte an. Wenn ihr Location-Parent in unserer 'visited'-Liste ist,
            # dann sind sie auch sichtbar/erreichbar (zumindest für den Resolver).
            # Das ist ineffizient O(N^2) im Worst Case, aber bei <1000 Items okay.
            # Besserer Ansatz: Iteriere solange, bis keine neuen Items mehr gefunden werden.
            
            changed = True
            while changed:
                changed = False
                # Suche Objekte, deren Parent bereits als "sichtbar" markiert wurde
                potential_contents = [
                    o for o in game.objects.values() 
                    if o.get('location') in visited and o[ATTR_ID] not in visited
                ]
                
                for item in potential_contents:
                    # Optional: Prüfen ob Parent ein offener Container ist?
                    # Für den Resolver ist es oft besser, tolerant zu sein ("nimm münze" geht auch wenn sie in der offenen truhe ist)
                    # Wir lassen die strikte "is_open"-Prüfung dem InteractionHandler, 
                    # aber wir schließen VOID definitiv aus, da VOID nie in 'visited' sein wird.
                    candidates.append(item)
                    visited.add(item[ATTR_ID])
                    to_process.append(item[ATTR_ID])
                    changed = True
            
            return candidates
            
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
