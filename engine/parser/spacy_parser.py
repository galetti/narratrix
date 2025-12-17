import spacy
from engine.action_dispatcher import ActionDispatcher

class SpacyParser:
    def __init__(self, game):
        self.game = game
        self.nlp = None
        self.available = False
        
        try:
            self.nlp = spacy.load("de_core_news_md")
            print("[SPACY] Modell 'de_core_news_md' erfolgreich geladen.")
            self.available = True
        except OSError:
            try:
                self.nlp = spacy.load("de_core_news_sm")
                print("[SPACY] Modell 'de_core_news_sm' geladen.")
                self.available = True
            except OSError:
                print("\n[SPACY ERROR] Kein Sprachmodell gefunden!")
                print("Bitte führe aus: python -m spacy download de_core_news_md\n")
                self.available = False

    def parse(self, user_input):
        if not self.available:
            self.game.log('error', "Systemfehler: NLP-Modul offline.")
            return

        # 1. KONTEXT-CHECK (WICHTIG!)
        if self.game.disambiguation or self.game.pending_interaction:
            # Wir leiten den rohen Input weiter, damit "Becher" als Argument ankommt
            # und nicht als fehlgeschlagener Verb-Versuch endet.
            # Splitte manuell für Dispatcher-Signatur
            parts = user_input.split()
            if parts:
                ActionDispatcher.dispatch(self.game, parts[0], parts[1:])
            return

        # 2. Kurze Befehle direkt durchleiten (Richtungsschutz)
        if len(user_input.strip()) <= 2:
            ActionDispatcher.dispatch(self.game, user_input.strip(), [])
            return

        doc = self.nlp(user_input)
        
        verbs = [t for t in doc if t.pos_ in ["VERB", "AUX"]]
        root = next((t for t in verbs if t.dep_ == "ROOT"), None)
        
        if not root and len(doc) > 0: root = doc[0]
        if not root: return 

        verb_lemma = root.lemma_.lower()
        canonical = self._get_canonical(verb_lemma)
        if not canonical: canonical = self._get_canonical(root.text.lower())
        final_verb = canonical if canonical else verb_lemma

        args = []
        for token in doc:
            if token == root: continue 
            if token.pos_ in ["PUNCT", "SPACE", "CCONJ", "DET"]: continue 
            args.append(token.text)

        ActionDispatcher.dispatch(self.game, final_verb, args)

    def _get_canonical(self, word):
        verbs = self.game.config.get('vocabulary', {}).get('verbs', {})
        for can, syns in verbs.items():
            if word == can or word in syns: return can
        return None