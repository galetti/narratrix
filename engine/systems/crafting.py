# narratrix_engine/engine/systems/crafting.py
from engine.constants import *

class CraftingSystem:
    def __init__(self, game):
        self.game = game

    def perform_combine(self, item1_name, item2_name, verb="use"):
        """
        Versucht, zwei Objekte zu kombinieren oder eine Aktion auszuführen.
        Unterstützt jetzt auch Ressourcen und Stationen.
        """
        # 1. Objekte finden (via Namen)
        # Wir nutzen eine einfache Suche im Inventar und im Raum (für Stationen)
        # Da wir Namen bekommen, müssen wir die IDs finden.
        
        item1 = self._find_obj_by_name(item1_name)
        item2 = self._find_obj_by_name(item2_name)
        
        if not item1 or not item2:
            return "Ich weiß nicht, was du kombinieren willst."

        # Identifiziere IDs
        id1 = item1[ATTR_ID]
        id2 = item2[ATTR_ID]
        
        # Suche nach passendem Rezept in den Kombinationen
        # Wir suchen nach einem Rezept, das diese beiden Items als Zutaten hat ODER
        # eins als Zutat und eins als Station.
        
        possible_recipes = []
        for combo in self.game.combinations:
            if combo.get('verb') != verb: continue
            
            recipe_items = combo.get('items', [])
            ingredients = combo.get('ingredients', {}) # NEU: Dict {id: count}
            station = combo.get('station')             # NEU: Station ID
            
            # Fall A: Klassische "Item + Item" Logik (Legacy Support)
            if recipe_items:
                if set(recipe_items) == {id1, id2}:
                    possible_recipes.append(combo)
                    continue

            # Fall B: Erweitertes Crafting (Zutaten + Station)
            # Wir prüfen, ob id1 und id2 in den Zutaten ODER als Station vorkommen.
            # Mindestens eine Interaktion muss passen.
            
            # Szenario: "Benutze Metall mit Werkbank"
            # Zutat: Metall, Station: Werkbank
            is_station_match = (station == id1 or station == id2)
            is_ingredient_match = (id1 in ingredients or id2 in ingredients)
            
            if is_station_match or is_ingredient_match:
                # Wir merken uns das Rezept und prüfen später die VOLLSTÄNDIGEN Bedingungen
                possible_recipes.append(combo)

        if not possible_recipes:
            return "Das scheint nicht zu funktionieren."

        # Versuche Rezepte auszuführen
        for recipe in possible_recipes:
            success, msg = self._try_craft(recipe, [item1, item2])
            if success:
                return msg
            elif msg: # Fehlermeldung (z.B. "Fehlt noch Draht")
                return msg

        return "Das funktioniert so nicht."

    def _try_craft(self, recipe, interacting_items):
        """
        Prüft Bedingungen für ein komplexes Rezept und führt es aus.
        """
        # 1. Prüfe Station (falls benötigt)
        required_station = recipe.get('station')
        if required_station:
            # Einer der interagierenden Gegenstände MUSS die Station sein,
            # ODER der Spieler steht davor (im Raum).
            station_present = False
            
            # Check interaction
            for item in interacting_items:
                if item[ATTR_ID] == required_station:
                    station_present = True
                    break
            
            # Check environment (falls Station im Raum ist)
            if not station_present:
                station_obj = self.game.objects.get(required_station)
                if station_obj and station_obj['location'] == self.game.location:
                    station_present = True
            
            if not station_present:
                # Rezept passt theoretisch, aber Station fehlt
                # Wir geben hier False zurück, damit evtl. andere Rezepte geprüft werden,
                # aber eigentlich ist es ein logischer Fehlschlag.
                return False, None 

        # 2. Prüfe Zutaten (Inventar)
        ingredients = recipe.get('ingredients', {})
        # Legacy Support: 'items' Liste in Dict wandeln
        if 'items' in recipe and not ingredients:
            ingredients = {i_id: 1 for i_id in recipe['items']}

        inventory_ids = [o[ATTR_ID] for o in self.game.objects.values() if o['location'] == LOC_INVENTORY]
        
        missing = []
        for ing_id, count in ingredients.items():
            # Zähle verfügbare Items (oder Stack-Größe)
            available = 0
            # Check Inventar
            item = self.game.objects.get(ing_id)
            if not item: continue
            
            # Ist es im Inventar?
            if item['location'] == LOC_INVENTORY:
                # Wenn es ein stapelbares Item ist (Resource), hat es ein 'count' Attribut
                if item.get('is_resource'):
                    available = item.get('count', 1)
                else:
                    available = 1 # Unikate Items zählen als 1
            
            # Auch interagierende Items zählen (selbst wenn nicht im Inv, z.B. Station-Input)
            for i_item in interacting_items:
                if i_item[ATTR_ID] == ing_id and i_item['location'] != LOC_INVENTORY:
                     if i_item.get('is_resource'): available += i_item.get('count', 1)
                     else: available += 1

            if available < count:
                item_name = self.game.objects[ing_id][ATTR_NAME]
                missing.append(f"{count}x {item_name}")

        if missing:
            return False, f"Dir fehlt noch: {', '.join(missing)}."

        # 3. Ausführung (Crafting)
        # Zutaten entfernen
        for ing_id, count in ingredients.items():
            item = self.game.objects.get(ing_id)
            if not item: continue
            
            # Stationen oder Werkzeuge, die nicht verbraucht werden (`consumable: false`), behalten wir
            if not recipe.get('consume_tools', True) and item.get('is_tool'):
                continue
                
            # Entferne Item
            if item.get('is_resource'):
                # Reduziere Stack
                current = item.get('count', 1)
                if current > count:
                    item['count'] = current - count
                else:
                    item['location'] = LOC_VOID # Aufgebraucht
            else:
                # Unikate Items
                item['location'] = LOC_VOID

        # Ergebnis erzeugen
        return True, self._execute_combination(recipe, interacting_items)

    def _execute_combination(self, combo, objects):
        # 1. Spawn Result
        if 'spawn_item' in combo:
            new_id = combo['spawn_item']
            if new_id in self.game.objects:
                self.game.objects[new_id]['location'] = LOC_INVENTORY
                return f"Hergestellt: {self.game.objects[new_id][ATTR_NAME]}"
        
        # 2. Text Feedback
        if 'message' in combo:
            return combo['message']
            
        # 3. Generische Effekte
        if 'effect' in combo:
            # Context NPC ist hier None, da Crafting meist keine Person involviert
            self.game.effects.process(combo['effect'])
            return "Aktion ausgeführt."

        return "Erledigt."

    def _find_obj_by_name(self, name):
        """Hilfsfunktion: Findet Objekt im Scope (Inv + Raum)."""
        name_clean = name.lower().strip()
        candidates = [o for o in self.game.objects.values() 
                      if o['location'] in [LOC_INVENTORY, self.game.location]]
        
        # Exakter Match
        for obj in candidates:
            if obj[ATTR_NAME].lower() == name_clean: return obj
            
        # Alias Match
        for obj in candidates:
            if any(a.lower() == name_clean for a in obj.get(ATTR_ALIASES, [])): return obj
            
        # Fuzzy / Substring
        for obj in candidates:
            if name_clean in obj[ATTR_NAME].lower(): return obj
            
        return None