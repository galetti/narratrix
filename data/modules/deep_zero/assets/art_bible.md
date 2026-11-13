# Narratrix Art Bible & Asset Tracker (Deep Zero)

Wir speichern Grafiken für dieses Modul im Ordner: data/modules/deep_zero/assets/images/.
Dateiformat: .png oder .jpg.
Auflösung: 400x300 (4:3) für Räume, 300x300 (1:1) für Portraits empfohlen.

## 1. Räume (Environment Art)

| ID (Dateiname) | Status | Beschreibung (Prompt Basis) |
| :--- | :--- | :--- |
| scifi_hub.png | Vorhanden (unverknüpft) | Sci-Fi Kommandozentrale, düster, rote Notbeleuchtung, großes Terminal in der Mitte, Cyberpunk Stil. |
| scifi_mess.png | Vorhanden (unverknüpft) | Futuristische Kantine, dreckig, Essenreste, ein kaputter Replikator an der Wand sprüht Funken, Ozon-Nebel. |
| scifi_reactor.png | Vorhanden (unverknüpft) | Reaktorkern, glühend violette Energie, massive Maschinen, Hitzeflimmern, bedrohlich, industriell. |
| scifi_tunnel.png | Vorhanden (unverknüpft) | Wartungstunnel, eng, Röhren, Dampf tritt aus, klaustrophobisch, Metallgitterboden. |
| scifi_bridge.png | Vorhanden (unverknüpft) | Raumschiffbrücke, Blick in den Weltraum (Sterne), zerstörte Konsolen, ein umgestürzter Kommandosessel. |
| scifi_medbay.png | Vorhanden (unverknüpft) | Krankenstation, steril weiß aber verwüstet, offene Schränke, Scherben am Boden, kaltes Licht. |
| scifi_airlock.png | ❌ Offen | Luftschleuse, massives Stahlschott, kaltes steriles Licht, Warntafeln, kleines Fenster mit Blick auf Sterne, sauber, klaustrophobisch. |

## 2. Charaktere (Portraits)

| ID (Dateiname) | Status | Beschreibung (Prompt Basis) |
| :--- | :--- | :--- |
| face_aris_tired.png | Vorhanden (unverknüpft) | Portrait eines Ingenieurs, Mitte 40, Öl im Gesicht, tiefe Augenringe, panischer Blick, Sci-Fi Overall. |
| face_aris_alert.png | Vorhanden (unverknüpft) | Derselbe Ingenieur, aber fokussiert, entschlossen, wach, professionell. |
| face_val_pain.png | Vorhanden (unverknüpft) | Commander (Frau), strenge Züge, schmerzverzerrtes Gesicht, Blut an der Stirn, Uniform. |
| face_val_stern.png | Vorhanden (unverknüpft) | Commander (Frau), stoisch, autoritär, Führungspersönlichkeit, Salutieren. |
| face_ai_glitch.png | Vorhanden (unverknüpft) | Hologramm-Avatar, abstraktes Gesicht, schwer verrauscht (Glitch-Effekt), rotes Leuchten. |
| face_ai_calm.png | Vorhanden (unverknüpft) | Hologramm-Avatar, klare Linien, beruhigendes blaues Licht, freundliches KI-Gesicht. |

## 3. Workflow

1. Bild generieren (z.B. mit dem Prompt aus der Tabelle).
2. Datei als {ID}.png in data/modules/deep_zero/assets/images/ speichern und im Raum/NPC als `"img": "{ID}"` eintragen.
3. Spiel starten -> GUI lädt es automatisch.
