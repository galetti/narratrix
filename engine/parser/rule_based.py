from engine.action_dispatcher import ActionDispatcher
import difflib

class RuleBasedParser:
    def __init__(self, game):
        self.game = game

    def parse(self, user_input):
        text = user_input.lower().strip()
        # Einfache Bereinigung von Satzzeichen
        for char in ".,!?;:": text = text.replace(char, "")
        words = text.split()
        
        if not words: return

        # 1. KONTEXT-CHECK (Disambiguierung ODER Pending Interaction)
        # Wenn das Spiel auf eine Antwort wartet, leiten wir alles weiter.
        if self.game.disambiguation or self.game.pending_interaction:
            # Wir übergeben das erste Wort als "Verb" und den Rest als Args,
            # aber der Dispatcher weiß bei Pending/Disambiguation, dass er das anders behandeln muss.
            ActionDispatcher.dispatch(self.game, words[0], words[1:])
            return

        # 2. Normales Parsing
        verb_input = words[0]
        args = words[1:]

        # A. Exakter Match oder Synonym-Check
        canonical = self._get_canonical(verb_input)
        
        # B. Fuzzy Match (Falls kein exakter Treffer)
        if not canonical:
            canonical = self._get_fuzzy_verb(verb_input)
            # Optional: Feedback geben, z.B.:
            # if canonical: self.game.log('info', f"(Ich nehme an, du meinst '{canonical}')")

        final_verb = canonical if canonical else verb_input
        
        ActionDispatcher.dispatch(self.game, final_verb, args)

    def _get_canonical(self, word):
        """Prüft auf exakte Übereinstimmung mit einem Verb oder dessen Synonymen."""
        verbs = self.game.config.get('vocabulary', {}).get('verbs', {})
        
        # 1. Check Key (Canonical)
        if word in verbs: return word
        
        # 2. Check Synonyms
        for can, syns in verbs.items():
            if word == can or word in syns: return can
            
        # 3. Check Directions (werden oft als Verben genutzt -> "norden" = "move north")
        vocab_dirs = self.game.config.get('vocabulary', {}).get('directions', {})
        for direction, synonyms in vocab_dirs.items():
            if word == direction or word in synonyms:
                # Wir geben das Wort zurück; ActionDispatcher fängt Directions ab und routet zu 'move'
                return word
                
        return None

    def _get_fuzzy_verb(self, word):
        """Versucht, ein ähnliches Verb zu finden (Toleranz für Tippfehler)."""
        verbs = self.game.config.get('vocabulary', {}).get('verbs', {})
        all_verbs = list(verbs.keys())
        for syns in verbs.values():
            all_verbs.extend(syns)
            
        # Auch Richtungen hinzufügen
        vocab_dirs = self.game.config.get('vocabulary', {}).get('directions', {})
        for d, syns in vocab_dirs.items():
            all_verbs.append(d)
            all_verbs.extend(syns)

        # Suche nach Ähnlichkeiten (Cutoff 0.8 bedeutet 80% Übereinstimmung nötig)
        matches = difflib.get_close_matches(word, all_verbs, n=1, cutoff=0.8)
        
        if matches:
            best_match = matches[0]
            # Jetzt müssen wir den Canonical dazu finden
            return self._get_canonical(best_match)
            
        return None