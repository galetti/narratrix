from __future__ import annotations

from typing import TYPE_CHECKING, Any

from engine.access import get_connecting_doors, get_door_target_room
from engine.resolver import Resolver, ResolutionError
from engine.constants import (
    ATTR_DESC,
    ATTR_ID,
    ATTR_MATTER,
    ATTR_NAME,
    ATTR_TEMP,
    ATTR_WEIGHT,
    FILTER_INVENTORY,
    FILTER_RECURSIVE,
    FILTER_ROOM,
    LOC_INVENTORY,
    MATTER_LIQUID,
    STATE_BROKEN,
    STATE_SABOTAGED,
    TYPE_CONTAINER,
    TYPE_FIXTURE,
    TYPE_ITEM,
    TYPE_SURFACE,
)
from engine.strings import Texts
from engine.handlers.common import CommonHandler

if TYPE_CHECKING:
    from engine.game_state import GameState


class ExplorationHandler:
    
    @staticmethod
    def hide(game: GameState, args: list[str]) -> None:
        if game.hidden_in:
            return game.log('info', Texts.HIDE_ALREADY)
            
        clean_args = Resolver.clean_args(args)
        try:
            target = Resolver.resolve_target(game, clean_args, location_filter=FILTER_ROOM, verb='hide')
            
            if target:
                if target.get('type') != TYPE_CONTAINER:
                    return game.log('error', Texts.HIDE_ERROR_TYPE)
                
                # Check Size via Weight heuristic (Objekte unter 100kg sind meist zu klein zum Verstecken)
                if target.get(ATTR_WEIGHT, 0) < 100 and target.get(ATTR_WEIGHT, 0) != float('inf'):
                     return game.log('error', Texts.HIDE_ERROR_SIZE)
                
                if not target.get('is_open', True):
                    return game.log('error', Texts.HIDE_ERROR_CLOSED)

                game.hidden_in = target[ATTR_ID]
                game.log('success', Texts.HIDE_SUCCESS.format(target=target[ATTR_NAME]))
                
        except ResolutionError as e: game.log('error', str(e))

    @staticmethod
    def look(game: GameState, args: list[str]) -> None:
        # Wenn versteckt, sieht man nur eingeschränkt
        if game.hidden_in:
            container = game.objects.get(game.hidden_in)
            if container:
                game.log('info', Texts.LOOK_HIDDEN_IN.format(container[ATTR_NAME]))
            
            # Eingeschränkter Blick in den Raum
            visible_npcs = [n[ATTR_NAME] for n in game.npcs if n['location'] == game.location]
            if visible_npcs: 
                game.log('character', Texts.HIDE_SEE_NPCS.format(', '.join(visible_npcs)))
            else: 
                game.log('info', Texts.LOOK_EMPTY)
            return

        room = game.get_room(game.location)
        if not room:
            game.log('error', Texts.LOOK_ROOM_NOT_FOUND)
            return

        if not args:
            # Raum-Name und Beschreibung
            game.log('location', room.get(ATTR_NAME, "Unbekannt"))
            game.log('story', game.render_room_desc(game.location))
            
            # Ausgänge anzeigen
            exits = room.get('exits', {})
            if exits:
                exit_names = [Texts.direction_name(d) for d in exits.keys()]
                game.log('info', Texts.LOOK_EXITS.format(', '.join(exit_names)))
            else: 
                game.log('info', Texts.LOOK_NO_EXITS)

            # Objekte im Raum anzeigen
            visible_objs: list[str] = []
            local_objects = [o for o in game.objects.values() if o['location'] == game.location]
            for door in get_connecting_doors(game, game.location):
                if door not in local_objects:
                    local_objects.append(door)
            
            for obj in local_objects:
                if CommonHandler.is_open_container(obj):
                    content_str = CommonHandler.format_contents_recursive(game, obj[ATTR_ID])
                    if content_str: 
                        msg = (
                            Texts.LOOK_ON_SURFACE.format(name=obj[ATTR_NAME], content=content_str)
                            if obj.get('type') == TYPE_SURFACE
                            else Texts.LOOK_IN_OPEN.format(name=obj[ATTR_NAME], content=content_str)
                        )
                        game.log('info', msg)
                    else:
                        msg = (
                            Texts.LOOK_NOTHING_ON.format(name=obj[ATTR_NAME])
                            if obj.get('type') == TYPE_SURFACE
                            else Texts.LOOK_NOTHING_IN.format(name=obj[ATTR_NAME])
                        )
                        game.log('info', msg)
                
                # Türen/Schotts extra anzeigen (Status)
                elif obj.get('linked_exit'):
                    state = Texts.LOOK_OPEN if obj.get('is_open') else Texts.LOOK_CLOSED
                    game.log('info', Texts.LOOK_DOOR_STATUS.format(name=obj[ATTR_NAME], state=state))
                    
                # Normale Items & Fixtures
                elif (
                    obj.get('type') in (TYPE_ITEM, TYPE_FIXTURE)
                    or (not obj.get('type') and obj.get(ATTR_WEIGHT, float('inf')) < float('inf'))
                ):
                    obj_level = int(obj.get('level', 0))
                    label = obj[ATTR_NAME]
                    if obj_level > game.elevation:
                        label += Texts.LEVEL_INFO_UP.format(level=obj_level)
                    elif obj_level < game.elevation:
                        label += Texts.LEVEL_INFO_DOWN.format(level=obj_level)
                    visible_objs.append(label)
            
            if visible_objs: 
                game.log('info', Texts.LOOK_GROUND.format(', '.join(visible_objs)))
            
            # NPCs anzeigen (inkl. Höhen-Info)
            visible_npcs = CommonHandler.format_visible_npcs(game, game.location)
            if visible_npcs: 
                game.log('character', Texts.LOOK_PERSONS.format(', '.join(visible_npcs)))
            return

        # Gezieltes Anschauen ("schaue kiste")
        clean_args = Resolver.clean_args(args)
        try:
            target = Resolver.resolve_target(game, clean_args, location_filter=FILTER_RECURSIVE, verb='look')
            if target:
                desc = target.get(ATTR_DESC, Texts.LOOK_DEFAULT)
                status: list[str] = []
                
                # Temperatur Info
                temp = target.get(ATTR_TEMP, 20)
                if temp > 50: status.append(Texts.LOOK_HOT)
                elif temp > 30: status.append(Texts.LOOK_WARM)
                elif temp < 5: status.append(Texts.LOOK_COLD)
                
                # Aggregatszustand
                if target.get(ATTR_MATTER) == MATTER_LIQUID: status.append(Texts.LOOK_LIQUID)

                # Waagen-Display
                if target.get('is_scale'):
                    total_weight = CommonHandler.get_contained_weight(game, target[ATTR_ID])
                    status.append(Texts.LOOK_SCALE_DISPLAY.format(total_weight))

                # Container Status
                if target.get('type') in [TYPE_CONTAINER, TYPE_SURFACE]:
                    if target.get('type') == TYPE_CONTAINER and target.get('is_locked'): 
                        status.append(Texts.LOOK_LOCKED)
                    elif CommonHandler.is_open_container(target):
                        content_str = CommonHandler.format_contents_recursive(game, target[ATTR_ID])
                        if content_str: status.append(Texts.LOOK_CONTENT.format(content_str))
                        else: status.append(Texts.LOOK_EMPTY_CONTAINER)
                    elif target.get('type') == TYPE_CONTAINER:
                        if target.get('linked_exit'):
                            status.append(Texts.LOOK_OPEN if target.get('is_open') else Texts.LOOK_CLOSED)
                        else:
                            status.append(Texts.LOOK_CLOSED)
                
                # Defekte / Sabotage
                if target.get('state') == STATE_SABOTAGED: status.append(Texts.LOOK_SABOTAGED)
                if target.get('state') == STATE_BROKEN: status.append(Texts.LOOK_BROKEN)
                
                if status: desc += " " + " ".join(status)
                game.log('story', desc)
        except ResolutionError as e:
            game.log('error', str(e))

    @staticmethod
    def _volume_through_neighbor(
        game: GameState,
        source_id: str,
        listener_id: str,
        target_neighbor_id: str,
        tool_bonus: float = 0.0,
    ) -> float:
        for neighbor, transmission, _ in game.acoustics._neighbors(listener_id):
            if neighbor != target_neighbor_id:
                continue
            effective = transmission
            if tool_bonus and transmission < 0.5:
                effective = min(1.0, transmission + tool_bonus)
            remote = game.acoustics._max_transmission(
                source_id,
                neighbor,
                forbidden={listener_id},
            )
            return remote * effective
        return 0.0

    @staticmethod
    def listen(game: GameState, args: list[str]) -> None:
        if game.hidden_in:
            container = game.objects.get(game.hidden_in)
            if container:
                game.log("info", Texts.LISTEN_FROM_HIDE.format(container=container[ATTR_NAME]))

        # 1. Prüfen auf Werkzeug ("mit <item>")
        tool_words: list[str] = []
        target_words: list[str] = []
        lower_args = [w.lower() for w in args]

        if "mit" in lower_args:
            mit_idx = lower_args.index("mit")
            if mit_idx == 0:
                sep_idx = -1
                for s_i, word in enumerate(lower_args[1:], start=1):
                    if word in {"an", "gegen", "durch", "bei"}:
                        sep_idx = s_i
                        break
                if sep_idx != -1:
                    tool_words = args[1:sep_idx]
                    target_words = args[sep_idx + 1 :]
                else:
                    tool_words = args[1:]
            else:
                target_words = args[:mit_idx]
                tool_words = args[mit_idx + 1 :]
        else:
            target_words = args

        used_tool: dict[str, Any] | None = None
        if tool_words:
            try:
                used_tool = Resolver.resolve_target(
                    game, tool_words, location_filter=FILTER_INVENTORY, verb="listen_tool"
                )
            except ResolutionError as exc:
                game.log("error", str(exc))
                return

        inventory_boost_tool = next(
            (
                obj
                for obj in game.objects.values()
                if obj.get("location") == LOC_INVENTORY
                and float(obj.get("acoustic_boost", 0.0)) > 0.0
            ),
            None,
        )

        clean_target = Resolver.clean_args(target_words)
        if clean_target:
            try:
                target = Resolver.resolve_target(
                    game, clean_target, location_filter=FILTER_RECURSIVE, verb="listen_target"
                )
                if not target:
                    return

                target_room_id = get_door_target_room(game, target, game.location)

                if used_tool or (inventory_boost_tool and not tool_words and target.get("linked_exit")):
                    active_tool = used_tool or inventory_boost_tool
                    if float(active_tool.get("acoustic_boost", 0.0)) <= 0.0:
                        game.log(
                            "info",
                            Texts.LISTEN_TOOL_NO_BOOST.format(
                                tool=active_tool[ATTR_NAME], target=target[ATTR_NAME]
                            ),
                        )
                        return

                    if target_room_id:
                        tool_bonus = float(active_tool.get("acoustic_boost", 0.0))
                        best_vol = 0.0
                        best_event = None
                        for ev in game.events.events:
                            if not ev.get("sound_msg") or not ev.get("origin_id"):
                                continue
                            if not game.events.evaluate_condition(ev.get("condition", {})):
                                continue
                            vol = ExplorationHandler._volume_through_neighbor(
                                game,
                                ev["origin_id"],
                                game.location,
                                target_room_id,
                                tool_bonus=tool_bonus,
                            )
                            if vol > best_vol:
                                best_vol = vol
                                best_event = ev

                        if best_vol >= 0.3 and best_event:
                            game.log(
                                "success",
                                Texts.LISTEN_CLEAR_VOICES.format(
                                    tool=active_tool[ATTR_NAME],
                                    target=target[ATTR_NAME],
                                    message=best_event["sound_msg"],
                                ),
                            )
                            game.add_knowledge("sabotage_plan_uncovered")
                            if "investigate_sabotage" in game.quests.states:
                                game.quests.update_quest("investigate_sabotage", 2)
                                game.quests.complete_quest("investigate_sabotage")
                            if best_event.get("effects"):
                                game.effects.process(best_event["effects"])
                            game.tick(1)
                            return
                        elif best_vol > 0.0:
                            game.log(
                                "info",
                                Texts.LISTEN_MUFFLED.format(
                                    tool=active_tool[ATTR_NAME], target=target[ATTR_NAME]
                                ),
                            )
                            return
                        else:
                            game.log(
                                "info",
                                Texts.LISTEN_ABSOLUTE_SILENCE.format(
                                    tool=active_tool[ATTR_NAME], target=target[ATTR_NAME]
                                ),
                            )
                            return

                if target_room_id:
                    best_vol = 0.0
                    for ev in game.events.events:
                        if not ev.get("sound_msg") or not ev.get("origin_id"):
                            continue
                        if not game.events.evaluate_condition(ev.get("condition", {})):
                            continue
                        vol = ExplorationHandler._volume_through_neighbor(
                            game,
                            ev["origin_id"],
                            game.location,
                            target_room_id,
                            tool_bonus=0.0,
                        )
                        if vol > best_vol:
                            best_vol = vol

                    if best_vol > 0.05:
                        hint = (
                            Texts.LISTEN_DOOR_MUFFLED_NO_TOOL
                            if inventory_boost_tool is None
                            else Texts.LISTEN_DOOR_MUFFLED_WITH_TOOL.format(
                                tool=inventory_boost_tool[ATTR_NAME]
                            )
                        )
                        game.log(
                            "info",
                            Texts.LISTEN_DOOR_MURMURS.format(
                                target=target[ATTR_NAME], hint=hint
                            ),
                        )
                        return
                    else:
                        game.log(
                            "info",
                            Texts.LISTEN_DOOR_SILENCE.format(target=target[ATTR_NAME]),
                        )
                        return

                game.log(
                    "info",
                    Texts.LISTEN_DOOR_NOTHING.format(target=target[ATTR_NAME]),
                )
                return
            except ResolutionError as exc:
                game.log("error", str(exc))
                return

        audible_count = 0
        for event in game.events.events:
            origin = event.get("origin_id")
            if not origin or "sound_msg" not in event:
                continue
            if not game.events.evaluate_condition(event.get("condition", {})):
                continue

            vol, direction = game.acoustics.get_audibility_info(
                origin, game.location, use_player_tools=bool(inventory_boost_tool)
            )
            heard_volume = min(1.0, vol * float(event.get("volume", 1.0)))
            if heard_volume > 0.05:
                audible_count += 1
                prefix = (
                    Texts.LISTEN_PREFIX_QUIET
                    if heard_volume < 0.3
                    else (Texts.LISTEN_PREFIX_LOUD if heard_volume > 0.8 else "")
                )
                dir_txt = direction[0].upper() + direction[1:] if direction else Texts.LISTEN_SOMEWHERE
                game.log(
                    "event",
                    Texts.LISTEN_HEAR_SOUND.format(
                        direction=dir_txt, prefix=prefix, sound=event["sound_msg"]
                    ),
                )

        if audible_count == 0:
            game.log(
                "info",
                Texts.LISTEN_QUIET_STATION,
            )
        game.tick(1)
