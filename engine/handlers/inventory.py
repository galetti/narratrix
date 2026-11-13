# narratrix_engine/engine/handlers/inventory.py
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from engine.resolver import Resolver, ResolutionError
from engine.constants import (
    ATTR_ID,
    ATTR_MATTER,
    ATTR_NAME,
    ATTR_WEIGHT,
    FILTER_INVENTORY,
    FILTER_RECURSIVE,
    LOC_INVENTORY,
    LOC_VOID,
    MATTER_LIQUID,
    TYPE_CONTAINER,
    TYPE_FIXTURE,
    TYPE_SCENERY,
    TYPE_SURFACE,
)
from engine.strings import Texts
from engine.handlers.common import CommonHandler
from engine.access import (
    _root_entity_and_location,
    is_directly_reachable,
    reach_error,
)
from engine.schema import DialogueOptionData, ObjectData

if TYPE_CHECKING:
    from engine.game_state import GameState


class InventoryHandler:

    @staticmethod
    def inventory(game: GameState, args: list[str]) -> None:
        items = [o for o in game.objects.values() if o['location'] == LOC_INVENTORY]
        
        display_list: list[str] = []
        normal_items: list[ObjectData] = []
        resources: dict[str, dict[str, Any]] = {}
        
        for item in items:
            if item.get('is_resource'):
                r_id = item.get('resource_id', item[ATTR_ID])
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
                
        for res in resources.values():
            display_list.append(f"{res['count']}x {res['name']}")
            
        for item in normal_items:
            name = item[ATTR_NAME]
            if CommonHandler.is_open_container(item):
                content_str = CommonHandler.format_contents_recursive(game, item[ATTR_ID])
                if content_str: name += Texts.INV_CONTAINS.format(content_str)
                else: name += Texts.INV_EMPTY_CONTAINER_LABEL
            elif item.get('type') == TYPE_CONTAINER: name += Texts.INV_CLOSED_CONTAINER_LABEL
            display_list.append(name)
            
        if not display_list: game.log('info', Texts.INV_EMPTY)
        else: game.log('info', Texts.INV_LIST.format(', '.join(display_list)))

    @staticmethod
    def take(game: GameState, args: list[str]) -> None:
        if game.hidden_in: return game.log('error', Texts.ERR_HIDDEN)
        
        # Check "take X with Y"
        separators = ["mit", "with", "using"]
        sep_indices = [i for i, w in enumerate(args) if w.lower() in separators]
        
        item_words = args
        tool_words: list[str] = []
        
        if sep_indices:
            idx = sep_indices[0]
            item_words = args[:idx]
            tool_words = args[idx+1:]

        if any(w.lower() in {"all", "alles", "alle"} for w in args):
            # Alles nehmen (nur reachable)
            candidates = Resolver._collect_candidates(game, FILTER_RECURSIVE)
            object_identities = {id(obj) for obj in game.objects.values()}
            candidates = [
                obj for obj in candidates
                if id(obj) in object_identities
                and obj['location'] != LOC_INVENTORY
                and InventoryHandler._is_takeable(obj)
                and obj.get(ATTR_WEIGHT, float('inf')) < float('inf')
            ]
            taken: list[str] = []
            for item in candidates:
                if item.get(ATTR_MATTER) == MATTER_LIQUID: continue
                
                # Check Reach (Reichweite)
                if not is_directly_reachable(game, item, upward_reach=1):
                    continue

                if item.get('is_resource'):
                    existing = InventoryHandler._find_resource_in_inventory(game, item[ATTR_ID])
                    if existing:
                        existing['count'] = existing.get('count', 1) + item.get('count', 1)
                        item['location'] = LOC_VOID 
                        taken.append(f"{item.get('count',1)}x {item[ATTR_NAME]}")
                        continue
                
                item['location'] = LOC_INVENTORY
                taken.append(item[ATTR_NAME])
                
            if taken:
                game.log('success', Texts.TAKE_ALL_SUCCESS.format(', '.join(taken)))
                game.tick(len(taken))
            else: game.log('info', Texts.TAKE_ALL_NOTHING)
            return

        clean_args = Resolver.clean_args(item_words)
        try:
            target = Resolver.resolve_target(game, clean_args, location_filter=FILTER_RECURSIVE, verb='take')
            if target:
                if not any(target is obj for obj in game.objects.values()):
                    return game.log('error', Texts.TAKE_CANNOT_PERSON)
                if target['location'] == LOC_INVENTORY: return game.log('info', Texts.TAKE_ALREADY)
                if not InventoryHandler._is_takeable(target):
                    return game.log('error', Texts.TAKE_TOO_HEAVY)
                
                # Vertikaler Check über zentrale Reichweitenlogik
                item_level = int(target.get('level', 0))
                player_level = game.elevation
                is_reachable = is_directly_reachable(game, target, upward_reach=1)
                
                if not is_reachable:
                    _, root_loc, blocked_by_container = _root_entity_and_location(game, target)
                    if blocked_by_container or root_loc not in (game.location, LOC_INVENTORY):
                        game.log('error', reach_error(game, target))
                        return

                    dist = abs(item_level - player_level)
                    
                    # Tool Check
                    if tool_words:
                        try:
                            tool = Resolver.resolve_target(game, tool_words, location_filter=FILTER_INVENTORY, verb='tool')
                            if not tool:
                                game.log('error', Texts.TOOL_NOT_IN_INVENTORY)
                                return
                            reach = int(tool.get('reach', 0))
                            if reach >= dist and is_directly_reachable(
                                game,
                                target,
                                upward_reach=max(1, reach),
                                allow_below=True,
                            ):
                                game.log(
                                    'info',
                                    Texts.TOOL_USE_TO_REACH.format(
                                        tool=tool[ATTR_NAME], target=target[ATTR_NAME]
                                    ),
                                )
                            else:
                                game.log(
                                    'error',
                                    Texts.TOOL_NOT_LONG_ENOUGH.format(tool=tool[ATTR_NAME]),
                                )
                                return
                        except ResolutionError:
                            game.log('error', Texts.TOOL_NOT_IN_INVENTORY)
                            return
                    else:
                        # Kein Tool
                        if item_level > player_level + 1:
                            game.log(
                                'error',
                                Texts.REACH_TOO_HIGH.format(
                                    target=target[ATTR_NAME], level=item_level
                                ),
                            )
                            return
                        if item_level < player_level:
                            game.log(
                                'error',
                                Texts.REACH_TOO_LOW.format(
                                    target=target[ATTR_NAME], level=item_level
                                ),
                            )
                            return
                        game.log('error', reach_error(game, target))
                        return

                weight = CommonHandler.get_total_weight(game, target)
                if weight == float('inf') or target.get(ATTR_WEIGHT, float('inf')) == float('inf'):
                    return game.log('error', Texts.TAKE_TOO_HEAVY)
                if target.get(ATTR_MATTER) == MATTER_LIQUID: return game.log('error', Texts.TAKE_LIQUID_ERROR)

                if target.get('is_resource'):
                    existing = InventoryHandler._find_resource_in_inventory(game, target[ATTR_ID])
                    if existing:
                        amount = target.get('count', 1)
                        existing['count'] = existing.get('count', 1) + amount
                        target['location'] = LOC_VOID 
                        game.log(
                            'success',
                            Texts.TAKE_RESOURCE_SUCCESS.format(
                                amount=amount,
                                item=target[ATTR_NAME],
                                total=existing['count'],
                            ),
                        )
                        game.tick(1)
                        return

                target['location'] = LOC_INVENTORY
                game.log('success', Texts.TAKE_SUCCESS.format(item=target[ATTR_NAME]))
                
                # Items IN target auch mitnehmen?
                if target.get('type') == TYPE_SURFACE:
                    contents = [o for o in game.objects.values() if o['location'] == target[ATTR_ID]]
                    names: list[str] = []
                    for item in contents:
                        item['location'] = LOC_INVENTORY
                        names.append(item[ATTR_NAME])
                    if names: game.log('info', Texts.TAKE_STORED_ALSO.format(', '.join(names)))
                
                game.tick(1)
        except ResolutionError as e: game.log('error', str(e))

    @staticmethod
    def drop(game: GameState, args: list[str]) -> None:
        if game.hidden_in: return game.log('error', Texts.ERR_HIDDEN)
        
        clean_args = Resolver.clean_args(args)
        try:
            target = Resolver.resolve_target(game, clean_args, location_filter=FILTER_INVENTORY, verb='drop')
            if target:
                target['location'] = game.location
                # Item landet auf aktueller Ebene
                target['level'] = game.elevation
                
                game.log('success', Texts.DROP_SUCCESS.format(item=target[ATTR_NAME]))
                game.tick(1)
        except ResolutionError as e: game.log('error', str(e))

    @staticmethod
    def give(game: GameState, args: list[str]) -> None:
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
                if not is_directly_reachable(game, npc):
                    return game.log('error', reach_error(game, npc))
                
                trigger_ids = [f"received_{item[ATTR_ID]}"]
                if item.get('type') == TYPE_CONTAINER:
                    contents = [o for o in game.objects.values() if o['location'] == item[ATTR_ID]]
                    for c in contents: trigger_ids.append(f"received_{c[ATTR_ID]}")
                
                current_state = npc.get('state', 'default')
                dialogue_db = {}
                if 'states' in npc:
                    dialogue_db = npc['states'].get(current_state, {}).get('dialogue', {})
                else:
                    dialogue_db = npc.get('dialogue', {}).get(current_state, {})

                reaction_entry: DialogueOptionData | None = None
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
                    for obj in game.objects.values():
                        if obj.get('location') == item[ATTR_ID]:
                            obj['location'] = LOC_VOID
                    for t_id in trigger_ids: game.add_knowledge(t_id)
                    
                    game.dialogue_active = True
                    game.dialogue_partner = npc
                    
                    game.log(
                        'event',
                        Texts.DIALOGUE_HEADER.format(npc=npc[ATTR_NAME].upper()),
                    )
                    game.dialogue_system.print_dialogue(npc, reaction_entry)
                    
                    if 'effect' in reaction_entry:
                         game.effects.process(reaction_entry['effect'], context_npc=npc)
                    game.tick(1)
                else: 
                    game.log('character', Texts.GIVE_REFUSED.format(npc=npc[ATTR_NAME]))
        except ResolutionError as e: game.log('error', str(e))

    @staticmethod
    def _find_resource_in_inventory(game: GameState, item_id: str) -> ObjectData | None:
        target = game.objects.get(item_id)
        resource_id = target.get('resource_id', item_id) if target else item_id
        for obj in game.objects.values():
            if (
                obj['location'] == LOC_INVENTORY
                and obj.get('resource_id', obj[ATTR_ID]) == resource_id
                and obj.get('is_resource')
            ):
                return obj
        return None

    @staticmethod
    def _is_takeable(obj: dict[str, Any]) -> bool:
        if obj.get('movable') is True:
            return True
        if obj.get('linked_exit'):
            return False
        return obj.get('type') not in {TYPE_FIXTURE, TYPE_SURFACE, TYPE_SCENERY}
