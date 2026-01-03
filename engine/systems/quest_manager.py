from engine.strings import Texts

class QuestStatus:
    INACTIVE = "inactive"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"

class QuestManager:
    """
    Verwaltet Quests, ihren Status und Fortschritt.
    """
    def __init__(self, game):
        self.game = game
        self.definitions = {} # Statische Daten (Titel, Stufen)
        # Dynamische Daten: {quest_id: {'status': 'active', 'stage': 1, 'visible': True}}
        self.states = {} 

    def load_definitions(self, quests_data):
        """Lädt die Quest-Definitionen aus der Config."""
        self.definitions = quests_data
        # Initialisiere States für neue Quests als INACTIVE
        for q_id in self.definitions:
            if q_id not in self.states:
                self.states[q_id] = {
                    'status': QuestStatus.INACTIVE,
                    'stage': 0,
                    'visible': False
                }

    def start_quest(self, quest_id, silent=False):
        """Startet eine Quest."""
        if quest_id not in self.definitions:
            print(f"[WARN] Quest '{quest_id}' nicht gefunden.")
            return

        state = self.states[quest_id]
        if state['status'] == QuestStatus.INACTIVE:
            state['status'] = QuestStatus.ACTIVE
            state['stage'] = 1
            state['visible'] = True
            
            if not silent:
                q_def = self.definitions[quest_id]
                self.game.log('event', f"--- NEUE AUFGABE: {q_def['title']} ---")
                self.game.log('info', f"Ziel: {self._get_stage_desc(quest_id, 1)}")

    def update_quest(self, quest_id, stage_index, silent=False):
        """Aktualisiert den Fortschritt einer Quest."""
        if quest_id not in self.states: return
        
        state = self.states[quest_id]
        if state['status'] != QuestStatus.ACTIVE: return # Nur aktive Quests updaten
        
        if state['stage'] != stage_index:
            state['stage'] = stage_index
            if not silent:
                self.game.log('success', f"Aufgabe aktualisiert: {self.definitions[quest_id]['title']}")
                self.game.log('info', f"Neues Ziel: {self._get_stage_desc(quest_id, stage_index)}")

    def complete_quest(self, quest_id, silent=False):
        """Schließt eine Quest erfolgreich ab."""
        if quest_id not in self.states: return
        
        state = self.states[quest_id]
        if state['status'] != QuestStatus.COMPLETED:
            state['status'] = QuestStatus.COMPLETED
            if not silent:
                self.game.log('success', f"AUFGABE ERLEDIGT: {self.definitions[quest_id]['title']}")

    def fail_quest(self, quest_id, silent=False):
        """Markiert eine Quest als gescheitert."""
        if quest_id not in self.states: return
        
        state = self.states[quest_id]
        state['status'] = QuestStatus.FAILED
        if not silent:
            self.game.log('alarm', f"AUFGABE GESCHEITERT: {self.definitions[quest_id]['title']}")

    def get_active_quests(self):
        """Gibt eine Liste aktiver Quests zurück."""
        active = []
        for q_id, state in self.states.items():
            if state['status'] == QuestStatus.ACTIVE and state['visible']:
                active.append({
                    'id': q_id,
                    'title': self.definitions[q_id]['title'],
                    'stage_desc': self._get_stage_desc(q_id, state['stage'])
                })
        return active

    def get_completed_quests(self):
        completed = []
        for q_id, state in self.states.items():
            if state['status'] == QuestStatus.COMPLETED and state['visible']:
                completed.append(self.definitions[q_id]['title'])
        return completed

    def _get_stage_desc(self, quest_id, stage_idx):
        stages = self.definitions[quest_id].get('stages', {})
        # JSON Keys sind oft Strings, wir versuchen Int Konvertierung
        stage_text = stages.get(stage_idx) or stages.get(str(stage_idx))
        return stage_text if stage_text else "..."

    # --- SAVE/LOAD ---
    def get_save_data(self):
        return self.states

    def load_save_data(self, data):
        self.states = data