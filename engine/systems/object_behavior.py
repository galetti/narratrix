# engine/systems/object_behavior.py
from utils import rng
from engine.constants import ATTR_NAME

class ObjectBehaviorSystem:
    def __init__(self, game):
        self.game = game

    def process_all_objects(self):
        """Haupt-Loop: Prüft alle Objekte auf autonome Verhaltensweisen."""
        for obj in self.game.objects.values():
            behavior = obj.get('behavior')
            if behavior:
                self._process_single_object(obj, behavior)

    def _process_single_object(self, obj, behavior):
        b_type = behavior.get('type')
        
        # 1. Defekte Tür/Schott (Öffnet und schließt sich zufällig)
        if b_type == 'random_open_close':
            chance = behavior.get('chance', 20)
            if rng.chance(chance):
                # Toggle Zustand
                was_open = obj.get('is_open', False)
                obj['is_open'] = not was_open
                
                # Wenn der Spieler im gleichen Raum ist -> Feedback
                if obj['location'] == self.game.location:
                    name = obj[ATTR_NAME]
                    if obj['is_open']:
                        self.game.log('event', f"Der {name} öffnet sich zischend von selbst.")
                    else:
                        self.game.log('event', f"Der {name} fällt scheppernd ins Schloss.")