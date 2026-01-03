# Narratrix Engine v5.7 - Entwickler-Dokumentation

Willkommen in der Narratrix Engine! Dies ist eine moderne, modulare Text-Adventure-Engine, die auf Python und Pygame basiert. Sie bietet fortschrittliche Funktionen wie Akustik-Simulation, KI-gesteuerte NPCs, ein tiefes Crafting-System und Quest-Management.

## Inhaltsverzeichnis

1. [Installation & Start](#installation--start)
2. [Architektur-Überblick](#architektur-überblick)
3. [Kern-Mechaniken](#kern-mechaniken)
    * [Erkundung & Interaktion](#erkundung--interaktion)
    * [Crafting System](#crafting-system)
    * [Quest & Journal System](#quest--journal-system)
    * [NPCs & Dialoge](#npcs--dialoge)
4. [Daten-Struktur (Layer-System)](https://www.google.com/search?q=%23daten-struktur-layer-system)
5. [Tools](#tools)

---

## Installation & Start

### Voraussetzungen
* Python 3.9+
* Pygame (`pip install pygame`)
* Spacy (Optional, für NLP):
    ```bash
    pip install spacy
    python -m spacy download de_core_news_sm
    ```

### Starten
Führe die Hauptdatei aus, um das Spiel zu starten:
```bash
python main_gui.py
```

---

## Architektur-Überblick

Die Engine folgt einem **Entity-Component-System (ECS)** ähnlichen Ansatz, bei dem Daten (`data/`) strikt von der Logik (`engine/`) getrennt sind.

* **`engine/`**: Enthält die Spiellogik.
    * `handlers/`: Spezialisierte Module für Spieler-Aktionen (Inventory, Mechanics, Exploration).
    * `systems/`: Hintergrund-Simulationen (AI, Acoustics, Crafting, Quests).
    * `parser/`: Verarbeitet Texteingaben (Rule-Based oder NLP mit Spacy).
* **`data/`**: Enthält die Spielinhalte.
    * `common/`: Globale Assets (Items, NPCs), die überall verfügbar sind.
    * `chapters/`: Episodische Inhalte. Jedes Kapitel überschreibt oder erweitert die Common-Daten.

---

## Kern-Mechaniken

### Erkundung & Interaktion

Der Spieler interagiert über Textbefehle mit der Welt. Dank des neuen **Spacy-Parsers** versteht die Engine auch natürliche Sätze wie *"Repariere bitte schnell die Konsole mit dem Schraubenzieher"*.

* **Befehle:** `schaue`, `gehe`, `nimm`, `öffne`, `verstecke`, `warte`.
* **Rich Text:** Die Ausgabe unterstützt Tags wie `<alert>Gefahr!</alert>` oder `<success>Erfolg</success>` für farbliche Hervorhebungen.

### Crafting System

Das Crafting-System (`engine/systems/crafting.py`) geht über einfaches Kombinieren hinaus. Rezepte können komplexe Bedingungen haben:

1. **Zutaten:** Objekte, die verbraucht werden (z.B. "Kleber", "Scherbe").
2. **Werkzeuge:** Objekte, die im Inventar sein müssen, aber **nicht** verbraucht werden (z.B. "Lötkolben").
3. **Stationen:** Objekte, die sich im Raum befinden müssen (z.B. "Werkbank").
4. **Wissen (Blueprints):** Der Spieler muss das Rezept erst gelernt haben (z.B. durch Lesen eines Datenpads).

**Beispiel-Rezept (`items.py` oder `config.py`):**
```python
{
    "ingredients": ["circuit_board", "wire_coil"],
    "result": "hacked_chip",
    "tools": ["soldering_iron"],       # Werkzeug (bleibt erhalten)
    "station": "tech_workbench",       # Muss im Raum stehen
    "blueprint": "knows_circuitry",    # Wissen erforderlich
    "message": "Mit ruhiger Hand lötest du die Brücke auf den Chip."
}
```

### Quest & Journal System

Der **QuestManager** (`engine/systems/quest_manager.py`) verwaltet Aufgaben und Ziele.

* **Befehl:** `journal` (oder `j`, `aufgaben`) zeigt offene und erledigte Quests an.
* **Struktur:** Eine Quest hat einen Titel, eine Beschreibung und mehrere **Stages** (Stufen).
* **Trigger:** Quests werden durch Events (`events.py`) gestartet oder aktualisiert.

**Beispiel-Quest (`quests.py`):**
```python
"q_main_survival": {
    "title": "Überleben",
    "stages": {
        "1": "Verlasse das Cockpit.",
        "2": "Finde Vorräte in der Station.",
        "10": "Ziel erreicht."
    }
}
```

**Event-Trigger (`events.py`):**
```python
{
    "trigger": "condition",
    "condition": {"type": "location", "value": "ship_corridor"},
    "quest_update": {"id": "q_main_survival", "stage": 2} # Setzt Quest auf Stufe 2
}
```

### NPCs & Dialoge

NPCs werden durch das **AISystem** (`engine/systems/ai.py`) gesteuert.

* **States:** NPCs haben Zustände (z.B. `idle`, `working`, `alert`). Jeder Zustand kann eigene Dialoge und Verhaltensweisen definieren.
* **Dialog-Bäume:** Gespräche sind hierarchisch strukturiert. Antworten können **Effekte** auslösen (Items geben, Wissen vermitteln, Quest-Status ändern).
* **Pathfinding:** NPCs können sich intelligent durch die Station bewegen, um Ziele zu erreichen.

---

## Daten-Struktur (Layer-System)

Die Engine lädt Daten in Schichten:
1. **Common Layer:** Lädt `data/common/`. Hier liegen Basis-Items (Taschenlampe) und globale NPCs.
2. **Chapter Layer:** Lädt das aktuelle Kapitel (z.B. `data/chapters/ep0_arrival`).
    * Räume und Objekte aus dem Kapitel werden hinzugefügt.
    * Gleiche IDs überschreiben Common-Daten (Patching).
    * **Links:** Definieren Übergänge zwischen Common-Räumen (z.B. "Docking Bay") und Kapitel-Räumen (z.B. "Raumschiff").

---

## Tools

### Narratrix World Builder
Ein grafischer Editor zum Erstellen von Räumen, Verbindungen und NPCs.
* **Start:** `python tools/world_editor_gui.py`
* **Funktionen:**
    * Laden/Speichern des `data`-Ordners.
    * Visuelles Verknüpfen von Räumen.
    * Bearbeiten von NPC-Daten und Dialogen.