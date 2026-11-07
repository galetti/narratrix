# engine/strings.py
from __future__ import annotations

from typing import Any


class Texts:
    # --- Directions & Orientations ---
    DIRECTIONS: dict[str, str] = {
        "north": "Norden",
        "south": "Süden",
        "east": "Osten",
        "west": "Westen",
        "up": "Oben",
        "down": "Unten",
        "out": "Ausgang",
        "northeast": "Nordost",
        "northwest": "Nordwest",
        "southeast": "Südost",
        "southwest": "Südwest",
    }

    DIRECTIONS_LONG: dict[str, str] = {
        "north": "Norden",
        "south": "Süden",
        "east": "Osten",
        "west": "Westen",
        "up": "Oben",
        "down": "Unten",
        "out": "Ausgang",
        "northeast": "Nordosten",
        "northwest": "Nordwesten",
        "southeast": "Südosten",
        "southwest": "Südwesten",
    }

    DIRECTIONS_FROM: dict[str, str] = {
        "north": "aus Norden",
        "south": "aus Süden",
        "east": "aus Osten",
        "west": "aus Westen",
        "up": "von Oben",
        "down": "von Unten",
        "out": "von Draußen",
        "northeast": "aus Nordosten",
        "northwest": "aus Nordwesten",
        "southeast": "aus Südosten",
        "southwest": "aus Südwesten",
    }

    HERE: str = "hier"

    @classmethod
    def direction_name(
        cls, direction: str, default: str | None = None, long_form: bool = False
    ) -> str:
        mapping = cls.DIRECTIONS_LONG if long_form else cls.DIRECTIONS
        return mapping.get(direction, default if default is not None else direction.capitalize())

    @classmethod
    def direction_from(cls, direction: str, default: str | None = None) -> str:
        return cls.DIRECTIONS_FROM.get(
            direction, default if default is not None else direction
        )

    # --- Exploration & Look ---
    LOOK_DEFAULT: str = "Nichts Besonderes."
    LOOK_EMPTY: str = "Der Raum scheint leer zu sein."
    LOOK_HIDDEN_IN: str = "Du versteckst dich in {}."
    LOOK_DOOR_STATUS: str = "{name} ({state})"
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
    LOOK_ROOM_NOT_FOUND: str = "Fehler: Aktueller Raum nicht gefunden."
    LOOK_ON_SURFACE: str = "Auf dem {name}: {content}"
    LOOK_IN_OPEN: str = "Im offenen {name}: {content}"
    LOOK_NOTHING_ON: str = "Auf dem {name} ist nichts."
    LOOK_NOTHING_IN: str = "Im offenen {name} ist nichts."
    LOOK_SCALE_DISPLAY: str = "Display: {:.2f} kg"

    # --- Acoustics & Listening ---
    LISTEN_FROM_HIDE: str = "Du lauschst aus deinem Versteck in {container} heraus..."
    LISTEN_TOOL_NO_BOOST: str = "Du hältst {tool} an {target}, aber es verstärkt den Schall nicht."
    LISTEN_CLEAR_VOICES: str = (
        "Du drückst {tool} fest gegen {target} und lauschst am Boden des Glases. "
        "Die Schwingungen der Tür übertragen sich klar auf das Glas! Du hörst zwei Stimmen glasklar:\n"
        "'{message}'"
    )
    LISTEN_MUFFLED: str = (
        "Du drückst {tool} gegen {target}. "
        "Du hörst gedämpfte Stimmen, aber der Schall wird noch zu stark geschluckt."
    )
    LISTEN_ABSOLUTE_SILENCE: str = (
        "Du drückst {tool} gegen {target} und lauschst angestrengt. "
        "Doch dahinter herrscht absolute Stille – der Raum scheint schallundurchdringlich isoliert zu sein."
    )
    LISTEN_DOOR_MUFFLED_NO_TOOL: str = (
        " Wenn du ein akustisches Verstärkerglas hättest, könntest du es verstehen!"
    )
    LISTEN_DOOR_MUFFLED_WITH_TOOL: str = (
        " Drücke dein {tool} an die Tür ('lausche an tür mit glas'), um es zu verstehen!"
    )
    LISTEN_DOOR_MURMURS: str = (
        "Du lauschst an {target}. Du nimmst gedämpftes Gemurmel und Stimmen wahr, "
        "aber das Schott schluckt zu viel Schall.{hint}"
    )
    LISTEN_DOOR_SILENCE: str = "Du lauschst an {target}. Dahinter ist es vollkommen still."
    LISTEN_DOOR_NOTHING: str = (
        "Du lauschst an {target}, kannst aber keine auffälligen Geräusche ausmachen."
    )
    LISTEN_HEAR_SOUND: str = "{direction} hörst du: {prefix}{sound}"
    LISTEN_QUIET_STATION: str = (
        "Du lauschst angestrengt in die Stille. Abgesehen vom leisen Surren der "
        "Stationslüftung ist nichts zu hören."
    )
    LISTEN_PREFIX_QUIET: str = "(leise) "
    LISTEN_PREFIX_LOUD: str = "(LAUT) "
    LISTEN_SOMEWHERE: str = "Irgendwo"

    # --- Movement & Climbing & Hiding ---
    HIDE_ALREADY: str = "Du bist bereits versteckt. Benutze 'raus' (oder 'gehe raus') um das Versteck zu verlassen."
    HIDE_ERROR_TYPE: str = "Darin kannst du dich nicht verstecken."
    HIDE_ERROR_SIZE: str = "Das ist zu klein für dich."
    HIDE_ERROR_CLOSED: str = "Es ist geschlossen."
    HIDE_SUCCESS: str = "Du kriechst in {target} und ziehst die Tür leise zu."
    HIDE_SEE_NPCS: str = "Durch den Spalt siehst du Personen: {}"
    MOVE_SEE_ITEMS: str = "Hier siehst du: {}"
    MOVE_LEAVE_HIDE: str = "Du kommst aus deinem Versteck hervor."
    MOVE_STILL_HIDDEN: str = "Du bist versteckt. Komm erst raus (gehe raus)."
    MOVE_NO_DEST: str = "Wohin willst du gehen?"
    MOVE_BLOCKED: str = "Der Weg ist versperrt durch: {blocker}"
    MOVE_NO_WAY: str = "Nach '{target}' führt kein Weg."
    MOVE_CLIMB_DOWN: str = "Du kletterst zurück auf den Boden."
    MOVE_CLIMB_CANNOT_SIMPLE: str = "Du kannst hier nicht einfach hochklettern. Benutze ein Objekt."
    MOVE_CLIMB_ALREADY_UP: str = "Du bist schon oben."
    MOVE_CLIMB_WHAT: str = "Worauf willst du klettern?"
    MOVE_CLIMB_CANNOT: str = "Du kannst nicht auf {target} klettern."
    MOVE_CLIMB_ALREADY_THERE: str = "Du bist bereits oben bei {target} (Ebene {level})."
    MOVE_CLIMB_SUCCESS_LEVEL: str = "Du kletterst auf {target}. (Ebene {level})"
    MOVE_CLIMB_SUCCESS_DEST: str = "Du kletterst auf {target}..."
    MOVE_CLIMB_SUCCESS_PASSAGE: str = "Du kletterst auf {target} und erreichst den Durchgang..."
    MOVE_CLIMB_NO_HEIGHT: str = "Du kletterst auf {target}, aber es bringt dich nicht höher."
    LEVEL_INFO_UP: str = " (oben auf Ebene {level})"
    LEVEL_INFO_DOWN: str = " (unten auf Ebene {level})"
    CONTAINER_OPEN: str = " (offen)"
    CONTAINER_CLOSED: str = " (geschlossen)"

    # --- Inventory & Manipulation ---
    INV_EMPTY: str = "Inventar: Leer"
    INV_LIST: str = "Inventar: {}"
    INV_CONTAINS: str = " (enthält: {})"
    INV_EMPTY_CONTAINER_LABEL: str = " (leer)"
    INV_CLOSED_CONTAINER_LABEL: str = " (geschlossen)"
    TAKE_ALREADY: str = "Hast du schon."
    TAKE_TOO_HEAVY: str = "Das ist viel zu schwer oder fest verankert."
    TAKE_LIQUID_ERROR: str = "Das kannst du nicht mit den bloßen Händen nehmen. Du brauchst einen Behälter."
    TAKE_SUCCESS: str = "{item} genommen."
    TAKE_ALL_SUCCESS: str = "Genommen: {}"
    TAKE_ALL_NOTHING: str = "Nichts Greifbares hier."
    TAKE_CANNOT_PERSON: str = "Personen kannst du nicht ins Inventar stecken."
    TAKE_RESOURCE_SUCCESS: str = "Du nimmst {amount}x {item} (Total: {total})."
    TAKE_STORED_ALSO: str = "Du verstaust auch: {}."
    DROP_SUCCESS: str = "{item} fallen gelassen."
    GIVE_MISSING_ARGS: str = "Was an wen?"
    GIVE_NPC_NOT_HERE: str = "Diese Person ist nicht hier."
    GIVE_SUCCESS: str = "Du gibst {item} an {npc}."
    GIVE_REFUSED: str = "{npc} lehnt ab: \"Das brauche ich gerade nicht.\""
    TOOL_NOT_IN_INVENTORY: str = "Du hast dieses Werkzeug nicht."
    TOOL_USE_TO_REACH: str = "Du benutzt {tool}, um {target} zu erreichen."
    TOOL_NOT_LONG_ENOUGH: str = "{tool} ist nicht lang genug."
    TRY_TAKE_WITH_TOOL: str = "(Versuche, {target} mit {tool} zu nehmen...)"

    # --- Mechanics (Put, Use, Open, Close, Break, Fix, Wait) ---
    PUT_MISSING_PREP: str = "Wo willst du das hintun? (Benutze 'in' oder 'auf')"
    PUT_ONLY_OBJECTS: str = "Nur Gegenstände lassen sich ablegen."
    PUT_PHYSICALLY_IMPOSSIBLE: str = "Das geht physikalisch nicht."
    PUT_CANNOT_PLACE: str = "Auf/in {target} lässt sich nichts legen."
    PUT_CONTAINER_CLOSED: str = "{target} ist geschlossen."
    PUT_CYCLIC_CONTAINER: str = "Container können nicht zyklisch verschachtelt werden."
    PUT_TOO_HEAVY_FOR_CONTAINER: str = "{item} ist zu schwer oder zu groß für {target}."
    PUT_LIQUID_ON_SURFACE: str = "Flüssigkeiten lassen sich nicht auf {target} ablegen."
    PUT_SUCCESS: str = "Du legst {item} in/auf {target}."
    USE_STATE_TOGGLED: str = "Du benutzt {target}. (Zustand: {state})"
    USE_NOTHING_HAPPENS: str = "Du benutzt {target}, aber nichts passiert."
    USE_ASK_WHAT_WITH: str = "Was willst du mit {target} benutzen?"
    OPEN_NOT_CONTAINER: str = "Das kann man nicht öffnen."
    OPEN_ALREADY_OPEN: str = "{target} ist bereits offen."
    OPEN_LOCKED: str = "{target} ist verschlossen."
    OPEN_UNLOCK_WITH_KEY: str = "Du schließt {target} mit {key} auf."
    OPEN_SUCCESS: str = "Du öffnest {target}."
    OPEN_CONTAINS: str = "Darin befindet sich: {}"
    CLOSE_NOT_CONTAINER: str = "Das kann man nicht schließen."
    CLOSE_ALREADY_CLOSED: str = "{target} ist bereits geschlossen."
    CLOSE_JAMMED: str = "{target} ist verkeilt und lässt sich nicht schließen."
    CLOSE_SUCCESS: str = "Du schließt {target}."
    BREAK_ALREADY_BROKEN: str = "{target} ist bereits kaputt."
    BREAK_IN_CONTAINER_SUCCESS: str = "Du zerstörst {target} in {tool}."
    BREAK_WITH_TOOL_SUCCESS: str = "Mit {tool} zerstörst du {target}!"
    BREAK_TOOL_NOT_STRONG: str = "{tool} ist nicht stark genug für {target}."
    BREAK_BARE_HANDS_SUCCESS: str = "Du zerstörst {target} mit bloßen Händen."
    BREAK_NEED_TOOL: str = "Du brauchst dafür ein passendes Werkzeug."
    FIX_SABOTAGED_HINT: str = "Das sieht nach Sabotage aus. Dafür brauchst du einen Plan."
    FIX_NOT_BROKEN: str = "{target} scheint in Ordnung zu sein."
    FIX_NEED_TOOL: str = "Du hast kein geeignetes Werkzeug dabei."
    FIX_SUCCESS: str = "Du hast {target} repariert."
    WAIT_MINUTES: str = "Du wartest {minutes} Minuten..."
    BROKEN_PREFIX: str = "kaputte(s) "
    BROKEN_DESC: str = "Völlig zerstört."

    # --- Dialogue ---
    TALK_WHO: str = "Mit wem willst du sprechen?"
    DIALOGUE_HEADER: str = "--- GESPRÄCH MIT {npc} ---"
    DIALOGUE_ENDED: str = "--- GESPRÄCH BEENDET{suffix} ---"
    DIALOGUE_NO_TOPICS: str = "(Keine offensichtlichen Gesprächsthemen)"
    DIALOGUE_OPTIONS: str = "Optionen: {}"
    DIALOGUE_CONFUSED: str = "{npc} schaut dich fragend an."
    DIALOGUE_THINKING: str = "({npc} denkt nach...)"
    DIALOGUE_LINE: str = '{npc}: "{text}"'

    # --- Access / Reach Errors ---
    REACH_TOO_HIGH: str = "{target} ist zu weit oben (Ebene {level}). Du kommst nicht heran."
    REACH_TOO_LOW: str = "{target} liegt zu weit unten (Ebene {level}). Du musst runterklettern."
    REACH_TOO_HIGH_GENERIC: str = "{name} ist auf Ebene {level}. Du kommst von hier nicht heran."
    REACH_UNREACHABLE_GENERIC: str = "{name} ist von hier nicht erreichbar."

    # --- Action Dispatcher ---
    DISAMBIGUATION_PROMPT: str = "Meinst du: {}?"
    UNKNOWN_VERB: str = "Ich weiß nicht, wie ich '{}' soll."

    # --- Systems (AI / NPC / Quests / Effects / Objects / Map / Journal / Save) ---
    NPC_LEAVES: str = "{npc} verlässt den Bereich{direction}."
    NPC_ENTERS: str = "{npc} betritt den Bereich{direction}."
    NPC_NODS: str = "{npc} nickt dir zu."
    NPC_NERVOUS: str = "{npc} schaut sich nervös um."
    NPC_SEARCHING: str = "{npc} sieht sich suchend um."
    NPC_DEPARTS: str = "{npc} bricht auf{direction}."
    QUEST_NEW: str = "NEUE AUFGABE: {title}"
    QUEST_GOAL: str = "Ziel: {goal}"
    QUEST_UPDATED: str = "AUFGABE AKTUALISIERT: {title}"
    QUEST_NEW_GOAL: str = "Neues Ziel: {goal}"
    QUEST_COMPLETED: str = "AUFGABE ERLEDIGT: {title}"
    QUEST_FAILED: str = "AUFGABE FEHLGESCHLAGEN: {title}"
    QUEST_OUTCOME: str = "Ergebnis: {outcome}"
    EFFECT_NPC_CHANGED: str = "({name} wirkt verändert.)"
    EFFECT_KNOWLEDGE_GAINED: str = "(Wissen erhalten: {fact})"
    EFFECT_ITEM_RECEIVED: str = "Erhalten: {name}"
    EFFECT_STABILITY_DROP: str = "WARNUNG: Hüllenintegrität gefallen (-{amount:g}%)"
    EFFECT_LEFT_LOCATION: str = "Ort verlassen"
    OBJ_AUTO_OPEN: str = "Der {name} öffnet sich zischend von selbst."
    OBJ_AUTO_CLOSE: str = "Der {name} fällt scheppernd ins Schloss."
    ACOUSTIC_FROM_ABOVE_CEILING: str = "von Oben (durch die Decke)"
    ACOUSTIC_FROM_BELOW_FLOOR: str = "von Unten (durch den Boden)"
    ACOUSTIC_BEHIND_WALL: str = "hinter der Wand zu {name}"
    SAVE_INVALID_NAME: str = "Save-Name darf nur Buchstaben, Zahlen, '_' und '-' enthalten."
    SAVE_SUCCESS: str = "Spiel gespeichert unter: {filename}"
    SAVE_ERROR: str = "Fehler beim Speichern: {error}"
    LOAD_NOT_FOUND: str = "Spielstand '{filename}' nicht gefunden."
    LOAD_SUCCESS: str = "Spielstand geladen."
    LOAD_PROCESS_ERROR: str = "Fehler beim Verarbeiten des Spielstands."
    LOAD_CRITICAL_ERROR: str = "Kritischer Fehler beim Laden: {error}"
    MAP_HEADER: str = "--- TAKTISCHE KARTE (Bekannte Sektoren) ---"
    MAP_NO_DATA: str = "Keine Kartendaten verfügbar."
    MAP_DEAD_END: str = "Sackgasse"
    MAP_HERE_MARKER: str = " [HIER]"
    MAP_UNKNOWN_ROOM: str = "Unbekannt"
    MAP_CONNECTIONS: str = "> {name}{marker}\n  Verbindungen: {exits}"
    JOURNAL_HEADER: str = "--- PERSÖNLICHES LOGBUCH ---"
    JOURNAL_ACTIVE_TITLE: str = "AKTUELLE ZIELE:"
    JOURNAL_NO_ACTIVE: str = "Keine aktiven Aufgaben."
    JOURNAL_DONE_TITLE: str = "ERLEDIGT:"
    JOURNAL_FAILED_TITLE: str = "FEHLGESCHLAGEN:"
    ORACLE_HEADER: str = "--- ORACLE SYSTEM STATUS ---"
    ORACLE_TIME_STABILITY: str = "Zeit: T+{time}m | Stabilität: {stability}%"
    ORACLE_ACTIVE_QUESTS: str = "Aktive Quests: {count}"
    ORACLE_NO_ACTIVE_QUESTS: str = "Keine aktiven Quests."
    ORACLE_PENDING_EVENTS: str = "Ausstehende Zeit-Events: {count}"
    ORACLE_CRITICAL_STABILITY: str = "KRITISCH: Stations-Integrität gefährdet!"
    ORACLE_SABOTAGE_IN: str = "Sabotage entdeckt in: {rooms}"
    ORACLE_NOMINAL: str = "Systemdiagnose: Nominal."
    HELP_TEXT: str = (
        "VERFÜGBARE BEFEHLE\n\n"
        "BEWEGUNG:\n"
        "  gehe <richtung> (n, s, e, w, u, d, out)\n"
        "  klettere <objekt> (climb)\n"
        "  verstecke <objekt> (hide in)\n\n"
        "INTERAKTION:\n"
        "  schaue / l [objekt]\n"
        "  nimm <objekt>\n"
        "  benutze <objekt> [mit <objekt>]\n"
        "  öffne <objekt>\n"
        "  schließe <objekt>\n"
        "  lege <objekt> in/auf <objekt>\n"
        "  zerstöre / break <objekt>\n\n"
        "SYSTEM:\n"
        "  inv / i       - Inventar zeigen\n"
        "  journal / j   - Aufgaben ansehen\n"
        "  save [name]   - Speichern\n"
        "  load [name]   - Laden\n"
        "  map           - Karte anzeigen"
    )

    # --- General Errors ---
    ERR_HIDDEN: str = "Nicht während du versteckt bist."
