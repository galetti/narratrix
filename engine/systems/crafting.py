# engine/systems/crafting.py
from engine.constants import *

class CraftingSystem:
    def __init__(self, game):
        self.game = game

    def perform_combine(self, item1_name, item2_name):
        # 1. Sammle alle Objekte für die Suche
        accessible_objs = []
        inv_objs = [o for o in self.game.objects.values() if o['location'] == LOC_INVENTORY]
        accessible_objs.extend(inv_objs)
        for o in inv_objs:
            if o.get('type') in [TYPE_CONTAINER, TYPE_SURFACE] and o.get('is_open', True):
                contents = [sub for sub in self.game.objects.values() if sub['location'] == o['id']]
                accessible_objs.extend(contents)

        room_objs = [o for o in self.game.objects.values() if o['location'] == self.game.location]
        accessible_objs.extend(room_objs)
        for o in room_objs:
            if o.get('type') in [TYPE_SURFACE, TYPE_CONTAINER] and o.get('is_open', True):
                contents = [sub for sub in self.game.objects.values() if sub['location'] == o['id']]
                accessible_objs.extend(contents)

        def find_in_list(name, lst):
            search = name.lower()
            return next((o for o in lst if search in o[ATTR_NAME].lower() or any(search in a for a in o.get(ATTR_ALIASES, []))), None)

        obj1 = find_in_list(item1_name, accessible_objs)
        obj2 = find_in_list(item2_name, accessible_objs)

        if not obj1: return f"Ich finde '{item1_name}' hier nicht."
        if not obj2: return f"Ich finde '{item2_name}' hier nicht."

        combinations = self.game.config.get('combinations', [])
        for recipe in combinations:
            needed = recipe['items']
            if (obj1[ATTR_ID] in needed and obj2[ATTR_ID] in needed) and (obj1[ATTR_ID] != obj2[ATTR_ID]):
                # Erfolg!
                target_location = LOC_INVENTORY
                
                loc1 = obj1['location']
                parent1 = self.game.objects.get(loc1)
                
                loc2 = obj2['location']
                parent2 = self.game.objects.get(loc2)

                consume_list = recipe.get('consume', True)

                # B. Konsumieren
                if consume_list is True:
                    if parent1 and parent1['location'] != LOC_VOID: target_location = loc1
                    elif parent2 and parent2['location'] != LOC_VOID: target_location = loc2
                    
                    obj1['location'] = LOC_VOID
                    obj2['location'] = LOC_VOID
                
                elif isinstance(consume_list, list):
                    if obj1[ATTR_ID] in consume_list: obj1['location'] = LOC_VOID
                    if obj2[ATTR_ID] in consume_list: obj2['location'] = LOC_VOID
                    
                    if obj1[ATTR_ID] not in consume_list and obj1.get('type') == TYPE_CONTAINER:
                        target_location = obj1[ATTR_ID]
                    elif obj2[ATTR_ID] not in consume_list and obj2.get('type') == TYPE_CONTAINER:
                        target_location = obj2[ATTR_ID]
                    elif parent1 and parent1['location'] != LOC_VOID:
                        target_location = loc1
                    elif parent2 and parent2['location'] != LOC_VOID:
                        target_location = loc2

                # C. Ergebnis erzeugen
                res_id = recipe.get('result')
                if res_id and res_id in self.game.objects:
                    res_obj = self.game.objects[res_id]
                    res_obj['location'] = target_location
                    
                    t1 = obj1.get(ATTR_TEMP, 20); t2 = obj2.get(ATTR_TEMP, 20)
                    res_obj[ATTR_TEMP] = max(t1, t2)
                    
                    return recipe['message']
                else:
                    return "Fehler: Ergebnis-Item nicht definiert."
        
        return "Das lässt sich nicht sinnvoll kombinieren."