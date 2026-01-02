import copy
import re
import threading
from engine.constants import *

from engine.systems.crafting import CraftingSystem
from engine.systems.pathfinder import Pathfinder
from engine.systems.ai import AISystem
from engine.systems.object_behavior import ObjectBehaviorSystem
from engine.systems.acoustics import AcousticsSystem 

class GameState:
    def __init__(self, config, silent=False):
        self.config = config
        self.silent = silent 
        self.time = 0
        self.logs = []
        self.lock = threading.RLock()
        
        self.persistent_flags = set() 
        self.pending_chapter_load = None 
        
        self.hidden_in = None 
        
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
        
        for npc in self.npcs:
            if 'states' in npc:
                if 'state' not in npc:
                    npc['state'] = npc.get('initial_state', list(npc['states'].keys())[0])
                self._hydrate_npc(npc)
                npc['_last_hydrated_state'] = npc['state']
            else:
                if not silent: 
                    print(f"[WARN] NPC '{npc.get('name')}' hat keine 'states' Definition.")

        for obj in self.objects.values():
            if ATTR_TEMP not in obj: obj[ATTR_TEMP] = 20
            if ATTR_MATTER not in obj: obj[ATTR_MATTER] = MATTER_SOLID

        self.crafting = CraftingSystem(self)
        self.pathfinder = Pathfinder(self)
        self.ai = AISystem(self)
        self.object_behavior = ObjectBehaviorSystem(self)
        self.acoustics = AcousticsSystem(self)

    def _hydrate_npc(self, npc):
        current_state = npc.get('state')
        state_data = npc.get('states', {}).get(current_state)
        
        if not state_data: return

        if 'behavior' in state_data:
            for k, v in state_data['behavior'].items(): npc[k] = v 
        if 'visuals' in state_data:
            for k, v in state_data['visuals'].items(): npc[k] = v 
        if 'dialogue' in state_data:
            if 'dialogue' not in npc: npc['dialogue'] = {}
            npc['dialogue'][current_state] = state_data['dialogue']

    def _synchronize_npcs(self):
        for npc in self.npcs:
            if 'states' in npc:
                current = npc.get('state')
                last = npc.get('_last_hydrated_state')
                if current != last:
                    self._hydrate_npc(npc)
                    npc['_last_hydrated_state'] = current

    def clone(self):
        new_state = GameState(self.config, silent=True)
        with self.lock:
            new_state.time = self.time
            new_state.location = self.location
            new_state.stability = self.stability
            new_state.game_over = self.game_over
            new_state.knowledge = copy.deepcopy(self.knowledge)
            new_state.persistent_flags = copy.deepcopy(self.persistent_flags)
            new_state.hidden_in = self.hidden_in 
            new_state.rooms = copy.deepcopy(self.rooms)
            new_state.npcs = copy.deepcopy(self.npcs)
            new_state.matrix = copy.deepcopy(self.matrix)
            new_state.objects = copy.deepcopy(self.objects)
            new_state.inventory = copy.deepcopy(self.inventory)
        return new_state

    def render_room_desc(self, room_id):
        if self.hidden_in:
            container = self.objects.get(self.hidden_in)
            c_name = container[ATTR_NAME] if container else "einem Versteck"
            return f"Du bist versteckt in {c_name}. Durch einen Spalt siehst du den Raum."

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
            self._synchronize_npcs()
            
            room = self.rooms.get(self.location)
            partner_name = None; partner_img = None
            if self.dialogue_active and self.dialogue_partner:
                partner_name = self.dialogue_partner[ATTR_NAME]; partner_img = self.dialogue_partner.get('img')
                
            return {
                "time": self.time, "stability": self.stability, "game_over": self.game_over,
                "pending_chapter_load": self.pending_chapter_load,
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
        return self.crafting.perform_combine(item1_name, item2_name)

    def find_path(self, start, target):
        return self.pathfinder.find_path(start, target)

    def get_direction_to(self, target_room_id):
        return self.pathfinder.get_direction_to(self.location, target_room_id)

    def _check_trigger_condition(self, node):
        if node.get('triggered', False): return False
        trigger_type = node.get('trigger', 'time')
        
        if trigger_type == 'time': 
            return self.time >= node.get('trigger_time', 99999)
        elif trigger_type == 'relative':
            parent_id = node.get('parent_id')
            delay = node.get('delay', 0)
            parent = next((n for n in self.matrix if n['id'] == parent_id), None)
            if parent and parent.get('triggered', False): 
                return self.time >= (parent.get('triggered_at', 0) + delay)
        elif trigger_type == 'condition':
            cond = node.get('condition', {})
            c_type = cond.get('type')
            
            if c_type == 'knowledge': 
                return cond.get('value') in self.knowledge
            elif c_type == 'item_location':
                item_id = cond.get('item')
                loc = cond.get('location')
                obj = self.objects.get(item_id)
                return obj and obj['location'] == loc
            # NEU: Check auf Spieler-Position
            elif c_type == 'location':
                target_loc = cond.get('value')
                return self.location == target_loc
                
        return False

    def tick(self, minutes):
        self.time += minutes
        
        # Physik
        for obj in self.objects.values():
            if ATTR_TEMP in obj:
                current = obj[ATTR_TEMP]; target = 20
                if current != target:
                    diff = target - current
                    if abs(change := diff * 0.1) < 0.5: obj[ATTR_TEMP] = target
                    else: obj[ATTR_TEMP] += change
        
        # Events
        for node in self.matrix:
            if self._check_trigger_condition(node):
                node['triggered'] = True
                node['triggered_at'] = self.time
                
                if 'effects' in node:
                    effects = node['effects']
                    if not isinstance(effects, list): effects = [effects]
                    for eff in effects:
                        e_type = eff.get('type')
                        if e_type == 'set_npc_state':
                            target_name = eff.get('npc')
                            new_state = eff.get('value')
                            target = next((n for n in self.npcs if n[ATTR_NAME] == target_name or target_name in n.get(ATTR_ALIASES, [])), None)
                            if target: target['state'] = new_state
                        elif e_type == 'learn':
                            fact = eff.get('fact')
                            if fact: self.add_knowledge(fact)
                
                if node.get('type') == 'chapter_switch':
                    target_chapter = node.get('target_chapter')
                    self.log('story', node.get('description', 'Kapitelwechsel...'))
                    self.pending_chapter_load = target_chapter
                    return 

                if node.get('type') == 'conversation':
                    self._process_conversation_event(node)
                    continue

                origin = node.get('origin_id')
                if origin == self.location:
                    self.log('event', f"EVENT: {node['title']}")
                    self.log('story', node['description'])
                else:
                    vol, direction = self.acoustics.get_audibility_info(origin, self.location)
                    if vol > 0.1:
                        sound_txt = node.get('sound_msg', "Geräusch.")
                        msg_prefix = f"Du hörst aus {direction}:" if direction != "hier" else "Hier ertönt:"
                        self.log('event', f"{msg_prefix} {sound_txt}")
                
                target_id = node.get('target_obj_id')
                if target_id:
                    target = self.objects.get(target_id)
                    if target and target.get('state') == STATE_SABOTAGED:
                        self.stability -= node.get('penalty', 0)
                        if 'fail_text' in node: self.log('alarm', f"ALARM: {node['fail_text']}")
                    else:
                        if 'success_text' in node: self.log('success', f"STATUS: {node['success_text']}")

        self.ai.process_all_npcs()
        self.object_behavior.process_all_objects()

        if self.stability <= 0: 
            self.log('alarm', "GAME OVER: STATION KRITISCH.")
            self.game_over = True

    def _process_conversation_event(self, node):
        origin = node.get('origin_id')
        actors = node.get('actors', [])
        content = node.get('content', [])
        
        volume, direction = self.acoustics.get_audibility_info(origin, self.location)
        
        if self.location == origin:
            if self.hidden_in:
                self.log('story', f"(Du lauschst aus deinem Versteck...)")
            self.log('event', f"GESPRÄCH: {', '.join(actors)}")
            for line in content:
                speaker = line.get('speaker', '???')
                text = line.get('text', '...')
                self.log('character', f"{speaker}: \"{text}\"")
                
        elif volume > 0.1:
            quality = "gedämpfte" if volume < 0.6 else "klare"
            self.log('event', f"Du hörst {quality} Stimmen aus {direction}...")
            
            for line in content:
                text = line.get('text', '')
                if volume < 0.4:
                    words = text.split()
                    fragment = "...".join([w for i, w in enumerate(words) if i % 3 == 0])
                    self.log('story', f"Unbekannt: \"...{fragment}...\"")
                else:
                    speaker = line.get('speaker', '???')
                    self.log('story', f"{speaker}: \"{text}\"")