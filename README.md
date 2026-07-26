# Narratrix Engine 6.0

Narratrix ist eine modulare, datengetriebene Textadventure-Engine für Python und
Pygame. Kapitel enthalten ausschließlich Welt- und Storydaten; die Logik liegt
in wiederverwendbaren Handlern und Systemen. Sämtliche Kapitel werden beim Laden
gegen denselben Datenvertrag validiert.

## Installation und Start

Voraussetzung ist Python 3.9 oder neuer.

```bash
python -m pip install -r requirements.txt
python main_gui.py
```

`requirements.txt` installiert das deutsche Spacy-Modell
`de_core_news_md`. Ist Spacy oder das Modell nicht verfügbar, verwendet die
Engine automatisch den regelbasierten Parser.

Die Laufzeitkonfiguration liegt in `data/config.json`. Dort werden Startkapitel,
Auflösung, Parser und die optionale Verbindung zu einem lokalen
OpenAI-kompatiblen LLM konfiguriert.

## Architektur

- `engine/game_state.py`: autoritativer, speicherbarer Weltzustand.
- `engine/schema.py`: gemeinsamer Datenvertrag und Referenzprüfung.
- `engine/handlers/`: Spieleraktionen wie Bewegung, Inventar und Mechanik.
- `engine/systems/`: Events, Effekte, Quests, Crafting, KI und Akustik.
- `engine/parser/`: regelbasierte und Spacy-basierte Texteingabe.
- `data/common/`: kapitelübergreifende Inhalte.
- `data/chapters/`: konkrete Episoden und Testszenarien.
- `tools/`: Validator, Simulationsansicht und JSON World Editor.
- `tests/`: Regressionstests der Kernsysteme.

Der Common-Layer wird zuerst geladen. Kapitel überschreiben Räume, Objekte,
NPCs und Events mit derselben ID. Doppelte oder ungültige Referenzen führen
bereits beim Laden zu einem verständlichen Fehler.

## Verbindliche IDs

Bei Räumen und Objekten müssen Dictionary-Schlüssel und internes `id`-Feld
identisch sein:

```python
ITEMS = {
    "soldering_iron": {
        "id": "soldering_iron",
        "name": "Lötkolben",
        "location": "workshop",
        "type": "item",
        "is_tool": True,
    }
}
```

Mehrere Ressourcenstapel erhalten eindeutige Objekt-IDs und eine gemeinsame
`resource_id`, zum Beispiel `scrap_1` und `scrap_2` mit
`resource_id: "scrap_metal"`.

## Crafting

Rezepte validieren erst alle Voraussetzungen und verändern den Zustand danach
atomar:

```python
{
    "verb": "use",
    "items": ["scrap_metal", "workbench"],
    "ingredients": {"scrap_metal": 2, "wire": 1},
    "tools": ["soldering_iron"],
    "station": "workbench",
    "blueprint": "knows_circuitry",
    "result": "hacked_chip",
    "message": "Du lötest die Schaltung zusammen.",
}
```

- `items`: Interaktionspartner des Befehls.
- `ingredients`: verbrauchte Inventarressourcen.
- `tools`: erforderliche, nicht verbrauchte Inventargegenstände.
- `station`: erreichbares Objekt im aktuellen Raum.
- `blueprint`: erforderlicher Wissenseintrag.
- `result`: vorhandenes Ergebnisobjekt, das ins Inventar verschoben wird.

## Events, Effekte und Quests

Events besitzen einen Trigger (`time`, `location`, `condition`, `complex` oder
`manual`) und optionale Zusatzeffekte. Zeit- und Orts-Trigger können zusätzlich
mit `condition` eingeschränkt werden.

Unterstützte Effekte sind unter anderem:

- `message`, `learn`, `receive_item`, `update_object`
- `move_npc`, `teleport_npc`, `set_npc_state`
- `trigger_event`, `damage_stability`, `game_over`
- `quest_start`, `quest_update`, `quest_complete`, `quest_fail`
- `load_chapter`

Beispiel:

```python
{
    "id": "repair_complete",
    "trigger": "manual",
    "effects": [
        {"type": "quest_update", "id": "main_repair", "stage": 1},
        {"type": "message", "message": "Die Anlage läuft wieder."},
    ],
}
```

Quest-Stages sind Ganzzahlen. Abschluss und Fehlschlag werden explizit über
`quest_complete` beziehungsweise `quest_fail` ausgelöst.

## Befehle

- `schaue [objekt]`
- `gehe <richtung>`
- `klettere <objekt|hoch|runter>`
- `nimm`, `lege`, `gib`
- `benutze <objekt> mit <objekt>`
- `öffne`, `schließe`, `zerstöre`, `repariere`
- `rede mit <person>`
- `inventar`, `journal`, `karte`
- `warte [minuten]`
- `save [name]`, `load [name]`

Höhe, Erreichbarkeit, geschlossene Türen und Inventarbesitz werden von den
zustandsverändernden Aktionen geprüft.

## Werkzeuge

Aktuelles Kapitel validieren:

```bash
python tools/validator.py
python tools/validator.py data.chapters.ep0_test_lab.config
```

JSON-Welt bearbeiten:

```bash
python tools/world-editor.py
```

Der World Editor bewahrt neben Räumen, Objekten und NPCs auch Events, Quests und
Rezepte eines geladenen JSON-Kapitels. Solche JSON-Dateien können direkt mit
`StoryLoader.load_chapter("/pfad/zum/kapitel.json")` geladen werden.

Simulation anzeigen:

```bash
python tools/sim-viewer.py
```

## Tests

```bash
python -m unittest discover -v
```

Savegames verwenden Schema-Version 2 und enthalten die Kapitelidentität.
Spielstände älterer oder anderer Kapitel werden bewusst nicht stillschweigend
in einen inkompatiblen Zustand geladen.
