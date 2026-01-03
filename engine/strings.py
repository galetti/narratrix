# engine/strings.py

class Texts:
    # --- Exploration ---
    LOOK_DEFAULT = "Nichts Besonderes."
    LOOK_EMPTY = "Der Raum scheint leer zu sein."
    LOOK_EXITS = "Ausgänge: {}"
    LOOK_NO_EXITS = "Es gibt keinen sichtbaren Ausweg."
    LOOK_GROUND = "Am Boden: {}"
    LOOK_PERSONS = "Personen: {}"
    LOOK_CONTENT = "Inhalt: {}"
    LOOK_EMPTY_CONTAINER = "Leer."
    LOOK_LOCKED = "Verschlossen."
    LOOK_CLOSED = "Geschlossen."
    LOOK_OPEN = "Offen."
    LOOK_HOT = "Es ist HEISS."
    LOOK_WARM = "Es ist warm."
    LOOK_COLD = "Es ist eiskalt."
    LOOK_LIQUID = "Es ist flüssig."
    LOOK_SABOTAGED = "[WARNUNG: SABOTIERT]"
    LOOK_BROKEN = "[DEFEKT]"
    
    # --- Movement / Hiding ---
    HIDE_ALREADY = "Du bist bereits versteckt. Benutze 'raus' (oder 'gehe raus') um das Versteck zu verlassen."
    HIDE_ERROR_TYPE = "Darin kannst du dich nicht verstecken."
    HIDE_ERROR_SIZE = "Das ist zu klein für dich."
    HIDE_ERROR_CLOSED = "Es ist geschlossen."
    HIDE_SUCCESS = "Du kriechst in {target} und ziehst die Tür leise zu."
    HIDE_SEE_NPCS = "Durch den Spalt siehst du Personen: {}"
    
    # --- Inventory ---
    INV_EMPTY = "Inventar: Leer"
    INV_LIST = "Inventar: {}"
    TAKE_ALREADY = "Hast du schon."
    TAKE_TOO_HEAVY = "Das ist viel zu schwer oder fest verankert."
    TAKE_LIQUID_ERROR = "Das kannst du nicht mit den bloßen Händen nehmen. Du brauchst einen Behälter."
    TAKE_SUCCESS = "{item} genommen."
    TAKE_NOTHING = "Hier gibt es nichts zum Mitnehmen."
    DROP_SUCCESS = "{item} fallen gelassen."
    GIVE_MISSING_ARGS = "Was an wen?"
    GIVE_NPC_NOT_HERE = "Diese Person ist nicht hier."
    GIVE_SUCCESS = "Du gibst {item} an {npc}."
    GIVE_REFUSED = "{npc} lehnt ab: \"Das brauche ich gerade nicht.\""
    
    # --- Mechanics ---
    USE_MISSING_ARGS = "Womit möchtest du {} benutzen?"
    USE_SUCCESS = "{}" # Platzhalter für individuelle Crafting-Nachricht
    OPEN_SURFACE_ERROR = "Das ist offen sichtbar."
    OPEN_ERROR = "Das lässt sich nicht öffnen."
    OPEN_ALREADY = "Ist schon offen."
    OPEN_SUCCESS = "{target} geöffnet."
    OPEN_LOCKED = "Verschlossen."
    OPEN_LOCKED_KEY = "Verschlossen. Du brauchst einen Schlüssel."
    OPEN_KEY_USED = "(Ich schließe mit {key} auf...)"
    OPEN_RUSTY = "Es klemmt."
    OPEN_NO_POWER = "Kein Strom."
    OPEN_DENIED = "Zugriff verweigert."
    
    PUT_MISSING_ARGS = "Was wohin legen?"
    PUT_SAME_ITEM = "Geht nicht."
    PUT_ERROR_TYPE = "Da kannst du nichts reinlegen."
    PUT_ERROR_CLOSED = "Der {container} ist geschlossen."
    PUT_SCALE_ERROR = "Die Waage muss auf einem stabilen Untergrund stehen."
    PUT_SUCCESS = "Du legst {item} {prep} {container}."
    
    FIX_SUCCESS = "Repariert."
    FIX_NOT_BROKEN = "Scheint intakt zu sein."
    
    BREAK_SUCCESS = "Du brichst das Schloss mit dem {tool} auf."
    BREAK_NEED_TOOL = "Du brauchst ein passendes Werkzeug (z.B. Brecheisen) oder den Schlüssel."
    BREAK_NOT_NEEDED = "Nicht nötig."
    
    WAIT_MSG = "Du wartest eine Weile..."
    
    # --- General Errors ---
    ERR_HIDDEN = "Nicht während du versteckt bist."