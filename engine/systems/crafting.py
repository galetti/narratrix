from engine.constants import *
from engine.resolver import Resolver

class CraftingSystem:
    """
    Verwaltet das Kombinieren von Gegenständen mit erweiterten Bedingungen
    wie Werkzeugen, Arbeitsstationen und Bauplänen.
    """
    def __init__(self, game):
        self.game = game
        # Rezepte werden aus der Config geladen (game.combinations)
        # Struktur eines Rezepts in der Config:
        # {
        #   "ingredients": ["item_a", "item_b"],
        #   "result": "item_c",
        #   "tools": ["tool_screwdriver"],       # Optional: Werkzeug im Inventar nötig (bleibt erhalten)
        #   "station": "obj_workbench",          # Optional: Muss im Raum oder Inventar sein
        #   "blueprint": "knows_circuitry",      # Optional: Knowledge-ID nötig
        #   "message": "Du lötest den Chip..."   # Optional: Custom Success Message
        # }

    def perform_combine(self, item1_name, item2_name):
        """
        Hauptmethode, die vom ActionDispatcher aufgerufen wird.
        Versucht, zwei Objekte anhand ihrer Namen zu kombinieren.
        """
        # 1. Objekte auflösen
        obj1 = self._resolve_crafting_item(item1_name)
        obj2 = self._resolve_crafting_item(item2_name)

        if not obj1 or not obj2:
            return "Ich konnte eines der Objekte nicht finden (muss im Inventar oder greifbar sein)."

        # 2. Rezept finden
        recipe = self._find_recipe(obj1['id'], obj2['id'])
        if not recipe:
            return "Das lässt sich nicht sinnvoll kombinieren."

        # 3. Bedingungen prüfen
        
        # A. Bauplan / Wissen
        if 'blueprint' in recipe:
            knowledge_id = recipe['blueprint']
            if knowledge_id not in self.game.knowledge:
                return "Du hast keine Ahnung, wie man diese Teile verbindet. Dir fehlt ein Bauplan oder Wissen."

        # B. Station (Werkbank, Herd, etc.)
        if 'station' in recipe:
            station_id = recipe['station']
            if not self._is_station_available(station_id):
                station_name = self._get_obj_name(station_id)
                return f"Dafür brauchst du eine Arbeitsfläche: {station_name}."

        # C. Werkzeuge
        if 'tools' in recipe:
            missing_tools = []
            for tool_id in recipe['tools']:
                if not self._has_item_in_inventory(tool_id):
                    tool_name = self._get_obj_name(tool_id)
                    missing_tools.append(tool_name)
            
            if missing_tools:
                return f"Dir fehlt das nötige Werkzeug: {', '.join(missing_tools)}."

        # 4. Crafting durchführen
        return self._execute_crafting(obj1, obj2, recipe)

    def _resolve_crafting_item(self, name):
        """Sucht das Item im Inventar oder im Raum (für Stationen/große Objekte)."""
        # Wir nutzen den Resolver, aber schränken die Suche ein, damit man nicht mit Dingen im anderen Raum craftet
        try:
            # Prio 1: Inventar
            return Resolver.resolve_target(self.game, name.split(), location_filter=FILTER_INVENTORY)
        except:
            pass
        
        try:
            # Prio 2: Raum (z.B. wenn man etwas auf einen stationären Amboss legt)
            return Resolver.resolve_target(self.game, name.split(), location_filter=FILTER_ROOM)
        except:
            return None

    def _find_recipe(self, id1, id2):
        """Sucht ein passendes Rezept für die beiden IDs (Reihenfolge egal)."""
        for recipe in self.game.combinations:
            ing = recipe.get('ingredients', [])
            if len(ing) == 2:
                if (ing[0] == id1 and ing[1] == id2) or (ing[0] == id2 and ing[1] == id1):
                    return recipe
        return None

    def _is_station_available(self, station_id):
        """Prüft, ob die Station im Raum oder (selten) im Inventar ist."""
        # Ist es der Raum selbst? (z.B. "room_lab")
        if self.game.location == station_id:
            return True
            
        # Ist es ein Objekt im Raum?
        for obj in self.game.objects.values():
            if obj['id'] == station_id:
                if obj['location'] == self.game.location or obj['location'] == LOC_INVENTORY:
                    return True
        return False

    def _has_item_in_inventory(self, item_id):
        """Prüft auf Besitz eines Items (für Werkzeuge)."""
        for obj in self.game.objects.values():
            if obj['id'] == item_id and obj['location'] == LOC_INVENTORY:
                return True
        return False

    def _get_obj_name(self, obj_id):
        """Hilfsfunktion für Fehlernachrichten."""
        obj = self.game.objects.get(obj_id)
        if obj: return obj[ATTR_NAME]
        # Fallback: Suche in Räumen
        room = self.game.rooms.get(obj_id)
        if room: return room[ATTR_NAME]
        return "Unbekanntes Objekt"

    def _execute_crafting(self, obj1, obj2, recipe):
        """Führt den Crafting-Prozess aus (Verbrauchen, Erzeugen)."""
        
        # 1. Zutaten verbrauchen (außer das Rezept sagt 'preserve': ['id'])
        preserved = recipe.get('preserve', [])
        
        if obj1['id'] not in preserved:
            obj1['location'] = LOC_VOID
        
        if obj2['id'] not in preserved:
            obj2['location'] = LOC_VOID

        # 2. Ergebnis erzeugen
        result_id = recipe.get('result')
        if result_id:
            # Wir holen das Template-Objekt
            result_obj = self.game.objects.get(result_id)
            if result_obj:
                result_obj['location'] = LOC_INVENTORY
                
                # Optional: Müll erzeugen (Nebenprodukte)
                byproducts = recipe.get('byproducts', [])
                for bid in byproducts:
                    bp = self.game.objects.get(bid)
                    if bp: bp['location'] = LOC_INVENTORY

                success_msg = recipe.get('message', f"Du kombinierst {obj1[ATTR_NAME]} und {obj2[ATTR_NAME]} zu: {result_obj[ATTR_NAME]}.")
                return success_msg
            else:
                return f"[ERROR] Ergebnis-Item '{result_id}' nicht in der Datenbank gefunden."
        
        return "Es ist etwas passiert, aber kein Ergebnis definiert."