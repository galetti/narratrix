from engine.resolver import Resolver, ResolutionError
from engine.constants import *
from engine.strings import Texts
from engine.handlers.common import CommonHandler
# Import von DialogueHandler entfernt

class InventoryHandler:

    @staticmethod
    def inventory(game, args):
        items = [o for o in game.objects.values() if o['location'] == LOC_INVENTORY]
        display_list = []
        for item in items:
            name = item[ATTR_NAME]
            # Wenn das Item selbst ein Container ist (z.B. Rucksack)
            if CommonHandler.is_open_container(item):
                content_str = CommonHandler.format_contents_recursive(game, item[ATTR_ID])
                if content_str: name += f" (enthält: {content_str})"
                else: name += " (leer)"
            elif item.get('type') == TYPE_CONTAINER: name += " (geschlossen)"
            display_list.append(name)
            
        if not display_list: game.log('info', Texts.INV_EMPTY)
        else: game.log('info', Texts.INV_LIST.format(', '.join(display_list)))

    @staticmethod
    def take(game, args):
        if game.hidden_in: return game.log('error', Texts.ERR_HIDDEN)
        
        # Spezialfall: "nimm alles"
        if any(w in args for w in ["all", "alles", "alle"]):
            candidates = Resolver._collect_candidates(game, FILTER_RECURSIVE)
            # Nur Dinge, die nicht schon im Inventar sind und tragbar sind
            candidates = [o for o in candidates if o['location'] != LOC_INVENTORY and o.get(ATTR_WEIGHT, float('inf')) < float('inf')]
            taken = []
            for item in candidates:
                if item.get(ATTR_MATTER) == MATTER_LIQUID: continue 
                item['location'] = LOC_INVENTORY
                taken.append(item[ATTR_NAME])
            if taken:
                game.log('success', f"Genommen: {', '.join(taken)}")
                game.tick(len(taken))
            else: game.log('info', Texts.TAKE_NOTHING)
            return

        clean_args = Resolver.clean_args(args)
        try:
            target = Resolver.resolve_target(game, clean_args, location_filter=FILTER_RECURSIVE, verb='take')
            if target:
                if target['location'] == LOC_INVENTORY: return game.log('info', Texts.TAKE_ALREADY)
                weight = target.get(ATTR_WEIGHT, float('inf'))
                if weight == float('inf'): return game.log('error', Texts.TAKE_TOO_HEAVY)
                if target.get(ATTR_MATTER) == MATTER_LIQUID: return game.log('error', Texts.TAKE_LIQUID_ERROR)

                target['location'] = LOC_INVENTORY
                game.log('success', Texts.TAKE_SUCCESS.format(item=target[ATTR_NAME]))
                
                # Logic: Wenn man ein Tablett nimmt, kommen die Sachen drauf mit
                if target.get('type') == TYPE_SURFACE:
                    contents = [o for o in game.objects.values() if o['location'] == target[ATTR_ID]]
                    if contents:
                        names = []
                        for item in contents:
                            item['location'] = LOC_INVENTORY
                            names.append(item[ATTR_NAME])
                        if names: game.log('info', f"Du verstaust auch: {', '.join(names)}.")
                
                game.tick(1)
        except ResolutionError as e: game.log('error', str(e))

    @staticmethod
    def drop(game, args):
        if game.hidden_in: return game.log('error', Texts.ERR_HIDDEN)
        
        clean_args = Resolver.clean_args(args)
        try:
            target = Resolver.resolve_target(game, clean_args, location_filter=FILTER_INVENTORY, verb='drop')
            if target: 
                target['location'] = game.location
                game.log('success', Texts.DROP_SUCCESS.format(item=target[ATTR_NAME]))
                game.tick(1)
        except ResolutionError as e: game.log('error', str(e))

    @staticmethod
    def give(game, args):
        if game.hidden_in: return game.log('error', Texts.ERR_HIDDEN)
        
        if not args: return game.log('error', Texts.GIVE_MISSING_ARGS)
        
        # Parsing "gib X an Y"
        separators = ["an", "to", "dem", "der"]
        sep_indices = [i for i, w in enumerate(args) if w.lower() in separators]
        item_words = args[:sep_indices[0]] if sep_indices else args[:-1]
        npc_words = args[idx+1:] if sep_indices else [args[-1]]
        
        try:
            item = Resolver.resolve_target(game, item_words, location_filter=FILTER_INVENTORY, verb='give_item')
            if item:
                npc = Resolver.find_mentioned_npc(game, npc_words)
                if not npc: return game.log('error', Texts.GIVE_NPC_NOT_HERE)
                
                trigger_ids = [f"received_{item[ATTR_ID]}"]
                if item.get('type') == TYPE_CONTAINER:
                    contents = [o for o in game.objects.values() if o['location'] == item[ATTR_ID]]
                    for c in contents: trigger_ids.append(f"received_{c[ATTR_ID]}")
                
                current_state = npc.get('state', 'default')
                
                # State Handling
                dialogue_root = {}
                if 'states' in npc:
                    dialogue_root = npc['states'].get(current_state, {}).get('dialogue', {})
                else:
                    dialogue_root = npc.get('dialogue', {}).get(current_state, {})

                reaction_entry = None
                for topic, entry in dialogue_root.items():
                    if isinstance(entry, dict) and 'condition' in entry:
                        cond = entry['condition']
                        if isinstance(cond, dict) and cond.get('type') == 'knowledge' and cond.get('value') in trigger_ids: 
                            reaction_entry = entry; break
                        elif isinstance(cond, str) and cond in trigger_ids: 
                            reaction_entry = entry; break
                
                if reaction_entry:
                    game.log('success', Texts.GIVE_SUCCESS.format(item=item[ATTR_NAME], npc=npc[ATTR_NAME]))
                    item['location'] = LOC_VOID 
                    for t_id in trigger_ids: game.add_knowledge(t_id)
                    
                    # LOCAL IMPORT FIX: Import hier, um Zirkelschluss zu verhindern
                    from engine.handlers.dialogue import DialogueHandler
                    
                    game.dialogue_active = True
                    game.dialogue_partner = npc
                    game.log('event', f"--- GESPRÄCH MIT {npc[ATTR_NAME].upper()} ---")
                    DialogueHandler._print_dialogue(game, npc, reaction_entry)
                    DialogueHandler.process_effects(game, reaction_entry, npc)
                else: 
                    game.log('character', Texts.GIVE_REFUSED.format(npc=npc[ATTR_NAME]))
        except ResolutionError as e: game.log('error', str(e))