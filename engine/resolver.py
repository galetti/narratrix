# narratrix_engine/engine/resolver.py
from __future__ import annotations

import difflib
from typing import TYPE_CHECKING, Any

from engine.constants import (
    ATTR_ALIASES,
    ATTR_ID,
    ATTR_NAME,
    FILTER_INVENTORY,
    FILTER_RECURSIVE,
    FILTER_ROOM,
    LOC_INVENTORY,
    TYPE_CONTAINER,
    TYPE_SURFACE,
)
from engine.schema import NPCData, ObjectData

if TYPE_CHECKING:
    from engine.game_state import GameState


class ResolutionError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class AmbiguityError(Exception):
    """
    Wird geworfen, wenn ein Begriff nicht eindeutig ist.
    Bubbles up zum ActionDispatcher, um den Kontext zu erhalten.
    """
    def __init__(self, candidates: list[dict[str, Any]], query_words: list[str]) -> None:
        self.candidates: list[dict[str, Any]] = candidates
        self.query_words: list[str] = query_words 


class Resolver:
    """
    Hilfsklasse zum Auflösen von Text zu Spielobjekten.
    Zentralisiert die Suchlogik und Disambiguierung.
    Includes Performance-Optimizations (Lazy Loading).
    """

    @staticmethod
    def clean_args(args: list[str]) -> list[str]:
        ignore = ["in", "im", "an", "am", "auf", "mit", "bei", "zu", "nach", "den", "die", "das", "dem", "der", "einen", "eine", "ein"]
        return [w for w in args if w.lower() not in ignore]

    @staticmethod
    def normalize_term(text: str) -> str:
        return text.lower().replace("-", " ").replace("_", " ").strip()

    @staticmethod
    def _collect_candidates(game: GameState, location_filter: str | None) -> list[dict[str, Any]]:
        """Sammelt Kandidaten basierend auf dem Filter."""
        candidates: list[dict[str, Any]] = []
        
        # Hilfsfunktion für Container-Inhalt
        visited_containers: set[str | None] = set()

        def add_contents_of(container_list: list[ObjectData], check_open: bool = True) -> None:
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
    def resolve_target(
        game: GameState,
        search_words: list[str],
        location_filter: str | None = None,
        verb: str = 'unknown',
    ) -> dict[str, Any] | None:
        if not search_words: 
            return None 
        
        # 1. Schneller Pfad: Lokale Suche OHNE Autokorrektur
        search_query = Resolver.normalize_term(" ".join(search_words))
        candidates = Resolver._collect_candidates(game, location_filter)
        
        exact_matches: list[dict[str, Any]] = []
        substring_matches: list[dict[str, Any]] = []
        
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
        known_terms: set[str] = set()
        for obj in game.objects.values():
             known_terms.add(Resolver.normalize_term(obj[ATTR_NAME]))
             for a in obj.get(ATTR_ALIASES, []): known_terms.add(Resolver.normalize_term(a))
        
        for npc in game.npcs:
             known_terms.add(Resolver.normalize_term(npc[ATTR_NAME]))
             for a in npc.get(ATTR_ALIASES, []): known_terms.add(Resolver.normalize_term(a))
             
        # Difflib Fuzzy Match
        corrected_query: str | None = None
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
    def find_mentioned_npc(game: GameState, words: list[str]) -> NPCData | None:
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
        npc_map: dict[str, NPCData] = {}
        for npc in local_npcs:
            npc_map[Resolver.normalize_term(npc[ATTR_NAME])] = npc
            for a in npc.get(ATTR_ALIASES, []): npc_map[Resolver.normalize_term(a)] = npc
            
        matches = difflib.get_close_matches(query, list(npc_map.keys()), n=1, cutoff=0.7)
        if matches:
            return npc_map[matches[0]]
            
        return None
