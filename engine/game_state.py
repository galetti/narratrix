import copy
import re
import threading
from engine.constants import *

# Sub-Systeme
from engine.systems.crafting import CraftingSystem
from engine.systems.pathfinder import Pathfinder
from engine.systems.ai import AISystem
from engine.systems.object_behavior import ObjectBehaviorSystem

class GameState:
    def __init__(self, config, silent=False):
        self.config = config
        self.silent = silent 
        self.time = 0
        self.logs = []
        self.lock = threading.RLock()
        
        # Layer 3: Persistente Daten & System Flags
        self.persistent_flags = set() 
        self.pending_chapter_load = None 
        
        # Startraum ermitteln
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

        # Tiefe Kopien der Daten, um den Config-State nicht zu verändern
        self.rooms = copy.deepcopy(config['rooms'])
        self.npcs = copy.deepcopy(config['npcs'])
        self.matrix = copy.deepcopy(config['narrative_matrix'])
        self.objects = copy.deepcopy(config['objects'])
        
        # Initialisiere NPCs (Strict Hydration)
        for npc in self.npcs:
            if 'states' in npc:
                if 'state' not in npc:
                    # Setze initialen State aus Config oder nehme den ersten
                    npc['state'] = npc.get('initial_state', list(npc['states'].keys())[0])
                self._hydrate_npc(npc)
                npc['_last_hydrated_state'] = npc['state']
            else:
                if not silent: 
                    print(f"[WARN] NPC '{npc.get('name')}' hat keine 'states' Definition. Ignoriere AI/Visuals.")

        # Physik-Initialisierung
        for obj in self.objects.values():
            if ATTR_TEMP not in obj: obj[ATTR_TEMP] = 20
            if ATTR_MATTER not in obj: obj[ATTR_MATTER] = MATTER_SOLID

        # --- INITIALISIERUNG DER SYSTEME ---
        self.crafting = CraftingSystem(self)
        self.pathfinder = Pathfinder(self)
        self.ai = AISystem(self)
        self.object_behavior = ObjectBehaviorSystem(self)

    def _hydrate_npc(self, npc):
        """
        Kopiert Daten aus der hierarchischen 'states'-Struktur in die flache NPC-Struktur.
        """
        current_state = npc.get('state')
        state_data = npc.get('states', {}).get(current_state)
        
        if not state_data: return

        # 1. Behavior (AI)
        if 'behavior' in state_data:
            for k, v in state_data['behavior'].items():
                npc[k] = v 
        
        # 2. Visuals (Anzeige)
        if 'visuals' in state_data:
            for k, v in state_data['visuals'].items():
                npc[k] = v 
        
        # 3. Dialogue (Interaktion)
        if 'dialogue' in state_data:
            if 'dialogue' not in npc: npc['dialogue'] = {}
            npc['dialogue'][current_state] = state_data['dialogue']

    def _synchronize_npcs(self):
        """Prüft auf Zustandsänderungen und aktualisiert die Daten."""
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

    # --- DELEGATION ZU SYSTEMEN ---
    
    def perform_combine(self, item1_name, item2_name):
        return self.crafting.perform_combine(item1_name, item2_name)

    def find_path(self, start, target):
        return self.pathfinder.find_path(start, target)

    def get_direction_to(self, target_room_id):
        return self.pathfinder.get_direction_to(self.location, target_room_id)

    # --- SIMULATION LOOP ---
    
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
                
        return False

    def tick(self, minutes):
        self.time += minutes
        
        # Physik (Temperatur-Angleichung)
        for obj in self.objects.values():
            if ATTR_TEMP in obj:
                current = obj[ATTR_TEMP]
                target = 20 # Raumtemperatur
                if current != target:
                    diff = target - current
                    change = diff * 0.1
                    if abs(change) < 0.5: obj[ATTR_TEMP] = target
                    else: obj[ATTR_TEMP] += change
        
        # Events verarbeiten
        for node in self.matrix:
            if self._check_trigger_condition(node):
                node['triggered'] = True
                node['triggered_at'] = self.time
                
                # --- EVENT EFFECTS ENGINE ---
                # Führt Effekte aus (z.B. NPC-Status setzen)
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
                
                # Spezialfall: Kapitelwechsel
                if node.get('type') == 'chapter_switch':
                    target_chapter = node.get('target_chapter')
                    self.log('story', node.get('description', 'Kapitelwechsel...'))
                    self.pending_chapter_load = target_chapter
                    return # Stop Tick Processing, GUI übernimmt

                # Standard Event-Ausgabe
                origin = node.get('origin_id')
                if origin == self.location:
                    self.log('event', f"EVENT: {node['title']}")
                    self.log('story', node['description'])
                else:
                    # Geräusch aus der Ferne
                    sound_dir = self.get_direction_to(origin)
                    sound_txt = node.get('sound_msg', "Geräusch.")
                    if sound_dir: 
                        self.log('event', f"Du hörst aus {sound_dir}: {sound_txt}")
                    else: 
                        self.log('event', f"Irgendwo in der Ferne: {sound_txt}")
                
                # Ziel-Objekt Prüfung (Schaden an der Station)
                target_id = node.get('target_obj_id')
                if target_id:
                    target = self.objects.get(target_id)
                    if target and target.get('state') == STATE_SABOTAGED:
                        self.stability -= node.get('penalty', 0)
                        if 'fail_text' in node: self.log('alarm', f"ALARM: {node['fail_text']}")
                    else:
                        if 'success_text' in node: self.log('success', f"STATUS: {node['success_text']}")

        # System Updates
        self.ai.process_all_npcs()
        self.object_behavior.process_all_objects()

        if self.stability <= 0: 
            self.log('alarm', "GAME OVER: STATION KRITISCH.")
            self.game_over = True