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
        'help': SystemHandler.help,
        'journal': SystemHandler.journal, 'logbuch': SystemHandler.journal, 'aufgaben': SystemHandler.journal # NEU
    }

    @staticmethod
    def dispatch(game, verb, args):
        # 1. Check auf ausstehende Interaktionen
        if game.pending_interaction:
            ActionDispatcher._handle_pending(game, verb, args)
            return

        # 2. Check auf Disambiguierung
        if game.disambiguation:
            ActionDispatcher._handle_disambiguation(game, verb, args)
            return

        # 3. Normales Dispatching
        handler_func = ActionDispatcher.COMMAND_MAP.get(verb)
        if handler_func:
            handler_func(game, args)
            return

        # 4. Fallback: Richtung?
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
        
        # WICHTIG: Wenn der Aufruf direkt vom GUI kommt (via "disambiguate" dummy verb),
        # steht der gesamte Input im ersten Argument von args.
        # Wenn er vom Parser kommt, ist 'verb' das erkannte Wort und 'args' leer.
        
        filter_text = ""
        if verb == "disambiguate":
            filter_text = args[0].strip().lower()
        else:
            # Fallback falls über Parser (sollte eigentlich durch GUI umgangen werden)
            filter_text = f"{verb} {' '.join(args)}".strip().lower()
        
        if filter_text in ["stop", "abbrechen", "nein", "cancel", "zurück"]:
            game.log('info', "Abgebrochen.")
            game.disambiguation = None
            return

        # Filtern der Kandidaten basierend auf User-Input
        matches = []
        for cand in candidates:
            # Wir suchen ob der filter_text im Namen oder Alias vorkommt
            # Bessere Logik: Prüfen ob filter_text "ähnlich" ist oder substring
            c_name = cand['name'].lower()
            if filter_text in c_name or any(filter_text in a.lower() for a in cand.get('aliases', [])):
                matches.append(cand)
        
        if len(matches) == 1:
            target = matches[0]
            game.disambiguation = None 
            game.log('user', f"(Ausgewählt: {target['name']})")
            
            # Wir müssen den ursprünglichen Befehl mit dem EINDEUTIGEN Zielnamen neu starten.
            # Dazu holen wir die originalen Argumente aus dem State.
            # Das ist tricky, da der Original-Befehl z.B. "benutze tool mit sicherung" war.
            # Wir wissen nicht, WELCHES Argument mehrdeutig war (tool oder sicherung).
            # Workaround: Wir rufen dispatch auf und hoffen, dass der Name jetzt eindeutig ist.
            # Aber wir ersetzen NICHTS im Original-String, da das Parsen schwer ist.
            
            # Bessere Strategie: Wir führen den Handler direkt aus, wenn möglich, 
            # oder wir starten den Resolver neu mit dem präzisen Namen.
            
            # Da 'ActionDispatcher' stateless ist, ist Restart schwer.
            # Einfachste Lösung: Wir loggen nur und der User muss den Befehl erneut eingeben? Nein, frustrierend.
            
            # Wir versuchen den Resolver zu 'primen' oder den Befehl neu zu bauen.
            # Wenn original_args da sind:
            # "benutze [tool] mit sicherung". Wir wissen nicht wo [tool] stand.
            
            # Pragmatisch: Wir rufen den Handler auf und übergeben den KLARTEXT Namen des gewählten Objekts
            # zusammen mit dem Rest. Aber woher wissen wir den Rest?
            # Im State 'original_args' steht z.B. ["tool", "mit", "sicherung"]
            
            # Da wir nicht wissen, welches Wort ersetzt werden muss, ist das hier eine Sackgasse der aktuellen Architektur.
            # ABER: Die meisten Disambiguierungen passieren bei einfachen Befehlen wie "nimm tool".
            # Bei "benutze X mit Y" ist es komplexer.
            
            # Lösung: Wir geben dem User Feedback und er muss es (leider) präziser eingeben,
            # ODER wir hacken es: Wir bauen einen neuen String, in dem der 'filter_text' (der den Match ausgelöst hat)
            # durch den vollen Namen ersetzt wird? Nein, der filter_text war ja die User-Eingabe JETZT.
            
            # Wir brechen hier ab und bitten den User, den Befehl mit dem eindeutigen Namen zu wiederholen.
            # game.log('info', f"Okay, ich nehme an du meinst {target['name']}. Bitte wiederhole den Befehl damit.")
            
            # ALTERNATIVE: Wir führen den Befehl aus und übergeben target['name'] als Argument.
            # Das klappt nur, wenn der Handler nur 1 Argument erwartet.
            # Bei 'use' (2 Args) schwierig.
            
            # Wir versuchen es einfach mit dem Namen des Targets als einziges Argument.
            # Das funktioniert für 'look', 'take', 'drop'. Für 'use' scheitert es ggf.
            ActionDispatcher.dispatch(game, original_verb, [target['name']])

        elif len(matches) > 1:
            names = [m['name'] for m in matches]
            game.log('info', f"Das grenzt es nicht genug ein. Meinst du: {', '.join(names)}?")
        else:
            game.log('info', "Das war keiner der Vorschläge. (Tippe 'stop' zum Abbrechen)")