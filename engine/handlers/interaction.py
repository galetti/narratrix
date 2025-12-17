from engine.resolver import Resolver
from engine.constants import *

class InteractionHandler:
    @staticmethod
    def look(game, args):
        room = game.get_room(game.location)
        if not args:
            game.log('location', room[ATTR_NAME])
            game.log('story', game.render_room_desc(game.location))
            
            exits = room.get('exits', {})
            if exits:
                trans = {"north": "Norden", "south": "Süden", "east": "Osten", "west": "Westen", "up": "Oben", "down": "Unten"}
                exit_names = [trans.get(d, d.capitalize()) for d in exits.keys()]
                game.log('info', f"Ausgänge: {', '.join(exit_names)}")
            else: game.log('info', "Es gibt keinen sichtbaren Ausweg.")

            visible_objs = []
            local_objects = [o for o in game.objects.values() if o['location'] == game.location]
            for obj in local_objects:
                if obj.get('type') == TYPE_SURFACE:
                    contents = [sub[ATTR_NAME] for sub in game.objects.values() if sub['location'] == obj[ATTR_ID]]
                    if contents: game.log('info', f"Auf dem {obj[ATTR_NAME]}: {', '.join(contents)}")
                elif obj.get('type') == TYPE_CONTAINER and obj.get('is_open'):
                    contents = [sub[ATTR_NAME] for sub in game.objects.values() if sub['location'] == obj[ATTR_ID]]
                    if contents: game.log('info', f"Im offenen {obj[ATTR_NAME]}: {', '.join(contents)}")
                elif obj.get('type') == TYPE_ITEM or (not obj.get('type') and obj.get(ATTR_MOVABLE)):
                     visible_objs.append(obj[ATTR_NAME])
            if visible_objs: game.log('info', f"Am Boden: {', '.join(visible_objs)}")
            visible_npcs = [n[ATTR_NAME] for n in game.npcs if n['location'] == game.location]
            if visible_npcs: game.log('character', f"Personen: {', '.join(visible_npcs)}")
            return

        clean_args = Resolver.clean_args(args)
        target = Resolver.resolve_target(game, clean_args, location_filter=FILTER_RECURSIVE, verb='look')
        
        if target:
            desc = target.get(ATTR_DESC, "Nichts Besonderes.")
            status = []
            
            temp = target.get(ATTR_TEMP, 20)
            if temp > 50: status.append("Es ist HEISS.")
            elif temp > 30: status.append("Es ist warm.")
            elif temp < 5: status.append("Es ist eiskalt.")
            
            if target.get(ATTR_MATTER) == MATTER_LIQUID: status.append("Es ist flüssig.")

            if target.get('type') == TYPE_CONTAINER:
                if target.get('is_locked'): status.append("Verschlossen.")
                elif target.get('is_open'):
                    contents = [o[ATTR_NAME] for o in game.objects.values() if o['location'] == target[ATTR_ID]]
                    if contents: status.append(f"Inhalt: {', '.join(contents)}")
                    else: status.append("Leer.")
                else: status.append("Geschlossen.")
            elif target.get('type') == TYPE_SURFACE:
                contents = [o[ATTR_NAME] for o in game.objects.values() if o['location'] == target[ATTR_ID]]
                if contents: status.append(f"Darauf liegt: {', '.join(contents)}")
                else: status.append("Leer.")
            if target.get('state') == STATE_SABOTAGED: status.append("[WARNUNG: SABOTIERT]")
            if target.get('state') == STATE_BROKEN: status.append("[DEFEKT]")
            
            if status: desc += " " + " ".join(status)
            game.log('story', desc)
        else:
            game.log('error', "Das siehst du hier nicht.")

    @staticmethod
    def take(game, args):
        if any(w in args for w in ["all", "alles", "alle"]):
            candidates = [o for o in game.objects.values() if o.get(ATTR_MOVABLE)]
            taken = []
            for item in candidates:
                if item.get(ATTR_MATTER) == MATTER_LIQUID: continue 
                
                loc_id = item['location']
                can_take = False
                if loc_id == game.location: can_take = True
                else:
                    container = game.objects.get(loc_id)
                    if container and container['location'] == game.location:
                        if container.get('type') == TYPE_SURFACE: can_take = True
                        elif container.get('type') == TYPE_CONTAINER and container.get('is_open'): can_take = True
                if can_take:
                    item['location'] = LOC_INVENTORY
                    taken.append(item[ATTR_NAME])
            if taken:
                game.log('success', f"Genommen: {', '.join(taken)}")
                game.tick(len(taken))
            else:
                game.log('info', "Hier gibt es nichts zum Mitnehmen.")
            return

        clean_args = Resolver.clean_args(args)
        target = Resolver.resolve_target(game, clean_args, location_filter=FILTER_RECURSIVE, verb='take')
        
        if target:
            if target['location'] == LOC_INVENTORY:
                game.log('info', "Hast du schon.")
                return
            elif not target.get(ATTR_MOVABLE):
                game.log('error', "Das ist fest verankert.")
                return
            
            if target.get(ATTR_MATTER) == MATTER_LIQUID:
                game.log('error', "Das kannst du nicht mit den bloßen Händen nehmen. Du brauchst einen Behälter.")
                return

            parent_id = target['location']
            if parent_id != game.location:
                parent = game.objects.get(parent_id)
                if parent and parent.get('type') == TYPE_CONTAINER and not parent.get('is_open'):
                    game.log('info', f"(Ich öffne zuerst den {parent[ATTR_NAME]}.)")
                    InteractionHandler.open(game, [parent[ATTR_NAME]])
                    if not parent.get('is_open'): return 

            target['location'] = LOC_INVENTORY
            game.log('success', f"{target[ATTR_NAME]} genommen.")
            game.tick(1)
        else:
            game.log('error', "Nicht gefunden.")

    @staticmethod
    def give(game, args):
        separators = ["an", "to", "dem", "der"]
        sep_indices = [i for i, w in enumerate(args) if w.lower() in separators]
        
        item_words = []
        npc_words = []
        
        if sep_indices:
            idx = sep_indices[0]
            item_words = args[:idx]
            npc_words = args[idx+1:]
        else:
            if len(args) < 2: return game.log('error', "Was an wen?")
            item_words = args[:-1]
            npc_words = [args[-1]]
            
        item = Resolver.resolve_target(game, item_words, location_filter=FILTER_INVENTORY, verb='give_item')
        if not item: return game.log('error', "Das hast du nicht.")
        
        npc = Resolver.find_mentioned_npc(game, npc_words)
        if not npc: return game.log('error', "Diese Person ist nicht hier.")
        
        game.log('success', f"Du gibst {item[ATTR_NAME]} an {npc[ATTR_NAME]}.")
        item['location'] = LOC_VOID 
        
        trigger_ids = [f"received_{item[ATTR_ID]}"]
        game.add_knowledge(trigger_ids[0])
        
        if item.get('type') == TYPE_CONTAINER:
            contents = [o for o in game.objects.values() if o['location'] == item[ATTR_ID]]
            for c in contents:
                k_id = f"received_{c[ATTR_ID]}"
                game.add_knowledge(k_id)
                trigger_ids.append(k_id)

        from engine.handlers.dialogue import DialogueHandler
        
        current_state = npc.get('state', 'default')
        dialogue_root = npc.get('dialogue', {})
        state_db = dialogue_root.get(current_state, {})
        
        reaction_entry = None
        
        for topic, entry in state_db.items():
            if isinstance(entry, dict) and 'condition' in entry:
                cond = entry['condition']
                if cond.get('type') == 'knowledge' and cond.get('value') in trigger_ids:
                    reaction_entry = entry
                    break
                elif isinstance(cond, str) and cond in trigger_ids:
                    reaction_entry = entry
                    break
        
        if reaction_entry:
            game.dialogue_active = True
            game.dialogue_partner = npc
            game.log('event', f"--- GESPRÄCH MIT {npc[ATTR_NAME].upper()} ---")
            
            DialogueHandler._print_dialogue(game, npc, reaction_entry)
            
            # FIX: Multi-Effekte und neue Effekte
            DialogueHandler.process_effects(game, reaction_entry, npc)
        else:
            DialogueHandler.talk(game, [npc[ATTR_NAME]])

    @staticmethod
    def open(game, args):
        clean_args = Resolver.clean_args(args)
        target = Resolver.resolve_target(game, clean_args, location_filter=FILTER_RECURSIVE, verb='open')
        
        if not target: 
            return game.log('error', "Das sehe ich hier nicht.")
        
        if target.get('type') == TYPE_SURFACE: return game.log('info', "Das ist offen sichtbar.")
        if target.get('type') != TYPE_CONTAINER: return game.log('error', "Das lässt sich nicht öffnen.")
        
        if target.get('is_locked'):
            key_id = target.get('key_id')
            if key_id:
                has_key = any(o[ATTR_ID] == key_id and o['location'] == LOC_INVENTORY for o in game.objects.values())
                if has_key:
                    key_obj = game.objects[key_id]; game.log('info', f"(Ich schließe mit {key_obj[ATTR_NAME]} auf...)"); target['is_locked'] = False
                else: return game.log('error', "Verschlossen. Du brauchst einen Schlüssel.")
            else: return game.log('error', "Verschlossen.")
        
        if target.get('is_open'):
            return game.log('info', "Ist schon offen.")

        target['is_open'] = True
        game.log('success', f"{target[ATTR_NAME]} geöffnet.")
        InteractionHandler.look(game, clean_args)

    @staticmethod
    def put(game, args):
        if not args: return game.log('error', "Was wohin legen?")
        separators = ["in", "auf", "on", "into", "an"]
        sep_indices = [i for i, w in enumerate(args) if w.lower() in separators]
        item_words = args[:sep_indices[0]] if sep_indices else args[:-1]
        container_words = args[sep_indices[0]+1:] if sep_indices else [args[-1]]
        item = Resolver.resolve_target(game, item_words, location_filter=FILTER_INVENTORY, verb='put_item')
        if not item: return game.log('error', "Das hast du nicht dabei (oder es ist flüssig).") 
        container = Resolver.resolve_target(game, container_words, location_filter=FILTER_RECURSIVE, verb='put_container')
        if not container: return game.log('error', "Diesen Behälter sehe ich hier nicht.")
        if container == item: return game.log('error', "Geht nicht.")
        if container.get('type') not in [TYPE_CONTAINER, TYPE_SURFACE]: return game.log('error', "Da kannst du nichts reinlegen.")
        if container.get('type') == TYPE_CONTAINER and not container.get('is_open'): return game.log('error', f"Der {container[ATTR_NAME]} ist geschlossen.")
        item['location'] = container[ATTR_ID]; prep = "auf" if container.get('type') == TYPE_SURFACE else "in"
        game.log('success', f"Du legst {item[ATTR_NAME]} {prep} {container[ATTR_NAME]}."); game.tick(2)

    @staticmethod
    def inventory(game, args):
        items = [o for o in game.objects.values() if o['location'] == LOC_INVENTORY]
        display_list = []
        for item in items:
            name = item[ATTR_NAME]
            if item.get('type') in [TYPE_CONTAINER, TYPE_SURFACE]:
                if item.get('type') == TYPE_SURFACE or item.get('is_open', True):
                    contents = [o[ATTR_NAME] for o in game.objects.values() if o['location'] == item[ATTR_ID]]
                    if contents: name += f" (enthält: {', '.join(contents)})"
                    else: name += " (leer)"
                else: name += " (geschlossen)"
            display_list.append(name)
        if not display_list: game.log('info', "Inventar: Leer")
        else: game.log('info', f"Inventar: {', '.join(display_list)}")

    @staticmethod
    def use(game, args):
        if not args: return game.log('error', "Was benutzen?")
        separator_indices = [i for i, word in enumerate(args) if word.lower() in ["mit", "with", "und", "an"]]
        item1_name = ""
        item2_name = ""
        if separator_indices:
            idx = separator_indices[0]
            item1_name = " ".join(args[:idx])
            item2_name = " ".join(args[idx+1:])
        elif len(args) >= 2:
            item1_name = args[0]
            item2_name = args[-1]
            if len(args) > 2: mid = len(args) // 2; item1_name = " ".join(args[:mid]); item2_name = " ".join(args[mid:])
        else:
            game.log('info', f"Womit möchtest du {' '.join(args)} benutzen?")
            game.pending_interaction = {'verb': 'use', 'args': args}
            return

        result_msg = game.perform_combine(item1_name, item2_name)
        if "Fehler" in result_msg or "nicht" in result_msg.lower(): game.log('error', result_msg)
        else: game.log('success', result_msg); game.tick(2)

    @staticmethod
    def break_(game, args): 
        clean_args = Resolver.clean_args(args)
        target = Resolver.resolve_target(game, clean_args, location_filter=FILTER_RECURSIVE, verb='break')
        if not target: return game.log('error', "Was aufbrechen?")
        if not target.get('type') == TYPE_CONTAINER or not target.get('is_locked'): return game.log('error', "Nicht nötig.")
        key_id = target.get('key_id'); key_obj = game.objects.get(key_id) if key_id else None
        if key_obj and key_obj['location'] == LOC_INVENTORY:
             game.log('success', f"Du brichst das Schloss mit dem {key_obj[ATTR_NAME]} auf."); target['is_locked'] = False; target['is_open'] = True; game.tick(5); InteractionHandler.look(game, clean_args)
        else: game.log('error', "Du brauchst Werkzeug.")

    @staticmethod
    def fix(game, args):
        clean_args = Resolver.clean_args(args)
        target = Resolver.resolve_target(game, clean_args, location_filter=FILTER_RECURSIVE, verb='fix')
        if not target: return game.log('error', "Was reparieren?")
        if target.get('state') in [STATE_SABOTAGED, STATE_BROKEN]: target['state'] = STATE_NORMAL; game.log('success', f"Repariert."); game.tick(15)
        else: game.log('info', "Scheint intakt zu sein.")
    
    @staticmethod
    def drop_item(game, args):
        clean_args = Resolver.clean_args(args)
        target = Resolver.resolve_target(game, clean_args, location_filter=FILTER_INVENTORY, verb='drop')
        if target: target['location'] = game.location; game.log('success', f"{target[ATTR_NAME]} fallen gelassen."); game.tick(1)
        
    @staticmethod
    def wait(game, args):
        game.log('info', "Du wartest eine Weile..."); game.tick(10)