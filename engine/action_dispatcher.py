# narratrix_engine/engine/action_dispatcher.py
from engine.handlers.movement import MovementHandler
from engine.handlers.dialogue import DialogueHandler
from engine.handlers.system import SystemHandler
from engine.handlers.exploration import ExplorationHandler
from engine.handlers.inventory import InventoryHandler
from engine.handlers.mechanics import MechanicsHandler

# NEU: Wir müssen AmbiguityError importieren
from engine.resolver import AmbiguityError
from engine.constants import ATTR_NAME

class ActionDispatcher:
    COMMAND_MAP = {
        # Exploration
        'look': ExplorationHandler.look, 'l': ExplorationHandler.look, 'x': ExplorationHandler.look,
        'hide': ExplorationHandler.hide, 'verstecke': ExplorationHandler.hide,
        
        # Inventory
        'take': InventoryHandler.take, 'get': InventoryHandler.take, 'nimm': InventoryHandler.take,
        'drop': InventoryHandler.drop,
        'give': InventoryHandler.give, 'gib': InventoryHandler.give,
        'inv': InventoryHandler.inventory, 'i': InventoryHandler.inventory, 'inventory': InventoryHandler.inventory,
        
        # Mechanics
        'put': MechanicsHandler.put,
        'use': MechanicsHandler.use, 'combine': MechanicsHandler.use,
        'open': MechanicsHandler.open,
        'break': MechanicsHandler.break_,
        'fix': MechanicsHandler.fix,
        'wait': MechanicsHandler.wait, 'warte': MechanicsHandler.wait,

        # Movement
        'move': MovementHandler.handle, 'gehe': MovementHandler.handle, 'lauf': MovementHandler.handle,

        # Dialogue
        'talk': DialogueHandler.talk, 'rede': DialogueHandler.talk, 'sprich': DialogueHandler.talk,

        # System
        'save': SystemHandler.save,
        'load': SystemHandler.load,
        'oracle': SystemHandler.oracle, 'orakel': SystemHandler.oracle, 'hack': SystemHandler.oracle,
        'map': SystemHandler.map, 'karte': SystemHandler.map,
        'help': SystemHandler.help,
        'journal': SystemHandler.journal, 'logbuch': SystemHandler.journal, 'aufgaben': SystemHandler.journal 
    }

    @staticmethod
    def dispatch(game, verb, args):
        # 1. Check auf ausstehende Interaktionen
        if game.pending_interaction:
            ActionDispatcher._handle_pending(game, verb, args)
            return

        # 2. Check auf Disambiguierung
        if game.disambiguation:
            ActionDispatcher._handle_disambiguation(game, verb, args)
            return

        # 3. Normales Dispatching mit Ambiguity Handling
        handler_func = ActionDispatcher.COMMAND_MAP.get(verb)
        if handler_func:
            try:
                handler_func(game, args)
            except AmbiguityError as e:
                # Hier fangen wir den Fehler vom Resolver
                names = [m[ATTR_NAME] for m in e.candidates]
                game.log('info', f"Meinst du: {', '.join(names)}?")
                
                # Wir speichern den Kontext, um den Befehl später neu bauen zu können
                game.disambiguation = {
                    'verb': verb,
                    'full_args': args,             # Die vollen Argumente (z.B. ["key", "with", "door"])
                    'ambiguous_words': e.query_words, # Der Teil, der mehrdeutig war (z.B. ["key"])
                    'candidates': e.candidates
                }
            return

        # 4. Fallback: Richtung?
        vocab_dirs = game.config.get('vocabulary', {}).get('directions', {})
        for canonical, synonyms in vocab_dirs.items():
            if verb == canonical or verb in synonyms:
                MovementHandler.handle(game, [verb])
                return

        game.log('error', f"Ich weiß nicht, wie ich '{verb}' soll.")

    @staticmethod
    def dialogue_step(game, user_input):
        DialogueHandler.step(game, user_input)

    @staticmethod
    def _handle_pending(game, verb, args):
        state = game.pending_interaction
        original_verb = state['verb']
        item1_args = state['args']
        
        item2_name = f"{verb} {' '.join(args)}".strip()
        item1_name = " ".join(item1_args)
        
        if original_verb == 'use':
            result_msg = game.perform_combine(item1_name, item2_name)
            if "Fehler" in result_msg or "nicht" in result_msg.lower(): 
                game.log('error', result_msg)
            else: 
                game.log('success', result_msg)
                game.tick(2)
        game.pending_interaction = None

    @staticmethod
    def _handle_disambiguation(game, verb, args):
        state = game.disambiguation
        candidates = state['candidates']
        
        # User Input verarbeiten
        filter_text = ""
        if verb == "disambiguate":
            filter_text = args[0].strip().lower()
        else:
            filter_text = f"{verb} {' '.join(args)}".strip().lower()
        
        if filter_text in ["stop", "abbrechen", "nein", "cancel", "zurück"]:
            game.log('info', "Abgebrochen.")
            game.disambiguation = None
            return

        # Filtern der Kandidaten
        matches = []
        for cand in candidates:
            c_name = cand['name'].lower()
            if filter_text in c_name or any(filter_text in a.lower() for a in cand.get('aliases', [])):
                matches.append(cand)
        
        if len(matches) == 1:
            target = matches[0]
            game.log('user', f"(Ausgewählt: {target['name']})")
            
            # --- REKONSTRUKTION DES BEFEHLS ---
            original_verb = state['verb']
            full_args = state['full_args'] # Liste von Strings
            ambiguous_part = state['ambiguous_words'] # Liste von Strings (z.B. ["key"])
            
            # Wir müssen die ambiguous_part Sequenz in full_args finden und durch den vollen Namen ersetzen
            new_args = list(full_args)
            
            # Einfacher Ansatz: Wir suchen das erste Vorkommen des ersten Worts der Ambiguität
            # und ersetzen die Länge der Ambiguität.
            if ambiguous_part:
                start_word = ambiguous_part[0]
                try:
                    # Finde Startindex
                    idx = -1
                    # Wir suchen manuell, um sicher zu sein (case sensitive check in args)
                    for i, w in enumerate(new_args):
                        if w == start_word: # Strenger Match, da Resolver clean_args nutzt, könnte unscharf sein
                            idx = i
                            break
                    
                    if idx == -1:
                        # Fallback: Versuche case-insensitive
                        for i, w in enumerate(new_args):
                            if w.lower() == start_word.lower():
                                idx = i
                                break

                    if idx != -1:
                        # Wir entfernen die mehrdeutigen Worte
                        # Wir ersetzen sie durch den präzisen Namen des Ziels (als Token-Liste)
                        target_tokens = target['name'].split()
                        
                        # Slice replacement
                        end_idx = idx + len(ambiguous_part)
                        new_args[idx:end_idx] = target_tokens
                        
                except Exception as e:
                    print(f"[WARN] Disambiguierung Rekonstruktion fehlgeschlagen: {e}")
                    # Fallback: Einfach Namen anhängen (funktioniert nur bei simplen Verben)
                    new_args = [target['name']]

            # Reset State
            game.disambiguation = None 
            
            # Erneuter Dispatch mit präzisiertem Befehl
            # game.log('info', f"DEBUG: Executing '{original_verb} {new_args}'")
            ActionDispatcher.dispatch(game, original_verb, new_args)

        elif len(matches) > 1:
            names = [m['name'] for m in matches]
            game.log('info', f"Das grenzt es nicht genug ein. Meinst du: {', '.join(names)}?")
        else:
            game.log('info', "Das war keiner der Vorschläge. (Tippe 'stop' zum Abbrechen)")