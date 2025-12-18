import copy
import time
from engine.constants import *

class GameState:
    def __init__(self, config=None):
        self.config = config if config else {}
        self.location = self.config.get('meta', {}).get('start_room', 'hub')
        # self.inventory als Liste entfernt, ist jetzt Property
        self.knowledge = [] 
        self.game_over = False
        
        # SPIELER STATS
        self.max_carry_weight = 20.0 
        
        # ZEIT SYSTEM
        self.total_minutes = 480 
        self.turn_count = 0
        
        # System-Flags
        self.pending_interaction = None
        self.disambiguation = None
        self.dialogue_active = False
        self.dialogue_partner = None
        self.stability = 100 
        
        self.message_log = []
        
        self.rooms = {}
        self.objects = {}
        self.npcs = []
        self.matrix = []
        self.combinations = [] 
        
        if config:
            self._initialize_world(config)

    @property
    def inventory(self):
        """Dynamische Property: Liefert alle IDs von Items im Inventar."""
        return [oid for oid, obj in self.objects.items() if obj.get('location') == LOC_INVENTORY]

    def _initialize_world(self, config):
        self.rooms = copy.deepcopy(config.get('rooms', {}))
        self.objects = copy.deepcopy(config.get('objects', {}))
        self.npcs = copy.deepcopy(config.get('npcs', []))
        self.matrix = copy.deepcopy(config.get('narrative_matrix', []))
        self.combinations = copy.deepcopy(config.get('combinations', []))
        
        for r_id, room in self.rooms.items():
            room[ATTR_ID] = r_id
            if 'visited' not in room: room['visited'] = False
            
        for o_id, obj in self.objects.items():
            obj[ATTR_ID] = o_id
            if 'location' not in obj: obj['location'] = LOC_VOID

    def get_real_weight(self, obj):
        base_weight = obj.get(ATTR_WEIGHT, 0.0)
        if obj.get('type') in [TYPE_CONTAINER, TYPE_SURFACE]:
            content_weight = 0.0
            contents = [o for o in self.objects.values() if o['location'] == obj[ATTR_ID]]
            for item in contents:
                content_weight += self.get_real_weight(item) 
            return base_weight + content_weight
        return base_weight

    def get_inventory_weight(self):
        total = 0.0
        # Nutzt jetzt die Property self.inventory
        for item_id in self.inventory:
            obj = self.objects.get(item_id)
            if obj:
                total += self.get_real_weight(obj)
        return total

    def reload_world_data(self, new_config):
        print(f"[SYSTEM] Lade Welt-Daten neu für Kapitelwechsel...")
        self.config = new_config
        
        room_states = {rid: {'visited': r.get('visited', False)} for rid, r in self.rooms.items()}
        
        obj_states = {}
        for oid, obj in self.objects.items():
            state_data = {
                'location': obj.get('location'),
                'state': obj.get('state'),
                'is_open': obj.get('is_open'),
                'is_locked': obj.get('is_locked')
            }
            obj_states[oid] = state_data
            
        npc_states = {}
        for npc in self.npcs:
            nid = npc.get(ATTR_ID, npc.get(ATTR_NAME))
            state_data = {
                'location': npc.get('location'),
                'state': npc.get('state'),
                'affinity': npc.get('affinity')
            }
            npc_states[nid] = state_data

        new_rooms = copy.deepcopy(new_config.get('rooms', {}))
        new_objects = copy.deepcopy(new_config.get('objects', {}))
        new_npcs = copy.deepcopy(new_config.get('npcs', []))
        
        self.rooms = new_rooms
        for r_id, room in self.rooms.items():
            room[ATTR_ID] = r_id
            if r_id in room_states: room['visited'] = room_states[r_id]['visited']
            else: room['visited'] = False

        self.objects = new_objects
        for o_id, obj in self.objects.items():
            obj[ATTR_ID] = o_id
            if o_id in obj_states:
                saved = obj_states[o_id]
                if saved['location'] is not None: obj['location'] = saved['location']
                if saved['state'] is not None: obj['state'] = saved['state']
                if saved['is_open'] is not None: obj['is_open'] = saved['is_open']
                if saved['is_locked'] is not None: obj['is_locked'] = saved['is_locked']
            
        self.npcs = new_npcs
        for npc in self.npcs:
            nid = npc.get(ATTR_ID, npc.get(ATTR_NAME))
            if nid in npc_states:
                saved = npc_states[nid]
                if saved['location'] is not None: npc['location'] = saved['location']
                if saved['state'] is not None: npc['state'] = saved['state']
                if saved['affinity'] is not None: npc['affinity'] = saved['affinity']

        self.matrix = copy.deepcopy(new_config.get('narrative_matrix', []))
        self.combinations = copy.deepcopy(new_config.get('combinations', []))
        print("[SYSTEM] Welt-Daten erfolgreich aktualisiert.")

    def log(self, category, text):
        entry = {'type': category, 'text': text}
        self.message_log.append(entry)
    
    def get_logs(self):
        """Gibt alle Logs zurück (für Copy-to-Clipboard etc.)."""
        return self.message_log
        
    def get_room(self, room_id):
        return self.rooms.get(room_id)
        
    def tick(self, minutes=1):
        self.turn_count += 1
        self.total_minutes += minutes 
        if self.total_minutes >= 1440: 
            self.total_minutes -= 1440
        self._check_matrix()
        
    def _check_matrix(self):
        for event in self.matrix:
            if event.get('done', False) and event.get('once', True): continue
            
            trigger = event.get('trigger', {})
            if isinstance(trigger, str):
                t_type = 'knowledge'; t_val = trigger
            else:
                t_type = trigger.get('type'); t_val = trigger.get('value')
            
            triggered = False
            
            if t_type == 'location':
                if self.location == t_val: triggered = True
            elif t_type == 'knowledge':
                if t_val in self.knowledge: triggered = True
            elif t_type == 'item_at':
                item_id = trigger.get('item_id'); loc_id = trigger.get('location_id')
                obj = self.objects.get(item_id)
                if obj and obj['location'] == loc_id: triggered = True
            elif t_type == 'time_ge':
                if self.total_minutes >= int(t_val): triggered = True
            elif t_type == 'weight_ge':
                parts = t_val.split(':')
                if len(parts) == 2:
                    oid = parts[0]; min_w = float(parts[1])
                    obj = self.objects.get(oid)
                    if obj and self.get_real_weight(obj) >= min_w: triggered = True
            elif t_type == 'always':
                triggered = True
                
            if triggered:
                self._execute_event(event)
                if event.get('once', True): event['done'] = True
                    
    def _execute_event(self, event):
        action = event.get('action', {})
        a_type = action.get('type'); val = action.get('value')
        
        if a_type == 'log': self.log('event', val)
        elif a_type == 'add_knowledge': self.add_knowledge(val)
        elif a_type == 'unlock_door':
            obj = self.objects.get(val)
            if obj: 
                obj['is_locked'] = False
                self.log('info', f"(Geräusch: {obj.get(ATTR_NAME, 'Etwas')} entriegelt sich.)")
                
    def add_knowledge(self, fact_id):
        if fact_id not in self.knowledge:
            self.knowledge.append(fact_id)
            self._check_matrix()

    def perform_combine(self, item1_name, item2_name):
        reachable_locs = {self.location, LOC_INVENTORY}
        changed = True
        while changed:
            changed = False
            potential_containers = [
                o for o in self.objects.values() 
                if o['location'] in reachable_locs and o['id'] not in reachable_locs
            ]
            for cont in potential_containers:
                is_accessible = False
                if cont.get('type') == TYPE_SURFACE: is_accessible = True
                elif cont.get('type') == TYPE_CONTAINER and cont.get('is_open'): is_accessible = True
                
                if is_accessible:
                    reachable_locs.add(cont['id'])
                    changed = True

        def find_obj(name):
            search = name.lower().strip()
            for obj in self.objects.values():
                if obj.get('location') not in reachable_locs: continue
                if obj.get(ATTR_NAME, "").lower() == search: return obj
                if search in [a.lower() for a in obj.get('aliases', [])]: return obj
            return None

        obj1 = find_obj(item1_name); obj2 = find_obj(item2_name)
        if not obj1: return f"Ich habe '{item1_name}' hier nicht."
        if not obj2: return f"Ich habe '{item2_name}' hier nicht."

        id1 = obj1[ATTR_ID]; id2 = obj2[ATTR_ID]
        
        # SONDERREGEL WAAGE
        if id1 == 'scale' or id2 == 'scale':
            other = obj2 if id1 == 'scale' else obj1
            if other[ATTR_ID] == 'scale': return "Du kannst die Waage nicht mit sich selbst benutzen."
            
            weight = self.get_real_weight(other)
            return f"Die Anzeige blinkt: {weight:.2f} kg."

        combos = self.combinations if isinstance(self.combinations, list) else []
        
        for recipe in combos:
            ingredients = recipe.get('items', [])
            if set(ingredients) == {id1, id2}:
                msg = recipe.get('message', "Das funktioniert.")
                if not recipe.get('keep_items', False):
                    obj1['location'] = LOC_VOID; obj2['location'] = LOC_VOID
                result_id = recipe.get('result')
                if result_id and result_id in self.objects:
                    self.objects[result_id]['location'] = LOC_INVENTORY
                    msg += f" (Erhalten: {self.objects[result_id][ATTR_NAME]})"
                return msg
        return "Das lässt sich nicht kombinieren."

    def render_room_desc(self, room_id):
        room = self.get_room(room_id)
        if not room: return "Das Nichts."
        return room.get('desc', "")

    def get_snapshot(self):
        current_room = self.get_room(self.location)
        room_name = current_room.get(ATTR_NAME, "Unbekannt") if current_room else "???"
        room_img = current_room.get('img') if current_room else None
        exits = list(current_room.get('exits', {}).keys()) if current_room else []

        inventory_names = []
        for item_id in self.inventory:
            obj = self.objects.get(item_id)
            if obj: inventory_names.append(obj.get(ATTR_NAME, "Unbekanntes Item"))
        
        dialogue_img = None; dialogue_partner_name = None; dialogue_header = "Gespräch"
        if self.dialogue_partner:
            dialogue_partner_name = self.dialogue_partner.get(ATTR_NAME)
            dialogue_img = self.dialogue_partner.get('img')
            dialogue_header = f"Gespräch mit {dialogue_partner_name}"

        chapter_title = self.config.get('meta', {}).get('chapter_title', "Unbekanntes Kapitel")
        
        hours = self.total_minutes // 60
        minutes = self.total_minutes % 60
        time_str = f"{hours:02d}:{minutes:02d}"

        cur_weight = self.get_inventory_weight()
        max_weight = self.max_carry_weight
        
        return {
            'location': self.location,
            'room_name': room_name,
            'room_img': room_img,
            'exits': exits,
            'chapter_title': chapter_title,
            'logs': self.message_log,
            'inventory': inventory_names,
            'stability': self.stability,
            'turn': self.turn_count,
            'time': time_str, 
            'dialogue_active': self.dialogue_active,
            'dialogue_partner': dialogue_partner_name,
            'dialogue_header': dialogue_header,
            'dialogue_img': dialogue_img,
            'game_over': self.game_over,
            'weight_info': f"{cur_weight:.1f}/{max_weight:.1f}kg"
        }

    def clone(self):
        new_state = GameState()
        new_state.config = self.config 
        new_state.location = self.location
        # Inventory property is automatic
        new_state.knowledge = list(self.knowledge)
        new_state.game_over = self.game_over
        new_state.turn_count = self.turn_count
        new_state.total_minutes = self.total_minutes 
        new_state.stability = self.stability
        new_state.max_carry_weight = self.max_carry_weight 
        new_state.rooms = copy.deepcopy(self.rooms)
        new_state.objects = copy.deepcopy(self.objects)
        new_state.npcs = copy.deepcopy(self.npcs)
        new_state.matrix = copy.deepcopy(self.matrix)
        new_state.combinations = self.combinations
        return new_state
