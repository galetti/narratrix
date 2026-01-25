# narratrix_engine/engine/systems/crafting.py
from engine.constants import *

class CraftingSystem:
    def __init__(self, game):
        self.game = game

    def perform_combine(self, item1_name, item2_name, verb="use"):
        # 1. Objekte finden (Items ODER NPCs)
        item1 = self._find_obj_or_npc_by_name(item1_name)
        item2 = self._find_obj_or_npc_by_name(item2_name)
        
        if not item1 or not item2:
            return "Ich weiß nicht, was du kombinieren willst."

        # Identifiziere IDs
        # Items haben ATTR_ID ('id'), NPCs auch ('id')
        id1 = item1.get(ATTR_ID, item1.get('id'))
        id2 = item2.get(ATTR_ID, item2.get('id'))
        
        possible_recipes = []
        for combo in self.game.combinations:
            if combo.get('verb') != verb: continue
            
            recipe_items = combo.get('items', [])
            ingredients = combo.get('ingredients', {})
            station = combo.get('station')
            
            # Fall A: Exakte ID-Übereinstimmung (z.B. [tool, npc])
            if recipe_items:
                if set(recipe_items) == {id1, id2}:
                    possible_recipes.append(combo)
                    continue

            # Fall B: Zutaten/Station Logik
            is_station_match = (station == id1 or station == id2)
            is_ingredient_match = (id1 in ingredients or id2 in ingredients)
            
            if is_station_match or is_ingredient_match:
                possible_recipes.append(combo)

        if not possible_recipes:
            return "Das scheint nicht zu funktionieren."

        for recipe in possible_recipes:
            success, msg = self._try_craft(recipe, [item1, item2])
            if success:
                return msg
            elif msg: 
                return msg

        return "Das funktioniert so nicht."

    def _try_craft(self, recipe, interacting_items):
        # 1. Prüfe Station
        required_station = recipe.get('station')
        if required_station:
            station_present = False
            # Check interaction objects
            for item in interacting_items:
                i_id = item.get(ATTR_ID, item.get('id'))
                if i_id == required_station:
                    station_present = True; break
            
            # Check environment
            if not station_present:
                # Check room items
                if required_station in self.game.objects:
                    if self.game.objects[required_station]['location'] == self.game.location:
                        station_present = True
                # Check room NPCs (falls Station ein NPC ist? Unwahrscheinlich aber möglich)
                if not station_present:
                    for npc in self.game.npcs:
                        if npc['id'] == required_station and npc['location'] == self.game.location:
                            station_present = True; break

            if not station_present: return False, None 

        # 2. Prüfe Zutaten (Nur im Inventar zählen)
        ingredients = recipe.get('ingredients', {})
        if 'items' in recipe and not ingredients:
            # Legacy: items liste ist keine Kosten-Liste, sondern Auslöser. 
            # Wenn ingredients leer ist, verbrauchen wir nichts (Standard Interaktion).
            ingredients = {}

        inventory_ids = [o[ATTR_ID] for o in self.game.objects.values() if o['location'] == LOC_INVENTORY]
        
        missing = []
        for ing_id, count in ingredients.items():
            available = 0
            item = self.game.objects.get(ing_id)
            if not item: continue
            
            if item['location'] == LOC_INVENTORY:
                if item.get('is_resource'): available = item.get('count', 1)
                else: available = 1
            
            # Check interacting items (falls man Ressource in Hand hält?)
            for i_item in interacting_items:
                i_id = i_item.get(ATTR_ID, i_item.get('id'))
                if i_id == ing_id and i_item.get('location') != LOC_INVENTORY:
                     if i_item.get('is_resource'): available += i_item.get('count', 1)
                     else: available += 1

            if available < count:
                missing.append(f"{count}x {item[ATTR_NAME]}")

        if missing: return False, f"Dir fehlt noch: {', '.join(missing)}."

        # 3. Ausführung - Zutaten entfernen
        for ing_id, count in ingredients.items():
            item = self.game.objects.get(ing_id)
            if not item: continue
            
            if not recipe.get('consume_tools', True) and item.get('is_tool'):
                continue
                
            if item.get('is_resource'):
                current = item.get('count', 1)
                if current > count: item['count'] = current - count
                else: item['location'] = LOC_VOID
            else:
                item['location'] = LOC_VOID

        return True, self._execute_combination(recipe, interacting_items)

    def _execute_combination(self, combo, objects):
        # FIX: Reihenfolge geändert! Erst Effekte, dann Return.
        
        # 1. Effekte verarbeiten
        if 'effect' in combo:
            # Versuch Kontext-NPC zu finden
            context_npc = None
            for o in objects:
                # NPCs haben kein 'type' Feld zwingend, aber eine ID in game.npcs
                if o in self.game.npcs: context_npc = o; break
            
            self.game.effects.process(combo['effect'], context_npc)

        # 2. Spawn Result
        spawn_msg = ""
        if 'spawn_item' in combo:
            new_id = combo['spawn_item']
            if new_id in self.game.objects:
                self.game.objects[new_id]['location'] = LOC_INVENTORY
                spawn_msg = f"Hergestellt: {self.game.objects[new_id][ATTR_NAME]}"
        
        # 3. Text Feedback (Priorität: Custom Message > Spawn Message > Default)
        if 'message' in combo:
            return combo['message']
        
        if spawn_msg: return spawn_msg
            
        return "Aktion ausgeführt."

    def _find_obj_or_npc_by_name(self, name):
        """Sucht in Objekten UND NPCs."""
        name_clean = name.lower().strip()
        
        # 1. Objekte (Inventar + Raum)
        candidates = [o for o in self.game.objects.values() 
                      if o['location'] in [LOC_INVENTORY, self.game.location]]
        
        # 2. NPCs (Raum)
        npc_candidates = [n for n in self.game.npcs if n['location'] == self.game.location]
        
        all_candidates = candidates + npc_candidates
        
        # Exakt
        for obj in all_candidates:
            if obj[ATTR_NAME].lower() == name_clean: return obj
            
        # Alias
        for obj in all_candidates:
            if any(a.lower() == name_clean for a in obj.get(ATTR_ALIASES, [])): return obj
            
        # Fuzzy
        for obj in all_candidates:
            if name_clean in obj[ATTR_NAME].lower(): return obj
            
        return None