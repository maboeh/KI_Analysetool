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

## Backup

**Backup erstellen** sichert `results.db` und die lokalen Ergebnisdateien in einem ZIP-Archiv. **Backup wiederherstellen** ersetzt nach Bestätigung die aktuelle Ergebnisdatenbank und die Ergebnisdateien vollständig.

Automatische tägliche Backups, selektiver Restore und Merge-Restore sind derzeit nicht vorhanden.

## Datenschutz und Sicherheit

- API-Key bevorzugt im Betriebssystem-Keyring
- maskierte Secret-Muster in Logs
- SSRF-Schutz für Webseiten
- erneute Prüfung jedes Redirects
- keine abschaltbare TLS-Prüfung
- lokale Speicherung von Ergebnissen und Profil
- Übertragung des Analyseinhalts an OpenAI
- temporärer PDF-Dateiupload bei PDF-Analyse

Übertrage keine Passwörter, Schlüssel oder andere Geheimnisse.

## Tastaturkürzel

- `Strg/Cmd + Enter`: Analyse starten
- `Strg/Cmd + S`: aktuelles Ergebnis speichern
- `Strg/Cmd + E`: Ergebnis als PDF exportieren
- `Strg/Cmd + F`: Favoriten anzeigen
- `Escape`: unterstützte Hilfe- und Dialogfenster schließen

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
