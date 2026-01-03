from engine.handlers.movement import MovementHandler
from engine.handlers.dialogue import DialogueHandler
from engine.handlers.system import SystemHandler
from engine.handlers.exploration import ExplorationHandler
from engine.handlers.inventory import InventoryHandler
from engine.handlers.mechanics import MechanicsHandler

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
        'help': SystemHandler.help
    }

    @staticmethod
    def dispatch(game, verb, args):
        # 1. Check auf ausstehende Interaktionen (z.B. "Benutze X" -> wartet auf "mit Y")
        if game.pending_interaction:
            ActionDispatcher._handle_pending(game, verb, args)
            return

        # 2. Check auf Disambiguierung (User muss wählen zwischen "Rote Taste" und "Blaue Taste")
        if game.disambiguation:
            ActionDispatcher._handle_disambiguation(game, verb, args)
            return

        # 3. Normales Dispatching
        handler_func = ActionDispatcher.COMMAND_MAP.get(verb)
        if handler_func:
            handler_func(game, args)
            return

        # 4. Fallback: Ist das Verb vielleicht eine Richtung? ("norden" statt "gehe norden")
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
        
        # Wir bauen den Namen des zweiten Items aus dem neuen Input
        item2_name = f"{verb} {' '.join(args)}".strip()
        item1_name = " ".join(item1_args)
        
        if original_verb == 'use':
            # Kombinations-Logik aufrufen
            result_msg = game.perform_combine(item1_name, item2_name)
            if "Fehler" in result_msg or "nicht" in result_msg.lower(): 
                game.log('error', result_msg)
            else: 
                game.log('success', result_msg)
                game.tick(2)
        
        # Reset
        game.pending_interaction = None

    @staticmethod
    def _handle_disambiguation(game, verb, args):
        state = game.disambiguation
        original_verb = state['verb']
        candidates = state['candidates']
        
        filter_text = f"{verb} {' '.join(args)}".strip().lower()
        
        if filter_text in ["stop", "abbrechen", "nein", "cancel", "zurück"]:
            game.log('info', "Abgebrochen.")
            game.disambiguation = None
            return

        # Filtern der Kandidaten basierend auf User-Input
        matches = []
        for cand in candidates:
            if filter_text in cand['name'].lower() or any(filter_text in a for a in cand.get('aliases', [])):
                matches.append(cand)
        
        if len(matches) == 1:
            # Eindeutig identifiziert -> Befehl erneut ausführen
            target = matches[0]
            game.disambiguation = None 
            game.log('user', f"(Ausgewählt: {target['name']})")
            ActionDispatcher.dispatch(game, original_verb, [target['name']])
        elif len(matches) > 1:
            names = [m['name'] for m in matches]
            game.log('info', f"Das grenzt es nicht genug ein. Meinst du: {', '.join(names)}?")
        else:
            game.log('info', "Das war keiner der Vorschläge. (Tippe 'stop' zum Abbrechen)")