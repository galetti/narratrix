from __future__ import annotations

import difflib
import logging
from typing import TYPE_CHECKING, Any

try:
    import spacy
except ImportError:  # Spacy support is optional.
    spacy = None  # type: ignore[assignment]

from engine.action_dispatcher import ActionDispatcher

if TYPE_CHECKING:
    from engine.game_state import GameState

logger = logging.getLogger(__name__)


class SpacyParser:
    """
    Fortschrittlicher Parser, der natürliche Sprache (NLP) nutzt, um Befehle zu verstehen.
    Verwendet bevorzugt das Spacy Modell 'de_core_news_md' und fällt auf
    'de_core_news_sm' oder den regelbasierten Parser zurück.
    """
    
    # Mapping von deutschen Lemmata (Grundformen) auf Engine-Befehle
    VERB_MAP: dict[str, str] = {
        # Bewegung
        "gehen": "move", "laufen": "move", "rennen": "move", "betreten": "move",
        "klettern": "climb", "erklimmen": "climb",
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
        "journal": "journal", "logbuch": "journal", "aufgaben": "journal",
        "karte": "map", "plan": "map", "radar": "map",
    }

    @staticmethod
    def _safe_lemma(token: Any) -> str:
        lemma = str(getattr(token, "lemma_", "")).strip().lower()
        if not lemma or lemma == "--":
            return str(token.text).strip().lower()
        return lemma

    def _match_vocab_verb(self, word: str) -> str | None:
        if word in self.VERB_MAP:
            return self.VERB_MAP[word]
        verbs = self.game.config.get("vocabulary", {}).get("verbs", {})
        if word in verbs:
            return str(word)
        for canonical, synonyms in verbs.items():
            if word == canonical or word in synonyms:
                return str(canonical)
        if word in ActionDispatcher.COMMAND_MAP:
            return word
        return None

    def _match_direction(self, word: str) -> str | None:
        vocab_dirs = self.game.config.get("vocabulary", {}).get("directions", {})
        for direction, synonyms in vocab_dirs.items():
            if word == direction or word in synonyms:
                return str(direction)
        return None

    def __init__(self, game: GameState) -> None:
        self.game: GameState = game
        self.available: bool = False
        self.nlp: Any = None
        
        if spacy is None:
            logger.info("Spacy ist nicht installiert; nutze Regelparser.")
            return

        try:
            for model_name in ("de_core_news_md", "de_core_news_sm"):
                try:
                    self.nlp = spacy.load(model_name)
                    self.available = True
                    logger.info("Spacy NLP Engine geladen: %s", model_name)
                    break
                except OSError:
                    continue
            if not self.available:
                logger.info("Kein deutsches Spacy-Modell gefunden; nutze Regelparser.")
        except (OSError, ImportError, ValueError, RuntimeError) as e:
            logger.warning("Fehler beim Laden von Spacy: %s", e)
            self.available = False

    def parse(self, user_input: str) -> None:
        if not self.available or not self.nlp or not user_input.strip():
            from engine.parser.rule_based import RuleBasedParser
            fallback = RuleBasedParser(self.game)
            fallback.parse(user_input)
            return

        if self.game.disambiguation or self.game.pending_interaction:
            words = user_input.lower().strip().split()
            if words:
                ActionDispatcher.dispatch(self.game, words[0], words[1:])
            return

        cleaned_input = user_input.strip()
        single_words = cleaned_input.lower().rstrip(".,!?;:").split()
        if len(single_words) == 1:
            direction_cmd = self._match_direction(single_words[0])
            if direction_cmd:
                ActionDispatcher.dispatch(self.game, direction_cmd, [])
                return
            direct_verb = self._match_vocab_verb(single_words[0])
            if direct_verb:
                ActionDispatcher.dispatch(self.game, direct_verb, [])
                return

        doc = self.nlp(cleaned_input)

        # 1. Hauptverb finden: Zuerst prüfen, ob ein Token direkt einem bekannten Verb entspricht
        # (da Spacy deutsche Imperative am Satzanfang wie "untersuche" oder "repariere" oft als ADJ taggt)
        main_verb_token: Any = None
        engine_cmd: str | None = None

        for token in doc:
            lemma = self._safe_lemma(token)
            raw_text = token.text.lower()
            matched = self._match_vocab_verb(lemma) or self._match_vocab_verb(raw_text)
            if matched:
                main_verb_token = token
                engine_cmd = matched
                break

        if not main_verb_token:
            for token in doc:
                if token.pos_ == "VERB" or token.dep_ == "ROOT":
                    main_verb_token = token
                    break

        # Verb Analyse (falls noch kein direkter Treffer)
        if main_verb_token and not engine_cmd:
            lemma = self._safe_lemma(main_verb_token)
            raw_text = main_verb_token.text.lower()

            # Sonderfall: Richtung als Haupttoken ("Norden", "s", "runter")
            direction_cmd = self._match_direction(raw_text) or self._match_direction(lemma)
            if direction_cmd:
                ActionDispatcher.dispatch(self.game, direction_cmd, [])
                return

            # Fuzzy Matching für das Verb, falls Mapping fehlschlägt
            matches = difflib.get_close_matches(lemma, self.VERB_MAP.keys(), n=1, cutoff=0.8)
            if matches:
                engine_cmd = self.VERB_MAP[matches[0]]
            else:
                matches_raw = difflib.get_close_matches(
                    raw_text, self.VERB_MAP.keys(), n=1, cutoff=0.7
                )
                if matches_raw:
                    engine_cmd = self.VERB_MAP[matches_raw[0]]

        # Fallback auf erstes Wort, wenn kein Verb-Token gefunden wurde
        if not engine_cmd and doc:
            first_word = doc[0].text.lower()
            matches = difflib.get_close_matches(
                first_word, self.VERB_MAP.keys(), n=1, cutoff=0.7
            )
            if matches:
                engine_cmd = self.VERB_MAP[matches[0]]
                main_verb_token = doc[0]

        if not engine_cmd:
            from engine.parser.rule_based import RuleBasedParser

            fallback = RuleBasedParser(self.game)
            fallback.parse(user_input)
            return

        # 2. Argumente extrahieren (Bindestrich-Komposita wie "Resonanz-Kern" zusammenhalten)
        args: list[str] = []
        if main_verb_token:
            filler = {"bitte", "schnell", "mal", "doch"}
            verb_raw = main_verb_token.text.lower()
            removed_verb = False
            for raw_word in cleaned_input.split():
                stripped = raw_word.strip(".,!?;:")
                if not stripped:
                    continue
                low = stripped.lower()
                if not removed_verb and low == verb_raw:
                    removed_verb = True
                    continue
                if low in filler:
                    continue
                args.append(stripped)
        else:
            args = user_input.split()[1:]

        ActionDispatcher.dispatch(self.game, engine_cmd, args)
