NARRATRIX Engine v1.0

Modulares, datengetriebenes Textadventure Framework

Über das Projekt

NARRATRIX ist eine moderne Engine für Interactive Fiction, geschrieben in Python. Sie unterscheidet sich von klassischen Parsern durch eine 4D-Simulations-Matrix, die Zeit und Ereignisse im Hintergrund steuert.

Aktuelles Szenario: Echo der Station Omega-9
Ein Cosmic-Horror-Mystery, bei dem ein zufälliger NPC zum Saboteur wird, während die Station langsam von einer Anomalie verschlungen wird.

Features

Narrative Matrix: Ereignisse finden zu festen Zeitpunkten statt, sofern der Spieler sie nicht verhindert.

Hydration System: Objekte werden direkt aus den Beschreibungen generiert (z.B. {locker:Spind|Verschlossen}).

Wissens-Datenbank: Dialoge und Optionen schalten sich frei, basierend auf dem, was der Spieler gesehen hat (knowledge-Tagging).

Container-Physik: Unterstützung für verschachtelte, verschlossene und offene Behälter.

Moderner Parser: Versteht Synonyme, ignoriert Füllwörter und nutzt Kontext.

Installation & Start

Voraussetzungen: Python 3.10+ installiert.

Abhängigkeiten:

pip install pygame


Starten:

python main_gui.py


Projektstruktur

main_gui.py: Grafisches Interface (Pygame) und Entry Point.

data/story_config.py: Alle Inhalte (Räume, Items, NPCs, Zeitlinie) befinden sich hier.

engine/game_state.py: Die Logik-Schicht (Zustandsverwaltung, KI, Zeit).

engine/command_parser.py: Die Input-Verarbeitung.

utils/rng.py: Zufallsgeneratoren.

Guide: Die Narrative Matrix designen

Die Matrix ist das Herzstück der Spannung. Sie definiert, was passiert, wenn der Spieler nichts tut.

1. Struktur eines Events

Ein Eintrag in der narrative_matrix Liste benötigt folgende Felder:

{
    "id": "evt_unique_name",      # Eindeutige ID
    "title": "Titel des Events",  # Wird im UI Log angezeigt
    "description": "Flavor Text", # Was der Spieler "spürt/hört"
    "trigger_time": 50,           # Wann passiert es (in Ticks)?
    "target_obj_id": "core",      # Welches Objekt wird geprüft?
    "penalty": 20,                # Schaden an der Station (Stability) bei Fehlschlag
    "fail_text": "...",           # Nachricht bei Sabotage/Defekt
    "success_text": "..."         # Nachricht bei intaktem System
}


2. Design-Philosophie

Kausalität: Ein Event prüft immer den Zustand eines Objekts (target_obj_id).

Ist das Objekt state: 'normal', ist das Event erfolgreich.

Ist das Objekt state: 'sabotaged', schlägt das Event fehl und die Station nimmt Schaden.

Timing: Lege Events so, dass der Saboteur (NPC) theoretisch Zeit hat, das Objekt vorher zu erreichen.

Beispiel: Wenn der Saboteur bei Tick 0 im Labor startet und zum Reaktor (3 Räume weiter) muss, sollte das Reaktor-Event frühestens bei Tick 20 stattfinden.

Eskalation: Starte mit kleinen Events (niedrige penalty) und steigere die Gefahr gegen Ende der Timeline.

3. Workflow für Autoren

Objekte definieren: Erstelle zuerst die kritischen Systeme (Generatoren, Lüftungen, Computer) in objects.

Timeline skizzieren: Zeichne einen Zeitstrahl (0 bis 100 Ticks). Setze 3-4 Knotenpunkte.

Saboteur-Pfad: Überlege, welchen Weg der Saboteur gehen muss, um diese Knotenpunkte anzugreifen. Passe die trigger_time an die Laufwege an.

Powered by NARRATRIX