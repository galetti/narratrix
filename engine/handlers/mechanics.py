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
        
        separator_indices = [i for i, word in enumerate(args) if word.lower() in ["mit", "with", "und", "an"]]
        item1_name = ""
        item2_name = ""
        
        if separator_indices:
            idx = separator_indices[0]
            item1_name = " ".join(args[:idx])
            item2_name = " ".join(args[idx+1:])
        elif len(args) >= 2:
            item1_name = args[0]; item2_name = args[-1]
            if len(args) > 2: mid = len(args) // 2; item1_name = " ".join(args[:mid]); item2_name = " ".join(args[mid:])
        else:
            # Wenn nur 1 Argument: Vielleicht wollte der User später das zweite angeben?
            # Oder das Item hat eine "Single Use" Funktion (hier nicht implementiert, aber vorbereitet)
            game.log('info', Texts.USE_MISSING_ARGS.format(' '.join(args)))
            game.pending_interaction = {'verb': 'use', 'args': args}
            return
        
        # Aufruf des Crafting Systems (im GameState verankert)
        result_msg = game.perform_combine(item1_name, item2_name)
        
        if "Fehler" in result_msg or "nicht" in result_msg.lower(): 
            game.log('error', result_msg)
        else: 
            game.log('success', result_msg)
            game.tick(2)

    @staticmethod
    def open(game, args):
        if game.hidden_in: return game.log('error', Texts.ERR_HIDDEN)
        
        clean_args = Resolver.clean_args(args)
        try:
            target = Resolver.resolve_target(game, clean_args, location_filter=FILTER_RECURSIVE, verb='open')
            if target: 
                if target.get('type') == TYPE_SURFACE: return game.log('info', Texts.OPEN_SURFACE_ERROR)
                
                # Nur Container oder verlinkte Exits (Türen) dürfen geöffnet werden
                if target.get('type') != TYPE_CONTAINER: return game.log('error', Texts.OPEN_ERROR)
                
                # Check auf spezielle Mechanismen (Rost, Elektronik)
                mechanism = target.get('mechanism')
                if mechanism:
                    mech_type = mechanism.get('type')
                    if mech_type == 'rusty':
                        if not mechanism.get('solved', False): 
                            return game.log('error', mechanism.get('fail_msg', Texts.OPEN_RUSTY))
                    elif mech_type == 'electronic':
                        if not mechanism.get('powered', True): 
                            return game.log('error', Texts.OPEN_NO_POWER)
                        if not mechanism.get('unlocked', False): 
                            return game.log('error', mechanism.get('fail_msg', Texts.OPEN_DENIED))

                # Schloss-Logik
                if target.get('is_locked'):
                    key_id = target.get('key_id')
                    if key_id:
                        # Automatisch Schlüssel suchen
                        has_key = any(o[ATTR_ID] == key_id and o['location'] == LOC_INVENTORY for o in game.objects.values())
                        if has_key: 
                            key_obj = game.objects[key_id]
                            game.log('info', Texts.OPEN_KEY_USED.format(key=key_obj[ATTR_NAME]))
                            target['is_locked'] = False
                        else: return game.log('error', Texts.OPEN_LOCKED_KEY)
                    else: return game.log('error', Texts.OPEN_LOCKED)
                
                if target.get('is_open'): return game.log('info', Texts.OPEN_ALREADY)
                
                target['is_open'] = True
                game.log('success', Texts.OPEN_SUCCESS.format(target=target[ATTR_NAME]))
                
                # Automatisch hineinschauen für Komfort
                ExplorationHandler.look(game, clean_args)
        except ResolutionError as e: game.log('error', str(e))

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
                    
                    # Verhindern, dass man die Waage auf sich selbst legt oder ähnliches
                    if container.get('is_scale'):
                        if CommonHandler.is_held_by_player(game, container):
                            return game.log('error', Texts.PUT_SCALE_ERROR)

                    item['location'] = container[ATTR_ID]
                    prep = "auf" if container.get('type') == TYPE_SURFACE else "in"
                    game.log('success', Texts.PUT_SUCCESS.format(item=item[ATTR_NAME], prep=prep, container=container[ATTR_NAME]))
                    game.tick(2)
                    
                    # Waagen-Feedback
                    if container.get('is_scale'):
                        contents = [o for o in game.objects.values() if o['location'] == container[ATTR_ID]]
                        total_weight = sum(o.get('weight', 0) for o in contents)
                        game.log('info', f"Das Display der Waage springt an: {total_weight:.2f} kg")
        except ResolutionError as e: game.log('error', str(e))

    @staticmethod
    def break_(game, args): 
        if game.hidden_in: return game.log('error', Texts.ERR_HIDDEN)
        
        clean_args = Resolver.clean_args(args)
        try:
            target = Resolver.resolve_target(game, clean_args, location_filter=FILTER_RECURSIVE, verb='break')
            if target: 
                if not target.get('type') == TYPE_CONTAINER or not target.get('is_locked'): 
                    return game.log('error', Texts.BREAK_NOT_NEEDED)
                
                key_id = target.get('key_id')
                key_obj = game.objects.get(key_id) if key_id else None
                
                # Fall 1: Mit passendem Schlüssel (Gewaltlos)
                if key_obj and key_obj['location'] == LOC_INVENTORY:
                     game.log('success', Texts.BREAK_SUCCESS.format(tool=key_obj[ATTR_NAME]))
                     target['is_locked'] = False; target['is_open'] = True
                     game.tick(5)
                     ExplorationHandler.look(game, clean_args)
                else: 
                    # Fall 2: Mit Brecheisen (Gewalt)
                    prying_tools = [o for o in game.objects.values() if o['location'] == LOC_INVENTORY and o.get('tool_type') == 'prying']
                    
                    if prying_tools:
                        tool = prying_tools[0]
                        game.log('success', Texts.BREAK_SUCCESS.format(tool=tool[ATTR_NAME]))
                        target['is_locked'] = False; target['is_open'] = True; 
                        game.tick(5)
                        ExplorationHandler.look(game, clean_args)
                    else:
                        game.log('error', Texts.BREAK_NEED_TOOL)
        except ResolutionError as e: game.log('error', str(e))

    @staticmethod
    def fix(game, args):
        if game.hidden_in: return game.log('error', Texts.ERR_HIDDEN)
        
        clean_args = Resolver.clean_args(args)
        try:
            target = Resolver.resolve_target(game, clean_args, location_filter=FILTER_RECURSIVE, verb='fix')
            if target: 
                if target.get('state') in [STATE_SABOTAGED, STATE_BROKEN]: 
                    target['state'] = STATE_NORMAL
                    game.log('success', Texts.FIX_SUCCESS)
                    game.tick(15)
                else: game.log('info', Texts.FIX_NOT_BROKEN)
        except ResolutionError as e: game.log('error', str(e))