from engine.constants import *

class EventManager:
    """
    Verwaltet dynamische Story-Events mit komplexen Triggern und Effekten.
    Ersetzt die alte Logik in game_state.py.
    """
    def __init__(self, game):
        self.game = game
        self.events = [] # Liste aller geladenen Events

    def load_events(self, events_data):
        """Lädt Events aus der Config."""
        self.events = events_data
        # Initialisierung: 'triggered' Flag setzen, falls nicht vorhanden
        for event in self.events:
            if 'triggered' not in event:
                event['triggered'] = False

    def update(self):
        """Wird jeden Tick aufgerufen. Prüft alle Events."""
        for event in self.events:
            if event.get('triggered', False) and event.get('once', True):
                continue
                
            if self._check_trigger(event):
                self._execute_event(event)

    def _check_trigger(self, event):
        """Prüft, ob ein Event ausgelöst werden soll."""
        trigger_type = event.get('trigger', 'always')
        
        if trigger_type == 'time':
            return self.game.time >= event.get('trigger_time', 99999)
            
        elif trigger_type == 'location':
            # Einfacher Location Check
            target_loc = event.get('location')
            # Fallback falls 'location' Key fehlt aber 'value' genutzt wird (siehe Diskussion vorher)
            if not target_loc: target_loc = event.get('value')
            return self.game.location == target_loc
            
        elif trigger_type == 'condition':
            # Einzelne Bedingung
            return self._evaluate_condition(event.get('condition', {}))
            
        elif trigger_type == 'complex':
            # Komplexe Logik (AND/OR)
            conditions = event.get('conditions', [])
            operator = event.get('operator', 'AND').upper()
            
            if not conditions: return False
            
            results = [self._evaluate_condition(c) for c in conditions]
            
            if operator == 'AND':
                return all(results)
            elif operator == 'OR':
                return any(results)
        
        # Manuelle Trigger (werden durch externe Aufrufe wie Crafting ausgelöst, hier False)
        elif trigger_type == 'manual':
            return False
                
        return False

    def _evaluate_condition(self, cond):
        """Wertet eine einzelne Bedingung aus."""
        c_type = cond.get('type')
        negate = cond.get('not', False)
        result = False

        if c_type == 'knowledge':
            # Hat der Spieler dieses Wissen?
            result = cond.get('value') in self.game.knowledge
            
        elif c_type == 'location':
            # Ist der Spieler an diesem Ort?
            result = self.game.location == cond.get('value')
            
        elif c_type == 'item_location':
            # Ist ein Item an einem bestimmten Ort (z.B. im Inventar)?
            item_id = cond.get('item')
            target_loc = cond.get('location')
            obj = self.game.objects.get(item_id)
            if obj:
                result = obj['location'] == target_loc
                
        elif c_type == 'npc_state':
            # Hat ein NPC einen bestimmten Status?
            npc_id = cond.get('npc') # Kann ID oder Name sein
            state = cond.get('state')
            target = next((n for n in self.game.npcs if n.get('id') == npc_id or n.get('name') == npc_id), None)
            if target:
                result = target.get('state') == state
                
        elif c_type == 'quest_state':
            # Ist eine Quest in einem bestimmten Stadium?
            q_id = cond.get('quest')
            stage = cond.get('stage')
            q_state = self.game.quests.states.get(q_id, {})
            result = q_state.get('status') == 'active' and q_state.get('stage') == stage
            
        elif c_type == 'stability':
            # Stations-Integrität
            threshold = cond.get('value', 0)
            op = cond.get('op', '<')
            if op == '<': result = self.game.stability < threshold
            elif op == '>': result = self.game.stability > threshold
            
        elif c_type == 'event_triggered':
            # Wurde ein anderes Event schon ausgelöst?
            ev_id = cond.get('id')
            target_ev = next((e for e in self.events if e.get('id') == ev_id), None)
            if target_ev:
                result = target_ev.get('triggered', False)

        return not result if negate else result

    def _execute_event(self, event):
        """Führt die Effekte eines Events aus."""
        event['triggered'] = True
        event['triggered_at'] = self.game.time
        
        # 1. Text-Ausgabe (Narrativ)
        if 'description' in event:
            # Nur anzeigen, wenn Spieler am Ort des Geschehens ist oder es global ist
            origin = event.get('origin_id')
            if not origin or origin == self.game.location:
                self.game.log('event', event.get('title', 'EVENT'))
                self.game.log('story', event['description'])
            elif origin:
                # Akustik-Check für entfernte Events
                vol, direction = self.game.acoustics.get_audibility_info(origin, self.game.location)
                if vol > 0.1:
                    sound_msg = event.get('sound_msg', "Ein Geräusch.")
                    self.game.log('event', f"Aus {direction} hörst du: {sound_msg}")

        # 2. Nachricht (System)
        if 'message' in event:
            self.game.log('info', event['message'])

        # 3. Quest Updates
        if 'quest_update' in event:
            q_data = event['quest_update']
            self.game.quests.update_quest(q_data['id'], q_data['stage'])
            
        if 'quest_start' in event:
            self.game.quests.start_quest(event['quest_start'])

        # 4. Generische Effekte
        effects = event.get('effects', [])
        if not isinstance(effects, list): effects = [effects]
        
        for eff in effects:
            self._apply_effect(eff)
            
    def _apply_effect(self, eff):
        e_type = eff.get('type')
        
        if e_type == 'set_npc_state':
            npc_id = eff.get('npc')
            new_state = eff.get('value')
            target = next((n for n in self.game.npcs if n.get('id') == npc_id or n.get('name') == npc_id), None)
            if target: 
                target['state'] = new_state
                self.game.log('info', f"({target['name']} wirkt verändert.)")
            else:
                print(f"[WARN] EventManager: NPC '{npc_id}' nicht gefunden für set_npc_state.")
                
        elif e_type == 'learn':
            fact = eff.get('fact')
            self.game.add_knowledge(fact)
            
        elif e_type == 'damage_stability':
            amount = eff.get('value', 0)
            self.game.stability -= amount
            if amount > 0:
                self.game.log('alarm', f"WARNUNG: Hüllenintegrität gefallen (-{amount}%)")
                
        elif e_type == 'move_npc':
            npc_id = eff.get('npc')
            room_id = eff.get('room')
            # Hier müssen wir aufpassen: game.ai.move_npc erwartet (npc_id, target_room_id)
            # und sucht den NPC anhand der ID.
            if hasattr(self.game.ai, 'move_npc'):
                self.game.ai.move_npc(npc_id, room_id)
            else:
                print("[WARN] EventManager: AI System hat keine move_npc Methode.")
            
        elif e_type == 'spawn_item':
            item_id = eff.get('item')
            location = eff.get('location') # 'inventory' oder Room ID
            obj = self.game.objects.get(item_id)
            if obj:
                if location == 'inventory':
                    obj['location'] = LOC_INVENTORY
                    self.game.log('success', f"Erhalten: {obj['name']}")
                else:
                    obj['location'] = location
            else:
                print(f"[WARN] EventManager: Item '{item_id}' nicht gefunden für spawn_item.")
        
        elif e_type == 'update_object':
            target_id = eff.get('target')
            updates = eff.get('updates', {})
            target = self.game.objects.get(target_id)
            if target:
                target.update(updates)
            else:
                # Fallback: Vielleicht ist es ein NPC, der wie ein Objekt behandelt wird?
                target_npc = next((n for n in self.game.npcs if n.get('id') == target_id), None)
                if target_npc:
                    target_npc.update(updates)
                else:
                    print(f"[WARN] EventManager: Objekt '{target_id}' nicht gefunden für update_object.")
        
        elif e_type == 'trigger_event':
            # Event Chain: Ein Event löst ein anderes aus
            next_event_id = eff.get('id')
            next_event = next((e for e in self.events if e.get('id') == next_event_id), None)
            if next_event:
                self._execute_event(next_event)
            else:
                print(f"[WARN] EventManager: Folge-Event '{next_event_id}' nicht gefunden.")