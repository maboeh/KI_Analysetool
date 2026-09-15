# KI Analysetool – Hilfe

## Schnellstart

1. Wähle eine Quelle: Text, Webseite, YouTube, PDF, Excel, Bild/PDF, CSV/Text oder Multi-Datei.
2. Gib Inhalt ein oder wähle eine Datei.
3. Wähle einen Analysetyp oder verwende einen eigenen Prompt.
4. Klicke auf **Analyse starten** oder drücke `Strg/Cmd + Enter`.
5. Nutze das Ergebnis für Folgeaktionen, Visualisierung oder Export.

Für eine sofortige Probe kannst du über **Hilfe → Onboarding erneut starten** einen Beispieltext einsetzen.

## Oberfläche

### Inhaltsquellen

Die linke beziehungsweise obere Seite enthält die Eingaben. Auf kleineren Bildschirmen ordnet die App Quellen und Analyse automatisch untereinander an. Der Trenner zwischen beiden Bereichen lässt sich verschieben und wird gespeichert.

### Analyse und Prompt

- **Prompt senden:** eigener Analyseauftrag; `{text}` dient als Platzhalter.
- **Zusammenfassung:** kurze Inhaltsübersicht.
- **Keyword-Extraktion:** zentrale Begriffe.
- **Sentiment Analyse:** Stimmung und Tonalität.
- **Themen-Erkennung:** Hauptthemen.

Der Button **Vorlagen** öffnet eine durchsuchbare Prompt-Bibliothek.

### Ergebnisbereich

Hier erscheinen formatierte Analyseergebnisse. Zoom und einklappbare Abschnitte erleichtern das Lesen. Rechts stehen passende Folgeaktionen bereit.

## Erfahrungsgrad und Lernpfad

Unter **Ansicht → Erfahrungsgrad ändern** kannst du wählen:

- **Anfänger:** mehr Platz und sichtbarer Lernpfad.
- **Fortgeschritten:** ausgewogene Standardansicht.
- **Experte:** kompakte Ansicht und ausgeblendeter Lernpfad.

Die Modi sperren keine Funktionen. Lernfortschritt entsteht nur durch erfolgreich ausgeführte Aktionen, nicht durch das Anzeigen einer Anleitung.

## Eingabeformate

### Text und Web

- Direkte Texteingabe
- öffentliche HTTP-/HTTPS-Webseiten
- YouTube-Links mit deutschem oder englischem Transkript

Private und lokale Netzwerkadressen werden blockiert.

### Dateien

- PDF: `.pdf`
- Excel: `.xlsx`, `.xls`
- Bilder: `.png`, `.jpg`, `.jpeg`, `.bmp`, `.tiff`, `.tif`
- CSV/Text: `.csv`, `.tsv`, `.txt`

Dateien können über den Systemdialog oder per Drag & Drop gewählt werden. Falls Drag & Drop auf einem System nicht geladen werden kann, bleibt der Dateidialog verfügbar.

## PDF und OCR

Der Tab **PDF** überträgt die ausgewählte PDF-Datei temporär zu OpenAI. Die App versucht, die Remote-Datei nach Abschluss oder Fehler wieder zu entfernen.

Der Tab **Bild/PDF** nutzt lokale OCR. Dafür müssen Tesseract und passende Sprachpakete installiert sein.

## Folgeaktionen

Je nach Ergebnis stehen unter anderem bereit:

- Zusammenfassen
- Vertiefen
- Übersetzen
- Analysieren
- Einfach erklären
- Daten extrahieren
- Als PDF exportieren
- In Zwischenablage kopieren

Fehlgeschlagene Aktionen werden nicht als erfolgreiche Ergebnisse oder Lernschritte gespeichert.

## Visualisierung

Unterstützte Diagramme:

- Balken
- Linie
- Kreis
- Streuung
- Histogramm

Diagramme können als PNG, PDF oder SVG exportiert werden. Dafür müssen geeignete numerische oder tabellarische Daten erkannt worden sein.

## Export

Verfügbar sind:

- JSON und Text
- CSV für tabellarische Daten
- Excel
- PDF-Ergebnis beziehungsweise PDF-Report
- PNG, PDF und SVG für Diagramme
- Export mehrerer ausgewählter Ergebnisse

HTML-Diagrammexport, Batch-Diagrammexport, Dashboard-Templates und Pivot-Templates sind derzeit nicht verfügbar.

## Ergebnisverlauf

Im Ergebnisverlauf kannst du:

- suchen und filtern,
- Ergebnisse öffnen,
- mehrere Ergebnisse vergleichen,
- Ergebnisse kombinieren,
- exportieren oder
- nach Bestätigung löschen.

Tags und Favoriten sind über **Erweiterte Funktionen** erreichbar.

## Projekte und Rezepte

- **Projekte verwalten**: Projekte bündeln Ergebnisse. Sie können erstellt, umbenannt, archiviert und gelöscht werden; gelöschte Projekte lassen die Ergebnisse unangetastet. Ein Ergebnis lässt sich über den Dialog einem Projekt zuordnen.
- **Rezepte verwalten**: Rezepte speichern Prompt-Vorlage, Modell, Quelltyp sowie geplante Folgeaktionen und Exportformat. „Anwenden" übernimmt Modell und Prompt in die Oberfläche.
- **Ergebnis bearbeiten**: Der Inhalt eines gespeicherten Ergebnisses kann bearbeitet werden. Vor jeder Änderung wird automatisch eine Version des bisherigen Inhalts gesichert.
- **Versionsverlauf**: Zeigt alle Versionen eines Ergebnisses, einen Diff zur aktuellen Version und eine Wiederherstellung mit Sicherungsversion.

## Batch-Verarbeitung

Über **Erweiterte Funktionen → Batch-Verarbeitung** können mehrere Dateien mit demselben Prompt analysiert werden:

- Jobs werden persistent gespeichert und überleben einen Neustart (unterbrochene Jobs können fortgesetzt werden).
- Pro Item gibt es Status, Fehlercode, Token- und Kostenerfassung.
- Pause, Fortsetzen und Abbrechen sind möglich; Parallelität ist auf 1–4 Worker begrenzt.
- Fehler werden nur bei wiederholbaren Fehlern (z. B. Rate-Limit, Timeout) einmal erneut versucht.
- Teilergebnisse werden sofort gespeichert. Items, bei denen der lokale Datenschutz-Scan sensible Daten findet, werden übersprungen statt übertragen.
- Der Vergleich im Ergebnisverlauf enthält zusätzlich einen zeilenweisen Text-Diff-Tab.

## Quellenbelege, Daten und Prompt-Playground

- **Quellenbelege prüfen**: Erkennt Zitate und Referenzen (Seiten-, Abschnitts-, Zeilen-, Zeitangaben) im Ergebnis und prüft sie gegen die Original-Quelle. Verifiziert wird nur, was wörtlich im Quelltext steht. Quellen werden je nach Typ mit Struktur geladen: lokale Textdateien direkt, PDFs seitenweise per OCR, YouTube-Transkripte mit Zeitmarken, Webseiten per erneutem Abruf. Seiten- und Zeitangaben, die in der Quellstruktur existieren, gelten als „plausibel"; Angaben auf nicht vorhandene Seiten oder Zeitpunkte jenseits der Videodauer gelten als „nicht gefunden" (möglicher erfundener Beleg). Ohne prüfbare Struktur bleibt eine Angabe „nicht prüfbar" – sie wird nie als verifiziert markiert.
- **Extrahierte Daten bearbeiten**: Öffnet die strukturierten Daten eines Ergebnisses als JSON-Editor mit Validierung; vor dem Speichern wird der bisherige Stand als Version gesichert.
- **Diagramm-Vorschläge**: Analysiert die erste extrahierte Tabelle, erkennt Spaltenrollen (Zahl, Datum, Kategorie, Text) und Fehlwerte und schlägt Diagrammtypen mit Begründung vor.
- **Prompt-Playground**: Führt denselben Inhalt mit mehreren Prompt-/Modell-Varianten nacheinander aus und zeigt Ergebnisse, Dauer und Tokenverbrauch nebeneinander. Variante pro Zeile im Format `Modell | Prompt`.

## Evaluationssuite

Unter **Erweiterte Funktionen → Qualität → Evaluationssuite** lassen sich Testfälle speichern und Prompt-/Modell-Varianten dagegen laufen lassen. Alle Checks sind lokal und deterministisch – es gibt bewusst kein LLM-as-Judge (Kosten/Datenschutz). Die Checks sind formale Prüfungen (enthält der Output X, ist er kürzer als N, ist es JSON …), **keine inhaltliche Qualitätsbewertung**.

- **Suites** (links): anlegen, umbenennen, löschen, als JSON importieren/exportieren; „Beispiel-Suite anlegen" erzeugt zwei Testfälle zum Ausprobieren.
- **Testfälle** (Mitte): bestehen aus Name, Input-Text und Erwartungen – eine pro Zeile:

| Syntax | Bedeutung |
|---|---|
| `enthält: Begriff` | Begriff muss im Output vorkommen (Groß-/Kleinschreibung und Leerzeichen tolerant) |
| `enthält nicht: Begriff` | Begriff darf nicht vorkommen |
| `regex: Ausdruck` | regulärer Ausdruck muss matchen; ungültige Ausdrücke schlagen als Check fehl |
| `max_zeichen: 800` | Output darf höchstens N Zeichen lang sein |
| `json` | Output (oder erster ```` ```json ````-Block) muss gültiges JSON sein |

- **Varianten** (rechts): eine pro Zeile im Format `Modell | Prompt` wie im Prompt-Playground. „Lauf starten" führt sequenziell Variante × Testfall aus; „Abbrechen" beendet den Lauf (verbleibende Kombinationen gelten als abgebrochen).
- **Datenschutz**: Findet der lokale Scan sensible Daten im Input und ist kein lokaler Provider aktiv, wird der Testfall als „datenschutz-blockiert" markiert und nicht gesendet. Bei lokalem Provider läuft die Analyse trotz Funden, da nichts das Gerät verlässt.
- **Ergebnisse**: Der Ergebnisbaum zeigt pro Variante bestandene Fälle, Check-Quote, Tokens, Kosten und Durchschnittsdauer; die beste Variante ist mit ★ markiert. Klick auf einen Testfall zeigt Output und Check-Details. Läufe werden gespeichert (Liste „Frühere Läufe") und können als Markdown-Bericht exportiert werden – er enthält nur die ersten 200 Zeichen je Output, keine vollständigen Inhalte.

## Analyse-Provider

Unter **Erweiterte Funktionen → Einstellungen → Analyse-Provider** kann zwischen drei Anbietern gewählt werden:

- **OpenAI (Cloud)**: Standard; benötigt API-Key, es fallen API-Kosten an.
- **Ollama (lokal)**: OpenAI-kompatibler lokaler Server (Standard-URL `http://localhost:11434/v1`). „Modelle erkennen" liest die installierten Modelle aus; kein API-Key nötig, keine Cloud-Übertragung, keine API-Kosten.
- **OpenAI-kompatibel (eigene URL)**: beliebiger Server (z. B. LM Studio, LocalAI). Ob Daten das Gerät verlassen, wird am Host der URL erkannt (localhost = lokal).

Bei lokalem Provider zeigt die Übertragungsbestätigung „Lokale Verarbeitung" und schätzt keine API-Kosten. Token werden weiterhin gezählt.

Lokale Server benötigen lokal installierte Modellnamen (z. B. `llama3:latest` – per „Modelle erkennen" abrufbar). Wird ein Cloud-Modellname wie `gpt-4o` auf einem lokalen Provider eingestellt, warnt die App in den Einstellungen und erneut vor der Analyse; die Anfrage würde auf dem lokalen Server fehlschlagen. Es werden trotzdem keine Daten an einen Cloud-Anbieter gesendet.

## Updates

Über **Hilfe → Nach Updates suchen** wird die GitHub-Releases-Seite auf eine neuere Version geprüft. In den Einstellungen lässt sich optional „Beim Start nach Updates suchen" aktivieren (standardmäßig aus). Es werden keine Nutzungsdaten übertragen. Bei einem verfügbaren Update bietet der Dialog zwei Wege: die Release-Seite im Browser öffnen oder das passende Paket für die eigene Plattform in den Downloads-Ordner laden. Installiert wird immer manuell – die App ersetzt oder startet sich nicht selbst.

## Backup

**Backup erstellen** sichert `results.db` und die lokalen Ergebnisdateien in einem ZIP-Archiv inklusive Manifest mit Formatversion und Dateiliste.

**Backup wiederherstellen** prüft das Archiv zuerst (Integrität, erlaubte Einträge, SQLite-Kopf, Formatversion). Vor dem Überschreiben wird automatisch ein Sicherungs-Backup des aktuellen Stands erstellt; schlägt dieses fehl, wird der Restore abgebrochen.

Automatische tägliche Backups, selektiver Restore und Merge-Restore sind derzeit nicht vorhanden.

## Datenschutz und Sicherheit

- API-Key bevorzugt im Betriebssystem-Keyring
- maskierte Secret-Muster in Logs
- SSRF-Schutz für Webseiten
- erneute Prüfung jedes Redirects
- keine abschaltbare TLS-Prüfung
- lokale Speicherung von Ergebnissen und Profil
- lokaler Datenschutz-Scan vor jeder Übertragung (E-Mail, IBAN, Kreditkarte, Telefon, API-Keys, Passwort-Zuweisungen)
- kombinierte Bestätigung mit Übertragungshinweis, Fundstellen und Kostenschätzung; bei Funden optional „Schwärzen & senden"
- temporärer PDF-Dateiupload bei PDF-Analyse (immer mit Hinweis bestätigt)

Übertrage keine Passwörter, Schlüssel oder andere Geheimnisse.

## Kostenkontrolle

- Die geschätzten Kosten einer Anfrage werden vor dem Senden im Bestätigungsdialog angezeigt (wenn dieser erscheint).
- In den **Einstellungen** kann ein optionales Sitzungsbudget in USD gesetzt werden. Ab 80 % Auslastung – einschließlich der geschätzten Kosten der nächsten Anfrage – erscheint vor jeder Analyse eine Bestätigung.
- Verbrauch und Budget sind unter **Erweiterte Funktionen → Token- & Kosten-Übersicht** einsehbar.

## Befehlspalette und Tastenkürzel

Mit `Strg+K` (macOS: `⌘K`) oder über **Ansicht → Befehlspalette…** öffnet sich die **Befehlspalette**: Alle Befehle lassen sich durch Tippen durchsuchen (Titel, Kategorien und Stichworte) und per Enter, Doppelklick oder Pfeiltasten ausführen. Befehle, die ein ausgewähltes Ergebnis benötigen, erscheinen ohne Ergebnis ausgegraut und geben einen Hinweis statt zu starten.

| Aktion | Windows/Linux | macOS |
|---|---|---|
| Analyse starten | `Strg+Enter` | `⌘↩` |
| Aktuelles Ergebnis speichern | `Strg+S` | `⌘S` |
| Ergebnis als PDF exportieren | `Strg+E` | `⌘E` |
| Favoriten anzeigen | `Strg+F` | `⌘F` |
| Befehlspalette öffnen | `Strg+K` | `⌘K` |
| Prompt-Playground | `Strg+Umschalt+P` | `⇧⌘P` |
| Batch-Verarbeitung | `Strg+B` | `⌘B` |
| Einstellungen | `Strg+,` | `⌘,` |
| Hilfe- und Dialogfenster schließen | `Escape` | `Escape` |

## Kontexthilfe

Die kleinen **?**-Buttons funktionieren mit Maus und Tastatur. Beim Fokus erscheint eine Kurzhilfe; ein Klick oder Enter öffnet ein dauerhaft lesbares Hilfefenster.

In dieser Dokumentation kannst du einen Abschnitt auswählen, nach Text suchen und zum nächsten Treffer wechseln.

## Häufige Probleme

### API-Key fehlt

Hinterlege den Key beim Start oder setze die Umgebungsvariable `OPENAI_API_KEY`.

### Analyse dauert lange

Große PDFs und OCR benötigen mehr Zeit. Teile große Dateien vorab auf oder verwende für Tests ein schnelleres Modell. Automatisches Chunking ist derzeit nicht verfügbar.

### Keine Diagramme verfügbar

Das Ergebnis benötigt geeignete numerische Werte oder Tabellen. Nicht jeder Text kann sinnvoll visualisiert werden.

### YouTube funktioniert nicht

Prüfe URL und verfügbare deutsche oder englische Untertitel.

### OCR funktioniert nicht

Prüfe Tesseract-Installation, Sprachpakete und Bildqualität.

## Diagnose

- Setup prüfen: `.venv/bin/python setup_validation.py`
- Gesamttests: `.venv/bin/python run_tests.py --group all`
- Logdatei: `logs/application.log`
- Vollständiges Handbuch: `USER_GUIDE.md`
