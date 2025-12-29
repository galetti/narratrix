from engine.handlers.movement import MovementHandler
from engine.handlers.interaction import InteractionHandler
from engine.handlers.dialogue import DialogueHandler
from engine.handlers.system import SystemHandler
from engine.resolver import Resolver

class ActionDispatcher:
    COMMAND_MAP = {
        # Interaction
        'look': InteractionHandler.look, 'l': InteractionHandler.look, 'x': InteractionHandler.look,
        'take': InteractionHandler.take, 'get': InteractionHandler.take, 'nimm': InteractionHandler.take,
        'drop': InteractionHandler.drop_item,
        'put': InteractionHandler.put,
        'inv': InteractionHandler.inventory, 'i': InteractionHandler.inventory, 'inventory': InteractionHandler.inventory,
        'use': InteractionHandler.use, 'combine': InteractionHandler.use,
        'open': InteractionHandler.open,
        'break': InteractionHandler.break_,
        'fix': InteractionHandler.fix,
        'give': InteractionHandler.give, 'gib': InteractionHandler.give,
        'wait': InteractionHandler.wait, 'warte': InteractionHandler.wait,
        'hide': InteractionHandler.hide, 'verstecke': InteractionHandler.hide, # NEU

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
        if game.pending_interaction:
            ActionDispatcher._handle_pending(game, verb, args)
            return
        if game.disambiguation:
            ActionDispatcher._handle_disambiguation(game, verb, args)
            return

        handler_func = ActionDispatcher.COMMAND_MAP.get(verb)
        if handler_func:
            handler_func(game, args)
            return

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
        original_verb = state['verb']
        candidates = state['candidates']
        filter_text = f"{verb} {' '.join(args)}".strip().lower()
        
        if filter_text in ["stop", "abbrechen", "nein", "cancel", "zurück"]:
            game.log('info', "Abgebrochen.")
            game.disambiguation = None
            return

        matches = []
        for cand in candidates:
            if filter_text in cand['name'].lower() or any(filter_text in a for a in cand.get('aliases', [])):
                matches.append(cand)
        
        if len(matches) == 1:
            target = matches[0]
            game.disambiguation = None 
            game.log('user', f"(Ausgewählt: {target['name']})")
            ActionDispatcher.dispatch(game, original_verb, [target['name']])
        elif len(matches) > 1:
            names = [m['name'] for m in matches]
            game.log('info', f"Das grenzt es nicht genug ein. Meinst du: {', '.join(names)}?")
        else:
            game.log('info', "Das war keiner der Vorschläge. (Tippe 'stop' zum Abbrechen)")