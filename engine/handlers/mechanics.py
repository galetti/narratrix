from engine.resolver import Resolver, ResolutionError
from engine.constants import *
from engine.strings import Texts
from engine.handlers.common import CommonHandler
from engine.handlers.exploration import ExplorationHandler

class MechanicsHandler:

    @staticmethod
    def wait(game, args):
        game.log('info', Texts.WAIT_MSG)
        game.tick(10)

    @staticmethod
    def use(game, args):
        if game.hidden_in: return game.log('error', Texts.ERR_HIDDEN)
        if not args: return game.log('error', Texts.USE_MISSING_ARGS.format("..."))
        
        separators = ["mit", "with", "und", "an", "auf", "on"]
        sep_indices = [i for i, w in enumerate(args) if w.lower() in separators]
        
        item1_name = ""
        item2_name = ""
        
        if sep_indices:
            idx = sep_indices[0]
            item1_name = " ".join(args[:idx])
            item2_name = " ".join(args[idx+1:])
        elif len(args) >= 2:
            item1_name = " ".join(args[:-1])
            item2_name = args[-1]
        else:
            game.log('info', Texts.USE_MISSING_ARGS.format(' '.join(args)))
            game.pending_interaction = {'verb': 'use', 'args': args}
            return
        
        result_msg = game.perform_combine(item1_name, item2_name)
        if "Fehler" in result_msg or "nicht" in result_msg.lower(): 
            game.log('error', result_msg)
        else: 
            game.log('success', result_msg)
            game.tick(2)

    @staticmethod
    def open(game, args):
        if game.hidden_in: return game.log('error', Texts.ERR_HIDDEN)
        if any(sep in args for sep in ["mit", "with", "using"]):
             return MechanicsHandler.use(game, args)

        clean_args = Resolver.clean_args(args)
        try:
            target = Resolver.resolve_target(game, clean_args, location_filter=FILTER_RECURSIVE, verb='open')
            if target: 
                if target.get('type') == TYPE_SURFACE: return game.log('info', Texts.OPEN_SURFACE_ERROR)
                if target.get('type') != TYPE_CONTAINER: return game.log('error', Texts.OPEN_ERROR)
                
                if target.get('is_locked'):
                    key_id = target.get('key_id')
                    if key_id:
                        has_key = any(o[ATTR_ID] == key_id and o['location'] == LOC_INVENTORY for o in game.objects.values())
                        if has_key: 
                            key_obj = game.objects[key_id]
                            game.log('info', Texts.OPEN_KEY_USED.format(key=key_obj[ATTR_NAME]))
                            target['is_locked'] = False
                        else: return game.log('error', Texts.OPEN_LOCKED_KEY)
                    else: 
                        if target.get('state') == STATE_BROKEN:
                             return game.log('error', "Der Mechanismus ist beschädigt. Du musst ihn reparieren.")
                        return game.log('error', Texts.OPEN_LOCKED)
                
                if target.get('is_open'): return game.log('info', Texts.OPEN_ALREADY)
                target['is_open'] = True
                game.log('success', Texts.OPEN_SUCCESS.format(target=target[ATTR_NAME]))
                ExplorationHandler.look(game, clean_args)
        except ResolutionError as e: game.log('error', str(e))

    @staticmethod
    def fix(game, args):
        return MechanicsHandler._generic_action(game, args, 'fix', STATE_BROKEN, Texts.FIX_SUCCESS, Texts.FIX_NOT_BROKEN)

    @staticmethod
    def break_(game, args):
        # 'break' braucht keinen Status, es funktioniert immer, wenn man ein Brecheisen hat
        return MechanicsHandler._generic_action(game, args, 'break', None, "Du hast es aufgebrochen.", "Das lässt sich nicht aufbrechen.")

    @staticmethod
    def put(game, args):
        if game.hidden_in: return game.log('error', Texts.ERR_HIDDEN)
        if not args: return game.log('error', Texts.PUT_MISSING_ARGS)
        
        separators = ["in", "auf", "on", "into", "an"]
        sep_indices = [i for i, w in enumerate(args) if w.lower() in separators]
        item_words = args[:sep_indices[0]] if sep_indices else args[:-1]
        container_words = args[sep_indices[0]+1:] if sep_indices else [args[-1]]
        
        try:
            item = Resolver.resolve_target(game, item_words, location_filter=FILTER_INVENTORY, verb='put_item')
            if item: 
                container = Resolver.resolve_target(game, container_words, location_filter=FILTER_RECURSIVE, verb='put_container')
                if container:
                    if container == item: return game.log('error', Texts.PUT_SAME_ITEM)
                    if container.get('type') not in [TYPE_CONTAINER, TYPE_SURFACE]: return game.log('error', Texts.PUT_ERROR_TYPE)
                    if container.get('type') == TYPE_CONTAINER and not container.get('is_open'): 
                        return game.log('error', Texts.PUT_ERROR_CLOSED.format(container=container[ATTR_NAME]))
                    if container.get('is_scale'):
                        if CommonHandler.is_held_by_player(game, container):
                            return game.log('error', Texts.PUT_SCALE_ERROR)

                    item['location'] = container[ATTR_ID]
                    prep = "auf" if container.get('type') == TYPE_SURFACE else "in"
                    game.log('success', Texts.PUT_SUCCESS.format(item=item[ATTR_NAME], prep=prep, container=container[ATTR_NAME]))
                    game.tick(2)
                    
                    if container.get('is_scale'):
                        contents = [o for o in game.objects.values() if o['location'] == container[ATTR_ID]]
                        total_weight = sum(o.get('weight', 0) for o in contents)
                        game.log('info', f"Das Display der Waage springt an: {total_weight:.2f} kg")
        except ResolutionError as e: game.log('error', str(e))

    @staticmethod
    def _generic_action(game, args, verb, required_state, success_msg, fail_msg):
        if game.hidden_in: return game.log('error', Texts.ERR_HIDDEN)
        clean_args = Resolver.clean_args(args)
        try:
            target = Resolver.resolve_target(game, clean_args, location_filter=FILTER_RECURSIVE, verb=verb)
            if target: 
                if required_state and target.get('state') == required_state: 
                    target['state'] = STATE_NORMAL
                    game.log('success', success_msg)
                    game.tick(15)
                elif verb == 'break' and target.get('type') == TYPE_CONTAINER and target.get('is_locked'):
                    # FIX: Brachiale Methode (Benötigt Brecheisen)
                    prying_tools = [o for o in game.objects.values() if o['location'] == LOC_INVENTORY and o.get('tool_type') == 'prying']
                    if prying_tools:
                        target['is_locked'] = False
                        target['is_open'] = True
                        game.log('success', f"Mit lautem Krachen bricht {target[ATTR_NAME]} auf.")
                        game.tick(5)
                    else:
                        game.log('error', "Du brauchst ein Brecheisen.")
                elif not required_state and verb != 'break':
                    game.log('info', fail_msg)
                else:
                    # Fallback für Break wenn nicht locked oder falsches Ziel
                    game.log('info', fail_msg)
        except ResolutionError as e: game.log('error', str(e))