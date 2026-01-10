# narratrix_engine/engine/systems/event_manager.py
from engine.constants import *

class EventManager:
    """
    Verwaltet dynamische Story-Events.
    Verschlankt: Nutzt jetzt Game.effects für die Ausführung.
    """
    def __init__(self, game):
        self.game = game
        self.events = [] 

    def load_events(self, events_data):
        self.events = events_data
        for event in self.events:
            if 'triggered' not in event:
                event['triggered'] = False

    def update(self):
        for event in self.events:
            if event.get('triggered', False) and not event.get('repeat', False):
                continue
            
            # Bei wiederholbaren Events prüfen wir, ob sie in DIESEM Tick feuern sollen
            # (z.B. Wahrscheinlichkeit oder einfach immer wenn Bedingung wahr ist)
            # Für time trigger: trigger_time ist Startzeit.
            
            if self._check_trigger(event):
                self._execute_event(event)
    
    def trigger_event_by_id(self, event_id):
        """Öffentliche Methode zum manuellen Triggern."""
        target_ev = next((e for e in self.events if e.get('id') == event_id), None)
        if target_ev:
            self._execute_event(target_ev)

    def _check_trigger(self, event):
        trigger_type = event.get('trigger', 'always')
        
        if trigger_type == 'time':
            # Bei Repeat: Feuert es jedes Mal ab trigger_time?
            # Ja, aber wir wollen nicht den Log spammen.
            # Einfache Logik: Wenn repeat=True, feuert es jeden Tick ab trigger_time.
            return self.game.time >= event.get('trigger_time', 99999)
            
        elif trigger_type == 'location':
            target_loc = event.get('location')
            if not target_loc: target_loc = event.get('value')
            return self.game.location == target_loc
            
        elif trigger_type == 'condition':
            return self._evaluate_condition(event.get('condition', {}))
            
        elif trigger_type == 'complex':
            conditions = event.get('conditions', [])
            operator = event.get('operator', 'AND').upper()
            if not conditions: return False
            results = [self._evaluate_condition(c) for c in conditions]
            return all(results) if operator == 'AND' else any(results)
        
        elif trigger_type == 'manual': return False
        return False

    def _evaluate_condition(self, cond):
        c_type = cond.get('type')
        negate = cond.get('not', False)
        result = False

        if c_type == 'knowledge': result = cond.get('value') in self.game.knowledge
        elif c_type == 'location': result = self.game.location == cond.get('value')
        elif c_type == 'item_location':
            item_id = cond.get('item')
            target_loc = cond.get('location')
            obj = self.game.objects.get(item_id)
            if obj: result = obj['location'] == target_loc
        elif c_type == 'npc_state':
            npc_id = cond.get('npc')
            state = cond.get('state')
            target = next((n for n in self.game.npcs if n.get('id') == npc_id or n.get('name') == npc_id), None)
            if target: result = target.get('state') == state
        elif c_type == 'quest_state':
            q_id = cond.get('quest')
            stage = cond.get('stage')
            q_state = self.game.quests.states.get(q_id, {})
            result = q_state.get('status') == 'active' and q_state.get('stage') == stage
        elif c_type == 'stability':
            threshold = cond.get('value', 0)
            op = cond.get('op', '<')
            if op == '<': result = self.game.stability < threshold
            elif op == '>': result = self.game.stability > threshold
        elif c_type == 'event_triggered':
            ev_id = cond.get('id')
            target_ev = next((e for e in self.events if e.get('id') == ev_id), None)
            if target_ev: result = target_ev.get('triggered', False)

        return not result if negate else result

    def _execute_event(self, event):
        """Führt die Effekte eines Events aus."""
        # Verhindere Spam bei Repeat-Events: Nur ausführen, wenn in DIESEM Tick noch nicht gefeuert?
        # Oder wir verlassen uns darauf, dass der GameState tickt.
        # Problem: self.game.time ändert sich nur bei Aktionen.
        # Wenn time=5 und wir bewegen uns nicht, bleibt time=5. Update wird trotzdem gerufen?
        # Nein, GameState.tick() wird nur bei Aktionen gerufen. Also ist es sicher.
        
        event['triggered'] = True
        event['triggered_at'] = self.game.time
        
        # 1. Narrativ (Text im aktuellen Raum)
        if 'description' in event:
            origin = event.get('origin_id')
            # Wenn kein Origin definiert ist ODER wir im Origin sind:
            if not origin or origin == self.game.location:
                self.game.log('event', event.get('title', 'EVENT'))
                self.game.log('story', event['description'])

        # 2. Akustik (Sound aus einem anderen Raum)
        # Dies war vorher falsch eingerückt! Jetzt ist es eigenständig.
        if 'sound_msg' in event:
            origin = event.get('origin_id')
            if origin and origin != self.game.location:
                # Prüfe Hörbarkeit
                vol, direction = self.game.acoustics.get_audibility_info(origin, self.game.location)
                
                # Debug Info im Log, falls gewünscht (auskommentiert)
                # print(f"Sound check from {origin} to {self.game.location}: Vol={vol}, Dir={direction}")
                
                if vol > 0.05: # Hörschwelle
                    sound_msg = event.get('sound_msg', "Ein Geräusch.")
                    
                    # Lautstärke-Indikator
                    prefix = ""
                    if vol < 0.3: prefix = "(leise) "
                    elif vol > 0.8: prefix = "(LAUT) "
                    
                    self.game.log('event', f"Aus {direction} hörst du: {prefix}{sound_msg}")
            
            elif origin == self.game.location:
                # Wenn wir im selben Raum sind, geben wir den Sound direkt aus (falls nicht schon durch description geschehen)
                if 'description' not in event:
                     self.game.log('event', event.get('sound_msg'))

        # 3. System-Nachrichten
        if 'message' in event: self.game.log('info', event['message'])

        # 4. Quest Updates
        if 'quest_update' in event:
            q_data = event['quest_update']
            self.game.quests.update_quest(q_data['id'], q_data['stage'])
        if 'quest_start' in event:
            self.game.quests.start_quest(event['quest_start'])

        # 5. Generische Effekte
        if 'effects' in event:
            self.game.effects.process(event['effects'])