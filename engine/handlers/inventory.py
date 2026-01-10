# narratrix_engine/engine/handlers/inventory.py
from engine.resolver import Resolver, ResolutionError
from engine.constants import *
from engine.strings import Texts
from engine.handlers.common import CommonHandler

class InventoryHandler:

    @staticmethod
    def inventory(game, args):
        """Zeigt das Inventar an, gruppiert Ressourcen."""
        items = [o for o in game.objects.values() if o['location'] == LOC_INVENTORY]
        
        display_list = []
        
        # 1. Normale Items sammeln
        normal_items = []
        # 2. Ressourcen sammeln (Dict: id -> {name, count})
        resources = {}
        
        for item in items:
            if item.get('is_resource'):
                r_id = item[ATTR_ID]
                count = item.get('count', 1)
                
                if r_id in resources:
                    resources[r_id]['count'] += count
                else:
                    resources[r_id] = {
                        'name': item[ATTR_NAME],
                        'count': count,
                        'obj': item
                    }
            else:
                normal_items.append(item)
                
        # 3. Ressourcen formatieren
        for res in resources.values():
            display_list.append(f"{res['count']}x {res['name']}")
            
        # 4. Normale Items formatieren
        for item in normal_items:
            name = item[ATTR_NAME]
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
        
        if any(w in args for w in ["all", "alles", "alle"]):
            candidates = Resolver._collect_candidates(game, FILTER_RECURSIVE)
            candidates = [o for o in candidates if o['location'] != LOC_INVENTORY and o.get(ATTR_WEIGHT, float('inf')) < float('inf')]
            taken = []
            for item in candidates:
                if item.get(ATTR_MATTER) == MATTER_LIQUID: continue
                
                # Ressource Merge Check
                if item.get('is_resource'):
                    existing = InventoryHandler._find_resource_in_inventory(game, item[ATTR_ID])
                    if existing:
                        existing['count'] = existing.get('count', 1) + item.get('count', 1)
                        item['location'] = LOC_VOID # Original entfernen (Merge)
                        taken.append(f"{item.get('count',1)}x {item[ATTR_NAME]}")
                        continue
                
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

                # Ressource Merge Check (Einzelaufnahme)
                if target.get('is_resource'):
                    existing = InventoryHandler._find_resource_in_inventory(game, target[ATTR_ID])
                    if existing:
                        amount = target.get('count', 1)
                        existing['count'] = existing.get('count', 1) + amount
                        target['location'] = LOC_VOID # Original entfernen
                        game.log('success', f"Du nimmst {amount}x {target[ATTR_NAME]} (Total: {existing['count']}).")
                        game.tick(1)
                        return

                target['location'] = LOC_INVENTORY
                game.log('success', Texts.TAKE_SUCCESS.format(item=target[ATTR_NAME]))
                
                if target.get('type') == TYPE_SURFACE:
                    contents = [o for o in game.objects.values() if o['location'] == target[ATTR_ID]]
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
                # TODO: Optional "drop 5 scrap" parsing
                target['location'] = game.location
                game.log('success', Texts.DROP_SUCCESS.format(item=target[ATTR_NAME]))
                game.tick(1)
        except ResolutionError as e: game.log('error', str(e))

    @staticmethod
    def give(game, args):
        if game.hidden_in: return game.log('error', Texts.ERR_HIDDEN)
        
        if not args: return game.log('error', Texts.GIVE_MISSING_ARGS)
        
        separators = ["an", "to", "dem", "der"]
        sep_indices = [i for i, w in enumerate(args) if w.lower() in separators]
        
        if sep_indices:
            idx = sep_indices[0]
            item_words = args[:idx]
            npc_words = args[idx+1:]
        else:
            item_words = args[:-1]
            npc_words = [args[-1]]
        
        try:
            item = Resolver.resolve_target(game, item_words, location_filter=FILTER_INVENTORY, verb='give_item')
            if item:
                npc = Resolver.find_mentioned_npc(game, npc_words)
                if not npc: return game.log('error', Texts.GIVE_NPC_NOT_HERE)
                
                trigger_ids = [f"received_{item[ATTR_ID]}"]
                if item.get('type') == TYPE_CONTAINER:
                    contents = [o for o in game.objects.values() if o['location'] == item[ATTR_ID]]
                    for c in contents: trigger_ids.append(f"received_{c[ATTR_ID]}")
                
                # Check Reaction
                current_state = npc.get('state', 'default')
                dialogue_db = {}
                if 'states' in npc:
                    dialogue_db = npc['states'].get(current_state, {}).get('dialogue', {})
                else:
                    dialogue_db = npc.get('dialogue', {}).get(current_state, {})

                reaction_entry = None
                for topic, entry in dialogue_db.items():
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
                    
                    # NEU: Nutzung des DialogueSystems anstelle des Handlers
                    game.dialogue_active = True
                    game.dialogue_partner = npc
                    
                    game.log('event', f"--- GESPRÄCH MIT {npc[ATTR_NAME].upper()} ---")
                    game.dialogue_system.print_dialogue(npc, reaction_entry)
                    
                    # Effekte via EffectProcessor (Delegation)
                    if 'effect' in reaction_entry:
                         game.effects.process(reaction_entry['effect'], context_npc=npc)
                else: 
                    game.log('character', Texts.GIVE_REFUSED.format(npc=npc[ATTR_NAME]))
        except ResolutionError as e: game.log('error', str(e))

    @staticmethod
    def _find_resource_in_inventory(game, item_id):
        """Hilfsfunktion: Findet existierenden Ressourcen-Stack im Inventar."""
        for obj in game.objects.values():
            if obj['location'] == LOC_INVENTORY and obj[ATTR_ID] == item_id and obj.get('is_resource'):
                return obj
        return None