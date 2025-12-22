# engine/systems/crafting.py
from engine.constants import *

class CraftingSystem:
    def __init__(self, game):
        self.game = game

    def perform_combine(self, item1_name, item2_name):
        # 1. Sammle alle Objekte für die Suche (Inventar + Raum + Offene Container rekursiv)
        accessible_objs = self._get_accessible_objects()

        # Helper zum Finden von Objekten per Name
        def find_in_list(name, lst):
            search = name.lower()
            return next((o for o in lst if search in o[ATTR_NAME].lower() or any(search in a for a in o.get(ATTR_ALIASES, []))), None)

        obj1 = find_in_list(item1_name, accessible_objs)
        obj2 = find_in_list(item2_name, accessible_objs)

        if not obj1: return f"Ich finde '{item1_name}' hier nicht."
        if not obj2: return f"Ich finde '{item2_name}' hier nicht."

        # Rezepte durchsuchen (Common + Chapter merged)
        combinations = self.game.config.get('combinations', [])
        
        for recipe in combinations:
            needed_items = recipe['items']
            
            # A. Zutaten prüfen (Sind obj1 und obj2 die richtigen?)
            if (obj1[ATTR_ID] in needed_items and obj2[ATTR_ID] in needed_items) and (obj1[ATTR_ID] != obj2[ATTR_ID]):
                
                # B. Werkzeuge prüfen (Sind alle Tools da?)
                needed_tools = recipe.get('tools', [])
                missing_tools = []
                for tool_id in needed_tools:
                    # Tool muss im Inventar oder equipped sein (hier: accessible)
                    if not any(o[ATTR_ID] == tool_id for o in accessible_objs):
                        # Namen für Fehlermeldung suchen (falls möglich)
                        tool_name = tool_id
                        if tool_id in self.game.objects:
                            tool_name = self.game.objects[tool_id][ATTR_NAME]
                        missing_tools.append(tool_name)
                
                if missing_tools:
                    return f"Das klappt so nicht. Du benötigst: {', '.join(missing_tools)}."

                # C. Crafting Erfolg!
                
                # 1. Zielort bestimmen
                target_location = LOC_INVENTORY
                loc1 = obj1['location']; parent1 = self.game.objects.get(loc1)
                loc2 = obj2['location']; parent2 = self.game.objects.get(loc2)
                
                # Konsum-Logik auswerten
                consume_target = recipe.get('consume', True) # Default: Alles weg
                
                objs_to_remove = []
                
                if consume_target is True:
                    objs_to_remove = [obj1, obj2]
                elif isinstance(consume_target, list):
                    if obj1[ATTR_ID] in consume_target: objs_to_remove.append(obj1)
                    if obj2[ATTR_ID] in consume_target: objs_to_remove.append(obj2)
                
                # Wo entsteht das Ergebnis?
                final_container = None
                
                # Check: Ist eine Zutat ein Container, der NICHT gelöscht wird?
                if obj1 not in objs_to_remove and obj1.get('type') == TYPE_CONTAINER: final_container = obj1
                elif obj2 not in objs_to_remove and obj2.get('type') == TYPE_CONTAINER: final_container = obj2
                
                if final_container:
                    target_location = final_container[ATTR_ID]
                else:
                    # Fallback auf Ursprungsort (nur wenn der Container noch existiert/gültig ist)
                    if parent1 and parent1['location'] != LOC_VOID: target_location = loc1
                    elif parent2 and parent2['location'] != LOC_VOID: target_location = loc2

                # 2. Zutaten entfernen
                for o in objs_to_remove:
                    o['location'] = LOC_VOID

                # 3. Ergebnis erzeugen
                res_id = recipe.get('result')
                if res_id:
                    if res_id in self.game.objects:
                        res_obj = self.game.objects[res_id]
                        res_obj['location'] = target_location
                        
                        # Temperatur Transfer
                        t1 = obj1.get(ATTR_TEMP, 20); t2 = obj2.get(ATTR_TEMP, 20)
                        res_obj[ATTR_TEMP] = max(t1, t2)
                        
                        return recipe['message']
                    else:
                        return f"Systemfehler: Ergebnis-Item '{res_id}' nicht gefunden."
                else:
                    return recipe['message']
        
        return "Das lässt sich nicht sinnvoll kombinieren."

    def _get_accessible_objects(self):
        """Hilfsmethode: Alle greifbaren Objekte (Inv + Raum + Offene Container, rekursiv)."""
        accessible = []
        
        # Rekursive Suchfunktion
        def scan_recursive(parent_id):
            # Finde alle Objekte, deren Ort 'parent_id' ist
            contents = [o for o in self.game.objects.values() if o['location'] == parent_id]
            for obj in contents:
                accessible.append(obj)
                # Wenn es ein offener Container oder eine Oberfläche ist -> Tiefer scannen
                if obj.get('type') in [TYPE_CONTAINER, TYPE_SURFACE] and obj.get('is_open', True):
                    scan_recursive(obj[ATTR_ID])

        # 1. Startpunkt: Inventar
        scan_recursive(LOC_INVENTORY)
        
        # 2. Startpunkt: Aktueller Raum
        scan_recursive(self.game.location)
        
        return accessible
