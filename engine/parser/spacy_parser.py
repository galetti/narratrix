import spacy
import difflib
from engine.action_dispatcher import ActionDispatcher

class SpacyParser:
    """
    Fortschrittlicher Parser, der natürliche Sprache (NLP) nutzt, um Befehle zu verstehen.
    Verwendet bevorzugt das Spacy Modell 'de_core_news_md' und fällt auf
    'de_core_news_sm' oder den regelbasierten Parser zurück.
    """
    
    # Mapping von deutschen Lemmata (Grundformen) auf Engine-Befehle
    VERB_MAP = {
        # Bewegung
        "gehen": "move", "laufen": "move", "rennen": "move",
        "klettern": "climb",
        "steigen": "move", "kriechen": "move", "wandern": "move",
        
        # Exploration
        "schauen": "look", "ansehen": "look", "betrachten": "look", "untersuchen": "look",
        "lesen": "look", "prüfen": "look", "gucken": "look", "blicken": "look",
        "verstecken": "hide", "ducken": "hide",
        
        # Inventory
        "nehmen": "take", "aufheben": "take", "greifen": "take", "einstecken": "take", "schnappen": "take",
        "tragen": "take", "behalten": "take",
        "ablegen": "drop", "fallenlassen": "drop", "hinlegen": "drop", "wegwerfen": "drop", "lassen": "drop",
        "geben": "give", "reichen": "give", "schenken": "give", "überreichen": "give", "händigen": "give",
        
        # Mechanics
        "benutzen": "use", "verwenden": "use", "kombinieren": "use", "anwenden": "use", "nutzen": "use",
        "öffnen": "open", "aufmachen": "open",
        "schließen": "close", "zumachen": "close", 
        "legen": "put", "stecken": "put", "tun": "put", "platzieren": "put", "stellen": "put", "packen": "put",
        "brechen": "break", "zerstören": "break", "zerschlagen": "break", "einschlagen": "break", "aufbrechen": "break", "treten": "break",
        "reparieren": "fix", "flicken": "fix", "heilen": "fix", "montieren": "fix",
        "warten": "wait", "ruhen": "wait", "schlafen": "wait",
        
        # Talk
        "reden": "talk", "sprechen": "talk", "sagen": "talk", "fragen": "talk", "antworten": "talk",
        
        # System
        "speichern": "save", "sichern": "save",
        "laden": "load",
        "hilfe": "help", "helfen": "help",
        "inventar": "inv", "tasche": "inv", "rucksack": "inv",
        "journal": "journal", "logbuch": "journal", "aufgaben": "journal"
    }

    def __init__(self, game):
        self.game = game
        self.available = False
        self.nlp = None
        
        try:
            for model_name in ("de_core_news_md", "de_core_news_sm"):
                try:
                    self.nlp = spacy.load(model_name)
                    self.available = True
                    print(f"[SYSTEM] Spacy NLP Engine geladen: {model_name}")
                    break
                except OSError:
                    continue
            if not self.available:
                print("[SYSTEM] Kein deutsches Spacy-Modell gefunden; nutze Regelparser.")
        except Exception as e:
            print(f"[SYSTEM] Fehler beim Laden von Spacy: {e}")
            self.available = False

    def parse(self, user_input):
        if not self.available or not user_input.strip():
            from engine.parser.rule_based import RuleBasedParser
            fallback = RuleBasedParser(self.game)
            fallback.parse(user_input)
            return

        if self.game.disambiguation or self.game.pending_interaction:
            words = user_input.lower().strip().split()
            if words:
                ActionDispatcher.dispatch(self.game, words[0], words[1:])
            return

        doc = self.nlp(user_input.strip())
        
        # 1. Hauptverb finden
        main_verb_token = None
        for token in doc:
            if token.pos_ == "VERB" or token.dep_ == "ROOT":
                main_verb_token = token
                break
        
        engine_cmd = None
        
        # Verb Analyse
        if main_verb_token:
            lemma = main_verb_token.lemma_.lower()
            engine_cmd = self.VERB_MAP.get(lemma)
            
            # Sonderfall: Directions als Nomen ("Norden")
            if not engine_cmd and main_verb_token.pos_ in ["NOUN", "PROPN"]:
                vocab_dirs = self.game.config.get('vocabulary', {}).get('directions', {})
                raw_text = main_verb_token.text.lower()
                for d, syns in vocab_dirs.items():
                    if raw_text == d or raw_text in syns:
                        ActionDispatcher.dispatch(self.game, d, [])
                        return

            # NEU: Fuzzy Matching für das Verb, falls Mapping fehlschlägt
            if not engine_cmd:
                # Wir suchen in den Keys unserer VERB_MAP
                matches = difflib.get_close_matches(lemma, self.VERB_MAP.keys(), n=1, cutoff=0.8)
                if matches:
                    engine_cmd = self.VERB_MAP[matches[0]]
                else:
                    # Auch im Raw Text suchen (z.B. "jounral" -> lemma ist oft gleich)
                    raw_text = main_verb_token.text.lower()
                    matches_raw = difflib.get_close_matches(raw_text, self.VERB_MAP.keys(), n=1, cutoff=0.7)
                    if matches_raw:
                        engine_cmd = self.VERB_MAP[matches_raw[0]]

        # Fallback auf erstes Wort, wenn kein Verb-Token gefunden wurde
        if not engine_cmd and doc:
            first_word = doc[0].text.lower()
            matches = difflib.get_close_matches(first_word, self.VERB_MAP.keys(), n=1, cutoff=0.7)
            if matches:
                engine_cmd = self.VERB_MAP[matches[0]]

        if not engine_cmd:
            # Wenn alles fehlschlägt, nutzen wir das Lemma, vielleicht kann der Dispatcher (RuleBased fallback) noch was retten
            engine_cmd = main_verb_token.lemma_.lower() if main_verb_token else user_input.split()[0]

        # 2. Argumente extrahieren
        args = []
        if main_verb_token:
            filler = {"bitte", "schnell", "mal", "doch"}
            relevant_tokens = [
                t
                for t in doc
                if t != main_verb_token
                and not t.is_punct
                and t.lemma_.lower() not in filler
            ]
            relevant_tokens.sort(key=lambda t: t.i)
            args = [t.text for t in relevant_tokens]
        else:
            args = user_input.split()[1:]

        ActionDispatcher.dispatch(self.game, engine_cmd, args)
