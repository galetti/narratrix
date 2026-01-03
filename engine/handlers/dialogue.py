from engine.resolver import Resolver
from engine.llm_bridge import LLMBridge
from engine.constants import *
# Import von InventoryHandler entfernt, um Zirkelschluss zu vermeiden

class DialogueHandler:
    @staticmethod
    def talk(game, args_words):
        clean_args = [w for w in args_words if w.lower() not in ["mit", "zu", "an"]]
        target_npc = Resolver.find_mentioned_npc(game, clean_args)
        
        if not target_npc:
            local = [n for n in game.npcs if n['location'] == game.location]
            if len(local) == 1: 
                target_npc = local[0]
            else: 
                return game.log('error', "Mit wem willst du sprechen?")

        game.dialogue_active = True
        game.dialogue_partner = target_npc
        
        # Begrüßung ausgeben
        current_state = target_npc.get('state', 'default')
        
        # Datenzugriff (Kompatibilität mit neuer State-Struktur und alter Struktur)
        dialogue_db = {}
        if 'states' in target_npc:
            state_data = target_npc['states'].get(current_state, {})
            dialogue_db = state_data.get('dialogue', {})
        else:
            # Fallback alte Struktur
            dialogue_db = target_npc.get('dialogue', {}).get(current_state, {})

        greeting = dialogue_db.get('greeting', "...")
        
        game.log('event', f"--- GESPRÄCH MIT {target_npc[ATTR_NAME].upper()} ---")
        DialogueHandler._print_dialogue(game, target_npc, greeting)
        
        # Themen-Liste anzeigen
        DialogueHandler._show_topics(game, target_npc, dialogue_db)

    @staticmethod
    def step(game, user_input):
        text = user_input.strip().lower()
        npc = game.dialogue_partner
        
        if not npc: 
            game.dialogue_active = False
            return

        exit_words = ["bye", "ende", "tschüss", "weg", "stop", "exit", "leave", "q"]
        if any(w == text for w in exit_words):
            game.log('event', "--- GESPRÄCH BEENDET ---")
            game.dialogue_active = False
            game.dialogue_partner = None
            return

        # Check auf 'give' Befehle im Dialog
        args = text.split()
        if args and args[0] in ["gib", "give", "geb", "geben", "reich"]:
            # LOCAL IMPORT FIX: Import hier, um Zirkelschluss mit inventory.py zu verhindern
            from engine.handlers.inventory import InventoryHandler
            
            if "an" not in args and "to" not in args:
                new_args = args[1:] + ["an", npc[ATTR_NAME]]
                InventoryHandler.give(game, new_args)
            else:
                InventoryHandler.give(game, args[1:])
                
            # Nach dem Geben Themen neu anzeigen (falls State sich änderte)
            current_state = npc.get('state', 'default')
            dialogue_db = DialogueHandler._get_dialogue_db(npc, current_state)
            DialogueHandler._show_topics(game, npc, dialogue_db)
            return

        # --- LOGIK: ZAHL ODER TEXT? ---
        current_state = npc.get('state', 'default')
        dialogue_db = DialogueHandler._get_dialogue_db(npc, current_state)
        
        visible_topics = DialogueHandler._get_visible_topics(game, dialogue_db)
        
        chosen_entry = None
        chosen_topic_key = None

        # Fall A: Zahleneingabe
        if text.isdigit():
            idx = int(text) - 1
            if 0 <= idx < len(visible_topics):
                chosen_topic_key, chosen_entry = visible_topics[idx]
        
        # Fall B: Texteingabe (Keyword Search)
        else:
            for topic, entry in dialogue_db.items():
                if topic in ['greeting', 'default']: continue
                
                if not DialogueHandler._check_condition_wrapper(game, entry):
                    continue

                if topic in text:
                    chosen_entry = entry
                    chosen_topic_key = topic
                    break

        # Verarbeitung
        if chosen_entry:
            if text.isdigit():
                label = chosen_topic_key
                if isinstance(chosen_entry, dict) and 'label' in chosen_entry:
                    label = chosen_entry['label']
                game.log('user', f"> {label}")

            DialogueHandler._print_dialogue(game, npc, chosen_entry)
            DialogueHandler.process_effects(game, chosen_entry, npc)
            
            new_state = npc.get('state', 'default')
            new_db = DialogueHandler._get_dialogue_db(npc, new_state)
            DialogueHandler._show_topics(game, npc, new_db)
            
        else:
            # Fallback / LLM
            use_llm = game.config.get('use_llm_dialogue', False)
            if use_llm: 
                DialogueHandler._print_dialogue(game, npc, "LLM_AUTO_REPLY", prompt_context=text)
            else: 
                default_reply = dialogue_db.get('default')
                if default_reply:
                    DialogueHandler._print_dialogue(game, npc, default_reply)
                else:
                    game.log('character', f"{npc[ATTR_NAME]} schaut dich fragend an.")
            
            DialogueHandler._show_topics(game, npc, dialogue_db)

    # --- HELPER ---

    @staticmethod
    def _get_dialogue_db(npc, state):
        if 'states' in npc:
            return npc['states'].get(state, {}).get('dialogue', {})
        return npc.get('dialogue', {}).get(state, {})

    @staticmethod
    def _get_visible_topics(game, dialogue_db):
        visible = []
        for topic, entry in dialogue_db.items():
            if topic in ['greeting', 'default']: continue
            
            if not DialogueHandler._check_condition_wrapper(game, entry):
                continue
            
            is_hidden = False
            if isinstance(entry, dict) and entry.get('hidden', False):
                is_hidden = True
            
            if not is_hidden:
                visible.append((topic, entry))
        return visible

    @staticmethod
    def _show_topics(game, npc, dialogue_db):
        visible = DialogueHandler._get_visible_topics(game, dialogue_db)
        
        if not visible:
            game.log('info', "(Keine offensichtlichen Gesprächsthemen)")
            return

        options = []
        for i, (topic, entry) in enumerate(visible):
            label = topic.capitalize()
            if isinstance(entry, dict) and 'label' in entry:
                label = entry['label']
            options.append(f"[{i+1}] {label}")
        
        game.log('info', "Optionen: " + ", ".join(options))

    @staticmethod
    def _check_condition_wrapper(game, entry):
        if isinstance(entry, dict) and 'condition' in entry: return DialogueHandler._check_condition(game, entry['condition'])
        return True

    @staticmethod
    def _check_condition(game, condition):
        if not condition: return True
        if isinstance(condition, str): return condition in game.knowledge
        if isinstance(condition, dict):
            c_type = condition.get('type')
            if c_type == 'knowledge': return condition.get('value') in game.knowledge
            elif c_type == 'location': return game.location == condition.get('value')
            elif c_type == 'item_location':
                item_id = condition.get('item')
                loc = condition.get('location')
                obj = game.objects.get(item_id)
                return obj and obj['location'] == loc
            elif c_type == 'npc_state':
                target_name = condition.get('npc')
                required_state = condition.get('state')
                target = next((n for n in game.npcs if n[ATTR_NAME] == target_name or target_name in n.get(ATTR_ALIASES, [])), None)
                if target: return target.get('state', 'default') == required_state
                return False
        return True

    @staticmethod
    def process_effects(game, entry, npc):
        if 'effect' not in entry: return
        effects_data = entry['effect']
        effect_list = effects_data if isinstance(effects_data, list) else [effects_data]
            
        for eff in effect_list:
            DialogueHandler._execute_effect(game, eff, npc)

    @staticmethod
    def _execute_effect(game, effect, npc):
        e_type = effect.get('type')
        
        if e_type == 'move_npc':
            target_room = effect.get('target')
            if target_room in game.rooms:
                game.log('event', f"[{npc[ATTR_NAME]} macht sich auf den Weg.]")
                npc[ATTR_AFFINITY] = [target_room]
                npc['location'] = target_room
                npc['destination'] = target_room
                if target_room != game.location:
                    game.dialogue_active = False; game.dialogue_partner = None
                    game.log('event', "--- GESPRÄCH BEENDET (Partner gegangen) ---")
            else: game.log('error', f"Effect Error: Room {target_room} not found.")
            
        elif e_type == 'learn':
            fact = effect.get('fact'); game.add_knowledge(fact); game.log('success', f"(Wissen erhalten: {fact})")
            
        elif e_type == 'game_over':
            reason = effect.get('reason', "Game Over"); game.log('alarm', reason); game.game_over = True
            
        elif e_type == 'set_state':
            new_state = effect.get('value')
            npc['state'] = new_state
            game.log('info', f"({npc[ATTR_NAME]} wirkt verändert.)")

        elif e_type == 'receive_item':
            item_id = effect.get('item_id')
            if item_id in game.objects:
                item = game.objects[item_id]
                item['location'] = LOC_INVENTORY
                game.log('success', f"Erhalten: {item[ATTR_NAME]}")
            else:
                game.log('error', f"Effect Error: Item {item_id} existiert nicht.")

        elif e_type == 'set_npc_state':
            target_name = effect.get('npc')
            new_state = effect.get('value')
            target = next((n for n in game.npcs if n[ATTR_NAME] == target_name or target_name in n.get(ATTR_ALIASES, [])), None)
            if target:
                target['state'] = new_state
                game.log('success', f"(Status von {target[ATTR_NAME]} aktualisiert)")

    @staticmethod
    def _print_dialogue(game, npc, response_entry, prompt_context=None):
        core_text = response_entry
        if isinstance(response_entry, dict): core_text = response_entry.get('text', "")
        
        final_text = core_text
        use_llm = game.config.get('use_llm_dialogue', False)
        if use_llm:
            personality = npc.get('personality', 'Neutral'); state = npc.get('state', 'default'); stress = "HOCH" if game.stability < 50 else "NIEDRIG"
            if response_entry == "LLM_AUTO_REPLY":
                sys_prompt = f"Du bist {npc[ATTR_NAME]} ({personality}). Stimmung: {state}. Stress: {stress}. Antworte auf: '{prompt_context}'."
                user_msg = "Antworte kurz und passend zur Rolle."
            else:
                sys_prompt = f"Du bist {npc[ATTR_NAME]} ({personality}). Stimmung: {state}. Stress: {stress}. Formuliere um:"
                user_msg = f"Kern-Aussage: {core_text}"
            game.log('info', f"({npc[ATTR_NAME]} denkt nach...)"); enhanced = LLMBridge.call(sys_prompt, user_msg)
            if enhanced: final_text = enhanced
            
        game.log('character', f"{npc[ATTR_NAME]}: \"{final_text}\"")