import copy
import re
from collections import deque
from utils import rng
import threading
from engine.constants import *

class GameState:
    def __init__(self, config, silent=False):
        self.config = config
        self.silent = silent 
        self.time = 0
        self.logs = []
        self.lock = threading.RLock()
        
        start_room = config.get('meta', {}).get('start_room')
        if not start_room and 'start' in config['rooms']: start_room = 'start'
        if not start_room or start_room not in config['rooms']:
            start_room = list(config['rooms'].keys())[0] if config['rooms'] else LOC_VOID

        self.location = start_room
        self.inventory = []
        self.stability = 100
        self.game_over = False
        self.last_subject_id = None
        self.disambiguation = None 
        self.pending_interaction = None
        self.dialogue_active = False
        self.dialogue_partner = None
        self.knowledge = set()

        self.rooms = copy.deepcopy(config['rooms'])
        self.npcs = copy.deepcopy(config['npcs'])
        self.matrix = copy.deepcopy(config['narrative_matrix'])
        self.objects = copy.deepcopy(config['objects'])
        
        for obj in self.objects.values():
            if ATTR_TEMP not in obj: obj[ATTR_TEMP] = 20
            if ATTR_MATTER not in obj: obj[ATTR_MATTER] = MATTER_SOLID

    def clone(self):
        new_state = GameState(self.config, silent=True)
        with self.lock:
            new_state.time = self.time
            new_state.location = self.location
            new_state.stability = self.stability
            new_state.game_over = self.game_over
            new_state.knowledge = copy.deepcopy(self.knowledge)
            new_state.rooms = copy.deepcopy(self.rooms)
            new_state.npcs = copy.deepcopy(self.npcs)
            new_state.matrix = copy.deepcopy(self.matrix)
            new_state.objects = copy.deepcopy(self.objects)
            new_state.inventory = copy.deepcopy(self.inventory)
        return new_state

    def render_room_desc(self, room_id):
        room = self.rooms.get(room_id)
        if not room: return f"ERROR: Raum '{room_id}' nicht gefunden."
        text = room[ATTR_DESC]
        def replace_match(match):
            key = match.group(1)
            obj = self.objects.get(key)
            if not obj: return f"ERROR:{key}"
            display_text = obj[ATTR_NAME]
            if obj.get('state') == STATE_SABOTAGED: display_text += " [SABOTIERT]"
            elif obj.get('state') == STATE_BROKEN: display_text += " [DEFEKT]"
            elif obj.get('is_container'):
                if obj.get('is_open'): display_text += " [OFFEN]"
                else: display_text += " [VERSCHLOSSEN]"
            return display_text
        return re.sub(r"\{(\w+)\}", replace_match, text)

    def log(self, type_str, text):
        if self.silent: return 
        with self.lock:
            self.logs.append({"type": type_str, "text": text, "turn": self.time})

    def get_logs(self):
        with self.lock: return list(self.logs)

    def get_snapshot(self):
        with self.lock:
            room = self.rooms.get(self.location)
            partner_name = None; partner_img = None
            if self.dialogue_active and self.dialogue_partner:
                partner_name = self.dialogue_partner[ATTR_NAME]; partner_img = self.dialogue_partner.get('img')
            return {
                "time": self.time, "stability": self.stability, "game_over": self.game_over,
                "room_name": room[ATTR_NAME] if room else "Unbekannt",
                "room_img": room.get('img', '???') if room else '???',
                "dialogue_active": self.dialogue_active,
                "dialogue_header": f"GESPRÄCH: {partner_name.upper()}" if partner_name else "",
                "dialogue_img": partner_img if partner_img else (partner_name if partner_name else "???"),
                "logs": list(self.logs)
            }

    def get_room(self, room_id): return self.rooms.get(room_id)
    def add_knowledge(self, fact_id): 
        if fact_id not in self.knowledge: self.knowledge.add(fact_id)

    def perform_combine(self, item1_name, item2_name):
        # 1. Sammle alle Objekte für die Suche
        accessible_objs = []
        inv_objs = [o for o in self.objects.values() if o['location'] == LOC_INVENTORY]
        accessible_objs.extend(inv_objs)
        for o in inv_objs:
            if o.get('type') in [TYPE_CONTAINER, TYPE_SURFACE] and o.get('is_open', True):
                contents = [sub for sub in self.objects.values() if sub['location'] == o['id']]
                accessible_objs.extend(contents)

        room_objs = [o for o in self.objects.values() if o['location'] == self.location]
        accessible_objs.extend(room_objs)
        for o in room_objs:
            if o.get('type') in [TYPE_SURFACE, TYPE_CONTAINER] and o.get('is_open', True):
                contents = [sub for sub in self.objects.values() if sub['location'] == o['id']]
                accessible_objs.extend(contents)

        def find_in_list(name, lst):
            search = name.lower()
            return next((o for o in lst if search in o[ATTR_NAME].lower() or any(search in a for a in o.get(ATTR_ALIASES, []))), None)

        obj1 = find_in_list(item1_name, accessible_objs)
        obj2 = find_in_list(item2_name, accessible_objs)

        if not obj1: return f"Ich finde '{item1_name}' hier nicht."
        if not obj2: return f"Ich finde '{item2_name}' hier nicht."

        combinations = self.config.get('combinations', [])
        for recipe in combinations:
            needed = recipe['items']
            if (obj1[ATTR_ID] in needed and obj2[ATTR_ID] in needed) and (obj1[ATTR_ID] != obj2[ATTR_ID]):
                # Erfolg!
                
                # A. Ziel-Container bestimmen
                target_location = LOC_INVENTORY
                
                # Check obj1
                loc1 = obj1['location']
                parent1 = self.objects.get(loc1)
                
                # Check obj2
                loc2 = obj2['location']
                parent2 = self.objects.get(loc2)

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
                if res_id and res_id in self.objects:
                    res_obj = self.objects[res_id]
                    res_obj['location'] = target_location
                    
                    t1 = obj1.get(ATTR_TEMP, 20); t2 = obj2.get(ATTR_TEMP, 20)
                    res_obj[ATTR_TEMP] = max(t1, t2)
                    
                    return recipe['message']
                else:
                    return "Fehler: Ergebnis-Item nicht definiert."
        
        return "Das lässt sich nicht sinnvoll kombinieren."

    # --- SENSORIK & WEGFINDUNG ---
    def find_path(self, start_room_id, target_room_id):
        if start_room_id == target_room_id: return []
        queue = deque([[start_room_id]]); visited = set([start_room_id])
        while queue:
            path = queue.popleft(); current = path[-1]
            if current == target_room_id: return path[1:]
            room_data = self.rooms.get(current)
            if room_data:
                for exit_id in room_data['exits'].values():
                    if exit_id not in visited and exit_id in self.rooms:
                        visited.add(exit_id); new_path = list(path); new_path.append(exit_id); queue.append(new_path)
        return None
        
    def get_direction_to(self, target_room_id):
        if self.location == target_room_id: return "hier"
        path = self.find_path(self.location, target_room_id)
        if not path: return None
        next_step = path[0]; current_room = self.rooms[self.location]
        for direction, r_id in current_room['exits'].items():
            if r_id == next_step:
                trans = {"north": "Norden", "south": "Süden", "east": "Osten", "west": "Westen", "up": "Oben", "down": "Unten"}
                return trans.get(direction, direction)
        return "irgendwo"

    def _check_trigger_condition(self, node):
        if node.get('triggered', False): return False
        trigger_type = node.get('trigger', 'time')
        if trigger_type == 'time': return self.time >= node.get('trigger_time', 99999)
        elif trigger_type == 'relative':
            parent_id = node.get('parent_id'); delay = node.get('delay', 0)
            parent = next((n for n in self.matrix if n['id'] == parent_id), None)
            if parent and parent.get('triggered', False): return self.time >= (parent.get('triggered_at', 0) + delay)
        elif trigger_type == 'condition':
            cond = node.get('condition', {}); c_type = cond.get('type')
            if c_type == 'knowledge': return cond.get('value') in self.knowledge
            elif c_type == 'item_location':
                item_id = cond.get('item'); loc = cond.get('location')
                obj = self.objects.get(item_id)
                return obj and obj['location'] == loc
        return False

    def tick(self, minutes):
        self.time += minutes
        for obj in self.objects.values():
            if ATTR_TEMP in obj:
                current = obj[ATTR_TEMP]; target = 20
                if current != target:
                    diff = target - current; change = diff * 0.1
                    if abs(change) < 0.5: obj[ATTR_TEMP] = target
                    else: obj[ATTR_TEMP] += change
                        
        for node in self.matrix:
            if self._check_trigger_condition(node):
                node['triggered'] = True; node['triggered_at'] = self.time
                origin = node.get('origin_id')
                if origin == self.location:
                    self.log('event', f"EVENT: {node['title']}"); self.log('story', node['description'])
                else:
                    sound_dir = self.get_direction_to(origin); sound_txt = node.get('sound_msg', "Geräusch.")
                    if sound_dir: self.log('event', f"Du hörst aus {sound_dir}: {sound_txt}")
                    else: self.log('event', f"Irgendwo in der Ferne: {sound_txt}")
                target_id = node.get('target_obj_id')
                if target_id:
                    target = self.objects.get(target_id)
                    if target and target.get('state') == STATE_SABOTAGED:
                        self.stability -= node.get('penalty', 0)
                        if 'fail_text' in node: self.log('alarm', f"ALARM: {node['fail_text']}")
                    else:
                        if 'success_text' in node: self.log('success', f"STATUS: {node['success_text']}")

        for npc in self.npcs:
            if not self.silent and npc == self.dialogue_partner and self.dialogue_active: continue
            self.process_npc_ai(npc)

        if self.stability <= 0: self.log('alarm', "GAME OVER: STATION KRITISCH."); self.game_over = True

    def move_npc(self, npc, next_room):
        player_sees_movement = (self.location == npc['location']) or (self.location == next_room)
        old_loc = npc['location']; npc['location'] = next_room
        if player_sees_movement and not self.silent:
            direction = "davon"; room_data = self.rooms.get(old_loc)
            if room_data:
                for d, r_id in room_data['exits'].items():
                    if r_id == next_room: direction = d; break
            trans = {"north": "Norden", "south": "Süden", "east": "Osten", "west": "Westen", "up": "Oben", "down": "Unten"}
            dir_de = trans.get(direction, direction)
            if self.location == old_loc: self.log('character', f"{npc[ATTR_NAME]} verlässt den Raum nach {dir_de}.")
            elif self.location == next_room: self.log('character', f"{npc[ATTR_NAME]} betritt den Raum.")

    def process_npc_ai(self, npc):
        # HIERARCHISCHE WAHRSCHEINLICHKEITSPRÜFUNG
        
        # 1. Startwert: Globaler Standard
        chance_to_move = AI_CHANCE_MOVE_DEFAULT
        
        # 2. Überschreiben durch NPC-Level Einstellung
        if 'movement_chance' in npc:
            chance_to_move = npc['movement_chance']
            
        # 3. Überschreiben durch State-Level Einstellung
        current_state = npc.get('state', 'default')
        dialogue_conf = npc.get('dialogue', {})
        state_conf = dialogue_conf.get(current_state, {})
        
        if 'movement_chance' in state_conf:
            chance_to_move = state_conf['movement_chance']
            
        # Ausführen
        if not rng.chance(chance_to_move): return 

        affinity_rooms = npc.get(ATTR_AFFINITY, []); current_loc = npc['location']
        if not affinity_rooms: return 
        if current_loc in affinity_rooms:
            if rng.chance(AI_CHANCE_STAY): return 
        target = rng.pick(affinity_rooms)
        if target == current_loc and len(affinity_rooms) > 1: target = rng.pick([r for r in affinity_rooms if r != current_loc])
        path = self.find_path(current_loc, target)
        if path: self.move_npc(npc, path[0])
