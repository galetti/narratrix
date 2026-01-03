from engine.constants import *
from engine.resolver import Resolver

class CraftingSystem:
    """
    Verwaltet das Kombinieren von Gegenständen mit erweiterten Bedingungen
    wie Werkzeugen, Arbeitsstationen und Bauplänen.
    """
    def __init__(self, game):
        self.game = game

    def perform_combine(self, item1_name, item2_name, verb="use"):
        """
        Hauptmethode, die vom ActionDispatcher aufgerufen wird.
        """
        # 1. Objekte auflösen
        # Wir geben das Verb an den Resolver weiter, damit dieser bei Disambiguierung weiß, was wir tun
        obj1 = self._resolve_crafting_item(item1_name, verb)
        obj2 = self._resolve_crafting_item(item2_name, verb)

        if not obj1 or not obj2:
            # Falls eines None ist, hat der Resolver schon eine Error-Message oder Disambiguierung ausgelöst
            return "Ich konnte eines der Objekte nicht finden (muss im Inventar oder greifbar sein)."

        # 2. Rezept finden
        recipe = self._find_recipe(obj1['id'], obj2['id'])
        if not recipe:
            return "Das lässt sich nicht sinnvoll kombinieren."

        # 3. Bedingungen prüfen
        
        # A. Bauplan / Wissen
        if 'blueprint' in recipe:
            knowledge_id = recipe['blueprint']
            if knowledge_id not in self.game.knowledge:
                return "Du hast keine Ahnung, wie man diese Teile verbindet. Dir fehlt ein Bauplan oder Wissen."

        # B. Station (Werkbank, Herd, etc.)
        if 'station' in recipe:
            station_id = recipe['station']
            if not self._is_station_available(station_id):
                station_name = self._get_obj_name(station_id)
                return f"Dafür brauchst du eine Arbeitsfläche: {station_name}."

        # C. Werkzeuge
        if 'tools' in recipe:
            missing_tools = []
            for tool_id in recipe['tools']:
                # Tool ist da, wenn es eines der Input Items ist ODER im Inventar liegt
                if tool_id == obj1['id'] or tool_id == obj2['id']:
                    continue
                    
                if not self._has_item_in_inventory(tool_id):
                    tool_name = self._get_obj_name(tool_id)
                    missing_tools.append(tool_name)
            
            if missing_tools:
                return f"Dir fehlt das nötige Werkzeug: {', '.join(missing_tools)}."

        # 4. Crafting durchführen
        return self._execute_crafting(obj1, obj2, recipe)

    def _resolve_crafting_item(self, name, verb):
        """Sucht das Item im Inventar oder im Raum (für Stationen/große Objekte)."""
        try:
            # Prio 1: Inventar
            return Resolver.resolve_target(self.game, name.split(), location_filter=FILTER_INVENTORY, verb=verb)
        except:
            pass
        
        try:
            # Prio 2: Raum (z.B. wenn man etwas auf einen stationären Amboss legt)
            return Resolver.resolve_target(self.game, name.split(), location_filter=FILTER_ROOM, verb=verb)
        except:
            return None

    def _find_recipe(self, id1, id2):
        """Sucht ein passendes Rezept für die beiden IDs (Reihenfolge egal)."""
        # Wir laden die Kombinationen dynamisch aus dem GameState
        combinations = getattr(self.game, 'combinations', [])
        
        for recipe in combinations:
            ing = recipe.get('ingredients', [])
            tools = recipe.get('tools', [])
            
            # Alle IDs in einem Topf
            all_parts = ing + tools
            
            # Wir prüfen, ob die beiden Items (id1, id2) in der Menge der benötigten Dinge vorkommen.
            if id1 in all_parts and id2 in all_parts and id1 != id2:
                # Treffer! 
                return recipe
            
            # Sonderfall: Single Ingredient + Tool (z.B. "use screwdriver with door")
            # Wenn Ingredient 'door' und Tool 'screwdriver' ist.
            # Hier prüfen wir explizit auf die Rollenverteilung, falls id1 und id2 nicht beide in all_parts sind (was selten ist, außer das Rezept ist komplexer)
            if len(ing) == 1 and len(tools) >= 1:
                if (id1 == ing[0] and id2 in tools) or (id2 == ing[0] and id1 in tools):
                    return recipe

        return None

    def _is_station_available(self, station_id):
        """Prüft, ob die Station im Raum oder (selten) im Inventar ist."""
        if self.game.location == station_id:
            return True
            
        for obj in self.game.objects.values():
            if obj['id'] == station_id:
                if obj['location'] == self.game.location or obj['location'] == LOC_INVENTORY:
                    return True
        return False

    def _has_item_in_inventory(self, item_id):
        """Prüft auf Besitz eines Items (für Werkzeuge)."""
        for obj in self.game.objects.values():
            if obj['id'] == item_id and obj['location'] == LOC_INVENTORY:
                return True
        return False

    def _get_obj_name(self, obj_id):
        """Hilfsfunktion für Fehlernachrichten."""
        obj = self.game.objects.get(obj_id)
        if obj: return obj[ATTR_NAME]
        
        room = self.game.rooms.get(obj_id)
        if room: return room[ATTR_NAME]
        return "Unbekanntes Objekt"

    def _execute_crafting(self, obj1, obj2, recipe):
        """Führt den Crafting-Prozess aus (Verbrauchen, Erzeugen, Effekte)."""
        
        preserved = recipe.get('preserve', [])
        tools = recipe.get('tools', [])
        
        # Logik: Items verbrauchen, außer sie sind Tools oder auf der Preserve-Liste
        if obj1['id'] not in preserved and obj1['id'] not in tools:
            obj1['location'] = LOC_VOID
        
        if obj2['id'] not in preserved and obj2['id'] not in tools:
            obj2['location'] = LOC_VOID

        # Ergebnis erzeugen
        result_id = recipe.get('result')
        if result_id:
            result_obj = self.game.objects.get(result_id)
            if result_obj:
                result_obj['location'] = LOC_INVENTORY
                
                # Müll/Nebenprodukte
                byproducts = recipe.get('byproducts', [])
                for bid in byproducts:
                    bp = self.game.objects.get(bid)
                    if bp: bp['location'] = LOC_INVENTORY
            else:
                # Wenn Result None ist (nur Effekte), ist das okay. Aber wenn String da ist und Item fehlt: Fehler.
                # Hier geben wir nur eine Warnung aus
                pass

        # Effekte ausführen
        if 'effects' in recipe:
            for eff in recipe['effects']:
                e_type = eff.get('type')
                
                if e_type == 'update_object':
                    target_id = eff.get('target')
                    updates = eff.get('updates', {})
                    
                    target = self.game.objects.get(target_id)
                    if not target: # Check NPCs
                        target = next((n for n in self.game.npcs if n['id'] == target_id), None)
                    
                    if target:
                        target.update(updates)
                        
                elif e_type == 'trigger_event':
                    event_id = eff.get('id')
                    if hasattr(self.game, 'events'):
                        # Wir suchen das Event in der Liste
                        target_event = next((e for e in self.game.events.events if e.get('id') == event_id), None)
                        if target_event:
                            self.game.events._execute_event(target_event)
                        else:
                            pass # Event nicht gefunden, stillschweigend ignorieren oder loggen

        return recipe.get('message', "Erledigt.")