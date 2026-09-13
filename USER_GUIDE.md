# KI Analysetool – Benutzerhandbuch

## 1. Überblick

Das KI Analysetool ist eine lokale Desktop-Anwendung für die Analyse von Texten, Webseiten, YouTube-Transkripten, PDFs, Excel-Dateien, Bildern sowie CSV-/Textdateien. Inhalte werden lokal extrahiert und für die gewählte KI-Analyse an OpenAI übertragen. Ergebnisse, Tags, Favoriten und Verlauf werden lokal gespeichert.

## 2. Schnellstart

1. Starte die Anwendung mit `.venv/bin/python main.py`.
2. Hinterlege beim ersten Start deinen OpenAI API-Key.
3. Wähle eine Inhaltsquelle.
4. Gib einen Text oder eine URL ein beziehungsweise wähle eine Datei aus.
5. Wähle einen Analysetyp oder formuliere einen eigenen Prompt.
6. Klicke auf **Analyse starten** oder drücke `Strg/Cmd + Enter`.
7. Nutze Folgeaktionen, Visualisierung, Export oder Ergebnisverlauf.

## 3. Erfahrungsmodi und Lernpfad

Unter **Ansicht → Erfahrungsgrad ändern** stehen drei Modi zur Verfügung:

- **Anfänger:** größere Prompt-Eingabe, sichtbarer Lernpfad und ausführlichere Orientierung.
- **Fortgeschritten:** ausgewogene Standardansicht.
- **Experte:** kompaktere Analyseansicht; Lernpfad standardmäßig ausgeblendet.

Die Modi sperren keine Funktionen. Der Lernpfad wird nur durch erfolgreich ausgeführte Aktionen fortgeschrieben. Das Anzeigen einer Anleitung zählt nicht als Abschluss.

Mit **Später erinnern** lässt sich das Lernpanel ausblenden. Die Einstellung bleibt nach einem Neustart erhalten. **Zurücksetzen** löscht den Lernfortschritt nach Bestätigung.

## 4. Unterstützte Eingaben

### Direkter Text

Im Tab **Text** kann Text direkt eingegeben oder eingefügt werden.

### Webseiten

Im Tab **Webseite** wird eine öffentliche HTTP-/HTTPS-URL eingegeben. Lokale und private Netzwerkadressen sind aus Sicherheitsgründen blockiert. Die App entfernt typische Navigations-, Script- und Layoutbereiche und analysiert den lesbaren Inhalt.

### YouTube

Im Tab **YouTube** werden reguläre YouTube- und `youtu.be`-Links unterstützt. Das Video benötigt ein verfügbares deutsches oder englisches Transkript.

### PDF

Der Tab **PDF** verarbeitet lokale PDF-Dateien. Für die Analyse wird die Datei temporär zu OpenAI hochgeladen und nach Abschluss bestmöglich wieder entfernt.

Der Tab **Bild/PDF** ist für OCR gedacht und kann auch gescannte PDFs verarbeiten.

### Excel

Unterstützt werden `.xlsx` und `.xls`. Nach der Auswahl können Arbeitsblätter gewählt und Daten in einer Vorschau geprüft werden.

### Bilder und OCR

Unterstützt werden `.png`, `.jpg`, `.jpeg`, `.bmp`, `.tiff` und `.tif`. OCR benötigt Tesseract. Die verfügbaren OCR-Sprachen hängen von der lokalen Tesseract-Installation ab.

### CSV und Textdateien

Unterstützt werden `.csv`, `.tsv` und `.txt`. Mehrere Dateien können kombiniert werden. Verfügbare Kombinationsarten sind `concat`, `merge` und `separate`.

### Mehrere Dateien

Im Tab **Multi-Datei** können unterstützte Dateien gemeinsam ausgewählt werden. **Vorschau erstellen** zeigt zunächst den zusammengeführten Analyseinhalt. Die KI-Analyse wird anschließend mit **Analyse starten** ausgelöst.

### Drag & Drop

Excel-, Bild-/PDF-, CSV-/Text- und Multi-Datei-Bereiche unterstützen Drag & Drop, wenn `tkinterdnd2` auf dem System geladen werden kann. Der System-Dateidialog bleibt immer als Fallback verfügbar. Nicht unterstützte oder nicht vorhandene Dateien werden nicht übernommen.

## 5. Analysearten

- **Prompt senden:** eigener Auftrag; `{text}` kann als Platzhalter verwendet werden.
- **Zusammenfassung:** komprimiert den Inhalt.
- **Keyword-Extraktion:** identifiziert zentrale Begriffe.
- **Sentiment Analyse:** bewertet Stimmung und Tonalität.
- **Themen-Erkennung:** erkennt Hauptthemen.

Über **Vorlagen** steht eine nach Erfahrungsgrad gefilterte und durchsuchbare Prompt-Bibliothek zur Verfügung.

## 6. Modellwahl und Kosten

Die aktuell in der Anwendung registrierten Modelle werden im Modell-Dropdown angezeigt. Modellpreise sind Schätzwerte aus der Anwendungskonfiguration und können sich beim Anbieter ändern.

Nach einer erfolgreichen Analyse zeigt die Statusleiste den erfassten Tokenverbrauch und die geschätzten Sitzungskosten. Unter **Erweiterte Funktionen → Token- & Kosten-Übersicht** können die Werte angesehen und zurückgesetzt werden.

Vor der Übertragung schätzt die App die Kosten der Anfrage aus der Textlänge und dem gewählten Modell. Erscheint der Übertragungsdialog, enthält er diese Schätzung.

In den **Einstellungen** kann ein optionales **Sitzungsbudget** in USD gesetzt werden. Ab 80 % Auslastung – gemessen an bisherigen plus geschätzten Kosten der nächsten Anfrage – wird vor jeder Analyse eine Bestätigung verlangt. Das Budget wird im Benutzerprofil gespeichert und beim Start geladen.

## 7. Ergebnisse und Folgeaktionen

Ergebnisse werden als formatierter Text angezeigt. Der Ergebnisbereich unterstützt:

- Zoom,
- einklappbare Abschnitte,
- Kopieren in die Zwischenablage,
- PDF-Export,
- Zusammenfassen,
- Vertiefen,
- Übersetzen,
- Analysieren,
- einfaches Erklären,
- Datenextraktion und weitere kontextabhängige Aktionen.

Fehlgeschlagene Extraktionen oder KI-Aufrufe werden nicht als erfolgreiche Ergebnisse gespeichert und erzeugen keinen Lernfortschritt.

## 8. Strukturierte Daten und Visualisierung

Die App versucht Tabellen, numerische Werte, Datumsangaben und Entitäten aus Ergebnissen zu erkennen. Nicht jede Analyse liefert visualisierbare Daten.

Verfügbare Diagrammtypen:

- Balken,
- Linie,
- Kreis,
- Streuung,
- Histogramm.

Diagramme können als PNG, PDF oder SVG exportiert werden. HTML-Export und Batch-Diagrammexport sind derzeit nicht verfügbar.

## 9. Export

Verfügbare Exportwege:

- Ergebnis als Text oder JSON,
- erste extrahierte Tabelle als CSV,
- strukturierte Daten als Excel,
- Analyseergebnis oder Report als PDF,
- Diagramm als PNG, PDF oder SVG,
- mehrere ausgewählte Ergebnisse als einzelne Dateien.

Dashboard-Templates, Pivot-Tabellen und frei konfigurierbare PDF-Layoutvorlagen sind derzeit nicht Bestandteil der App.

## 10. Ergebnisverlauf

Im Tab **Ergebnisverlauf** können gespeicherte Ergebnisse:

- durchsucht,
- nach Typ, Quelle, Zeitraum und Dateninhalt gefiltert,
- geöffnet,
- exportiert,
- verglichen,
- kombiniert oder
- nach Bestätigung gelöscht werden.

Tags und Favoriten stehen über das Menü **Erweiterte Funktionen** zur Verfügung. Der Vergleich zeigt Inhalte, Metadaten und erkannte Daten mehrerer Ergebnisse.

## 10.1 Projekte

Über **Erweiterte Funktionen → Projekte verwalten** können Projekte angelegt, umbenannt, archiviert und gelöscht werden. Das aktuelle Ergebnis lässt sich über den Dialog einem Projekt zuordnen. Beim Löschen eines Projekts bleiben die Ergebnisse erhalten – nur die Zuordnung wird entfernt.

## 10.2 Analyse-Rezepte

Über **Erweiterte Funktionen → Rezepte verwalten** lassen sich wiederverwendbare Analysekonfigurationen speichern:

- Prompt-Vorlage,
- Modell,
- Quelltyp,
- geplante Folgeaktionen,
- Exportformat.

„Aus aktuellem Prompt erstellen" übernimmt den gerade eingegebenen Prompt und das gewählte Modell. „Anwenden" lädt Modell und Prompt-Vorlage in die Oberfläche; die geplanten Folgeaktionen werden als Hinweis angezeigt. Die Ausführung von Folgeaktionen und Export erfolgt derzeit manuell.

## 10.3 Ergebnisse bearbeiten und Versionen

Über **Ergebnis bearbeiten** kann der Inhalt eines gespeicherten Ergebnisses geändert werden. Vor jeder Änderung sichert die App automatisch den bisherigen Stand als Version. Der **Versionsverlauf** zeigt alle Versionen, einen zeilenweisen Diff zur aktuellen Version und ermöglicht die Wiederherstellung – wobei auch dann zuerst der aktuelle Stand gesichert wird.

## 10.4 Batch-Verarbeitung

Über **Erweiterte Funktionen → Batch-Verarbeitung** lassen sich mehrere Dateien mit demselben Prompt analysieren:

- Jobs und Items werden persistent in der Ergebnisdatenbank gespeichert und überleben einen Neustart. Unterbrochene Jobs werden pausiert angezeigt und können fortgesetzt werden.
- Parallelität ist pro Job auf 1–4 Worker begrenzt.
- Jedes Item speichert Status, Versuche, Fehlercode, Token und geschätzte Kosten; Teilergebnisse werden sofort im Ergebnisverlauf gespeichert.
- Fehler werden nur bei wiederholbaren Fehlern (Rate-Limit, Timeout, Verbindung) einmal erneut versucht.
- Vor dem Versand prüft der lokale Datenschutz-Scanner den extrahierten Inhalt jedes Items; Items mit Funden werden als „skipped" markiert statt übertragen.
- Pause, Fortsetzen und Abbrechen sind jederzeit möglich; abgebrochene Jobs bleiben zur Einsicht erhalten.

Der Ergebnisvergleich enthält zusätzlich einen **Text-Diff-Tab** mit zeilenweisem Unified-Diff zwischen den ersten zwei ausgewählten Ergebnissen.

## 10.5 Quellenbelege, Datenbearbeitung und Prompt-Playground

**Quellenbelege prüfen** erkennt Zitate und Referenzen im Ergebnistext und validiert sie gegen die Original-Quelle:

- Verifiziert wird nur, was wörtlich (Whitespace-normalisiert) im Quelltext vorkommt.
- Nicht gefundene Zitate werden als „nicht gefunden" markiert – mögliche Umformulierung oder frei erfundener Beleg.
- Bei PDFs wird die Quelle seitenweise per OCR geladen: Eine Seitenangabe, die es gibt, gilt als „plausibel"; eine Seitenangabe jenseits der Dokumentlänge als „nicht gefunden" (möglicher erfundener Beleg).
- Bei YouTube werden die Transkript-Zeitmarken geladen: Zeitangaben innerhalb der Videodauer gelten als „plausibel", darüber hinaus als „nicht gefunden".
- Bei Webseiten wird der Inhalt erneut abgerufen; lokale Textdateien werden direkt gelesen.
- Abschnitts- und Zeilenangaben sowie Angaben ohne prüfbare Struktur bleiben „nicht prüfbar" und werden nie als verifiziert markiert.

**Extrahierte Daten bearbeiten** öffnet die strukturierten Daten als JSON-Editor. Die Eingabe wird gegen das `StructuredData`-Schema validiert; vor dem Speichern wird der bisherige Stand als Version gesichert.

**Diagramm-Vorschläge** analysiert die erste extrahierte Tabelle: Spaltenrollen (Zahl, Datum, Kategorie, Text), Fehlwertanteile und daraus begründete Diagrammvorschläge (Linie, Balken, Kreis, Streuung, Histogramm) inklusive Hinweis auf fehlende Werte.

**Prompt-Playground** führt denselben Inhalt mit mehreren Varianten aus – eine pro Zeile im Format `Modell | Prompt`. Die Varianten laufen nacheinander, Ergebnisse erscheinen mit Modell, Dauer und Tokenverbrauch in getrennten Tabs; ein Lauf lässt sich abbrechen. Ergebnisse werden nicht automatisch gespeichert.

## 10.6 Analyse-Provider (lokal oder Cloud)

In den **Einstellungen** lässt sich der Analyse-Provider wählen:

- **OpenAI (Cloud)**: Standard, benötigt den API-Key und verursacht API-Kosten.
- **Ollama (lokal)**: verbindet einen lokal laufenden Ollama-Server (`http://localhost:11434/v1`). Mit „Modelle erkennen" werden die installierten Modelle geladen; eines davon muss als lokales Modell eingetragen werden.
- **OpenAI-kompatibel (eigene URL)**: für Server wie LM Studio oder LocalAI. Die App erkennt an der URL, ob der Server lokal läuft (`localhost`/`127.0.0.1`) oder extern ist.

Bei lokalem Provider werden Inhalte nicht an eine Cloud übertragen, es entstehen keine API-Kosten und die Übertragungsbestätigung weist entsprechend auf „Lokale Verarbeitung" hin. Der lokale Datenschutz-Scan bleibt trotzdem aktiv.

Wichtig: Lokale Server benötigen lokal installierte Modelle (z. B. `llama3:latest`). Steht ein Cloud-Modellname wie `gpt-4o` auf einem lokalen Provider eingestellt, warnt die App in den Einstellungen und vor der Analyse – die Anfrage schlägt auf dem lokalen Server fehl, es gehen aber keine Daten an eine Cloud.

## 10.7 Updates

**Hilfe → Nach Updates suchen** vergleicht die installierte Version mit dem neuesten GitHub-Release. Bei einem verfügbaren Update kann das passende Paket für die eigene Plattform direkt in den Downloads-Ordner geladen werden oder die Release-Seite im Browser geöffnet werden. Die Installation erfolgt immer manuell – die App ersetzt sich nicht selbst. Optional kann in den Einstellungen „Beim Start nach Updates suchen" aktiviert werden (standardmäßig deaktiviert). Die Prüfung sendet nur eine Anfrage an die GitHub-Releases-API – keine Nutzungsdaten.

## 11. Analyse-Historie

Die Analyse-Historie hält die Schritte der aktuellen Sitzung einschließlich Folgeaktionen und Elternbeziehungen fest. Sitzungen können als JSON gespeichert werden. Sie ist nicht mit dem persistenten Ergebnisverlauf identisch.

## 12. Auto-Save und Einstellungen

Unter **Erweiterte Funktionen → Einstellungen** können aktiviert werden:

- Ergebnisse automatisch speichern,
- Visualisierungen automatisch erstellen,
- Datenschutzprüfung vor Übertragung,
- optionales Sitzungsbudget in USD (leer = unbegrenzt).

Die Einstellungen werden im lokalen Benutzerprofil gespeichert.

## 13. Backup und Wiederherstellung

**Backup erstellen** erzeugt ein ZIP-Archiv aus `results.db` und dem Ergebnisverzeichnis. Jedes Backup enthält ein `manifest.json` mit Formatversion, Zeitstempel und Dateiliste.

**Backup wiederherstellen** validiert das Archiv zuerst:

- ZIP-Integrität,
- erlaubte Archiveinträge (Schutz gegen Pfad-Manipulation/„Zip-Slip"),
- SQLite-Dateikopf der enthaltenen `results.db`,
- unterstützte Formatversion des Manifests.

Vor dem Überschreiben wird automatisch ein **Sicherungs-Backup** des aktuellen Stands erstellt (Dateiname mit `_sicherung`). Schlägt dieses fehl, wird der Restore abgebrochen, damit kein Datenverlust entsteht. Backups ohne Manifest (ältere Versionen) werden mit Warnung akzeptiert.

Automatisch geplante tägliche Backups, 30-Tage-Aufbewahrung, selektive Wiederherstellung und Merge-Restore sind derzeit nicht verfügbar.

## 14. Datenschutz und Sicherheit

- Der API-Key wird bevorzugt im Schlüsselbund des Betriebssystems gespeichert.
- Ohne Keyring kann `config.ini` als Klartext-Fallback verwendet werden; die Datei erhält restriktive Zugriffsrechte.
- Secret-Muster werden in Logs maskiert.
- Private, lokale, Link-Local- und reservierte URL-Ziele sind blockiert.
- Jeder Redirect wird erneut geprüft.
- TLS-Prüfung kann nicht deaktiviert werden.
- Analyseinhalte werden an OpenAI gesendet.
- PDF-Dateien im PDF-Analysetab werden temporär als Datei hochgeladen.
- Ergebnisse und Benutzerprofil bleiben lokal.
- Vor jeder Übertragung prüft ein **lokaler Datenschutz-Scanner** den ausgehenden Text auf E-Mail-Adressen, IBANs, Kreditkartennummern (mit Luhn-Prüfung), Telefonnummern, API-Keys und Passwort-/Secret-Zuweisungen. Es werden keine Daten zum Scannen an externe Dienste gesendet.
- Bei Funden, einem PDF-Upload oder einer Budget-Warnung erscheint ein kombinierter **Bestätigungsdialog** mit Übertragungshinweis, Fundstellen (maskiert) und Kostenschätzung. Möglich sind „Senden", „Schwärzen & senden" (Funde werden durch Platzhalter ersetzt) und „Abbrechen" – bei Abbruch werden keine Daten übertragen.
- Die Datenschutzprüfung lässt sich in den Einstellungen deaktivieren.

Lade keine Dateien hoch, die Passwörter, private Schlüssel oder andere Geheimnisse enthalten.

## 15. Tastaturkürzel

- `Strg/Cmd + Enter`: Analyse starten
- `Strg/Cmd + S`: aktuelles Ergebnis speichern
- `Strg/Cmd + E`: aktuelles Ergebnis als PDF exportieren
- `Strg/Cmd + F`: Favoriten anzeigen
- `Escape`: unterstützte Hilfe- und Dialogfenster schließen

## 16. Hilfe

Kleine **?**-Buttons können mit Maus oder Tastatur fokussiert und aktiviert werden. Ein Klick beziehungsweise Enter öffnet eine dauerhaft lesbare Kontexthilfe.

Unter **Hilfe → Dokumentation anzeigen** öffnet sich die vollständige In-App-Hilfe mit:

- gerenderten Überschriften,
- Abschnittsauswahl,
- Suche,
- Navigation zum nächsten Treffer.

Das Onboarding kann über das Hilfemenü erneut gestartet werden.

## 17. Fehlerbehebung

### Kein API-Key

Öffne die App erneut und hinterlege den Key im Startdialog oder setze `OPENAI_API_KEY`.

### Webseite nicht erlaubt

Nur öffentliche HTTP-/HTTPS-Adressen sind zulässig. Interne und lokale Netzwerke werden absichtlich blockiert.

### YouTube-Transkript fehlt

Prüfe URL und verfügbare Untertitel. Videos ohne deutsches oder englisches Transkript können nicht analysiert werden.

### OCR funktioniert nicht

Installiere Tesseract und die benötigten Sprachpakete. Nutze möglichst scharfe, gerade und kontrastreiche Bilder.

### Große Dateien sind langsam

Teile große Dateien vor der Analyse in kleinere Einheiten. Automatisches Chunking und ein konfigurierbarer Analysecache sind derzeit nicht vorhanden.

### Diagnose

- Syntaxprüfung: `.venv/bin/python -m py_compile *.py`
- Setupprüfung: `.venv/bin/python setup_validation.py`
- Gesamttests: `.venv/bin/python run_tests.py --group all`
- Logdatei: `logs/application.log`

## 18. Derzeit nicht implementiert

Zur eindeutigen Abgrenzung gehören folgende Funktionen nicht zum aktuellen Stand:

- automatische tägliche Backups,
- selektiver oder zusammenführender Restore,
- automatische Verarbeitung großer Inhalte in Chunks,
- konfigurierbarer Analysecache,
- HTML-Diagrammexport,
- Batch-Export mehrerer Diagramme,
- Dashboard- und Pivot-Templates,
- automatische Telemetrie oder Cloud-Synchronisation,
- lokale KI-Provider.
