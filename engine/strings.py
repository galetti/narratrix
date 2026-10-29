# engine/strings.py
from __future__ import annotations

class Texts:
    # --- Exploration ---
    LOOK_DEFAULT: str = "Nichts Besonderes."
    LOOK_EMPTY: str = "Der Raum scheint leer zu sein."
    LOOK_EXITS: str = "Ausgänge: {}"
    LOOK_NO_EXITS: str = "Es gibt keinen sichtbaren Ausweg."
    LOOK_GROUND: str = "Am Boden: {}"
    LOOK_PERSONS: str = "Personen: {}"
    LOOK_CONTENT: str = "Inhalt: {}"
    LOOK_EMPTY_CONTAINER: str = "Leer."
    LOOK_LOCKED: str = "Verschlossen."
    LOOK_CLOSED: str = "Geschlossen."
    LOOK_OPEN: str = "Offen."
    LOOK_HOT: str = "Es ist HEISS."
    LOOK_WARM: str = "Es ist warm."
    LOOK_COLD: str = "Es ist eiskalt."
    LOOK_LIQUID: str = "Es ist flüssig."
    LOOK_SABOTAGED: str = "[WARNUNG: SABOTIERT]"
    LOOK_BROKEN: str = "[DEFEKT]"
    
    # --- Movement / Hiding ---
    HIDE_ALREADY: str = "Du bist bereits versteckt. Benutze 'raus' (oder 'gehe raus') um das Versteck zu verlassen."
    HIDE_ERROR_TYPE: str = "Darin kannst du dich nicht verstecken."
    HIDE_ERROR_SIZE: str = "Das ist zu klein für dich."
    HIDE_ERROR_CLOSED: str = "Es ist geschlossen."
    HIDE_SUCCESS: str = "Du kriechst in {target} und ziehst die Tür leise zu."
    HIDE_SEE_NPCS: str = "Durch den Spalt siehst du Personen: {}"
    
    # --- Inventory ---
    INV_EMPTY: str = "Inventar: Leer"
    INV_LIST: str = "Inventar: {}"
    TAKE_ALREADY: str = "Hast du schon."
    TAKE_TOO_HEAVY: str = "Das ist viel zu schwer oder fest verankert."
    TAKE_LIQUID_ERROR: str = "Das kannst du nicht mit den bloßen Händen nehmen. Du brauchst einen Behälter."
    TAKE_SUCCESS: str = "{item} genommen."
    DROP_SUCCESS: str = "{item} fallen gelassen."
    GIVE_MISSING_ARGS: str = "Was an wen?"
    GIVE_NPC_NOT_HERE: str = "Diese Person ist nicht hier."
    GIVE_SUCCESS: str = "Du gibst {item} an {npc}."
    GIVE_REFUSED: str = "{npc} lehnt ab: \"Das brauche ich gerade nicht.\""
    
    # --- General Errors ---
    ERR_HIDDEN: str = "Nicht während du versteckt bist."
