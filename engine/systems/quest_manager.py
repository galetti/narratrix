from engine.constants import *

class QuestManager:
    def __init__(self, game):
        self.game = game
        self.definitions = {}
        self.states = {} # id -> {status: active/completed/failed, stage: int}

    def load_definitions(self, quests_data):
        self.definitions = quests_data
        # Ensure states exist for defined quests if not loaded from save
        for q_id in self.definitions:
            if q_id not in self.states:
                self.states[q_id] = {'status': 'inactive', 'stage': 0}

    def start_quest(self, quest_id):
        # Safety Check
        if quest_id not in self.definitions:
            # Fallback: Vielleicht wurde definitions noch nicht geladen oder ID ist falsch
            print(f"[WARN] Quest '{quest_id}' definition not found in {self.definitions.keys()}")
            return
        
        if quest_id not in self.states:
            self.states[quest_id] = {'status': 'inactive', 'stage': 0}
            
        # Nur starten, wenn noch nicht aktiv oder abgeschlossen
        if self.states[quest_id]['status'] == 'inactive':
            self.states[quest_id]['status'] = 'active'
            self.states[quest_id]['stage'] = 0
            
            q_def = self.definitions[quest_id]
            title = q_def.get('title', quest_id)
            self.game.log('success', f"NEUE AUFGABE: {title}")
            
            # Zeige ersten Schritt
            desc = q_def.get('stages', {}).get(0, "")
            if desc: self.game.log('info', f"Ziel: {desc}")

    def update_quest(self, quest_id, stage):
        if quest_id not in self.states: return
        
        current_status = self.states[quest_id]['status']
        if current_status != 'active': return 
        
        current_stage = self.states[quest_id].get('stage', 0)
        if stage != current_stage:
            self.states[quest_id]['stage'] = stage
            self.game.log('success', f"AUFGABE AKTUALISIERT: {self.definitions[quest_id].get('title', quest_id)}")
            
            stage_desc = self.definitions[quest_id].get('stages', {}).get(stage, "")
            if stage_desc:
                self.game.log('info', f"Neues Ziel: {stage_desc}")

    def complete_quest(self, quest_id):
        if quest_id in self.states and self.states[quest_id]['status'] == 'active':
            self.states[quest_id]['status'] = 'completed'
            self.game.log('success', f"AUFGABE ERLEDIGT: {self.definitions[quest_id].get('title', quest_id)}")

    def fail_quest(self, quest_id):
        if quest_id in self.states and self.states[quest_id]['status'] == 'active':
            self.states[quest_id]['status'] = 'failed'
            self.game.log('error', f"AUFGABE FEHLGESCHLAGEN: {self.definitions[quest_id].get('title', quest_id)}")

    def get_active_quests(self):
        active = []
        for q_id, state in self.states.items():
            if state['status'] == 'active':
                q_def = self.definitions.get(q_id, {})
                title = q_def.get('title', q_id)
                stage = state.get('stage', 0)
                # Wichtig: Hole die Beschreibung für die aktuelle Stage
                stage_desc = q_def.get('stages', {}).get(stage, "")
                
                active.append({
                    'id': q_id,
                    'title': title,
                    'stage': stage,
                    'stage_desc': stage_desc
                })
        return active

    def get_completed_quests(self):
        completed = []
        for q_id, state in self.states.items():
            if state['status'] == 'completed':
                q_def = self.definitions.get(q_id, {})
                title = q_def.get('title', q_id)
                completed.append(title)
        return completed

    def get_save_data(self):
        return self.states

    def load_save_data(self, data):
        self.states = data