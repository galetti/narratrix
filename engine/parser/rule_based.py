# engine/parser/rule_based.py
from engine.action_dispatcher import ActionDispatcher

class RuleBasedParser:
    def __init__(self, game):
        self.game = game

    def parse(self, user_input):
        text = user_input.lower().strip()
        for char in ".,!?;:": text = text.replace(char, "")
        words = text.split()
        
        if not words: return

        # 1. KONTEXT-CHECK (Disambiguierung ODER Pending Interaction)
        # Wenn das Spiel auf eine Antwort wartet, ignorieren wir die Grammatik.
        if self.game.disambiguation or self.game.pending_interaction:
            ActionDispatcher.dispatch(self.game, words[0], words[1:])
            return

        # 2. Normales Parsing
        verb = words[0]
        args = words[1:]

        canonical = self._get_canonical(verb)
        final_verb = canonical if canonical else verb
        
        ActionDispatcher.dispatch(self.game, final_verb, args)

    def _get_canonical(self, word):
        verbs = self.game.config.get('vocabulary', {}).get('verbs', {})
        for can, syns in verbs.items():
            if word == can or word in syns: return can
        return None