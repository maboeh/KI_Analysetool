# KI Analysetool - Benutzerhandbuch

## Inhaltsverzeichnis

1. [Erste Schritte](#erste-schritte)
2. [Grundlegende Funktionen](#grundlegende-funktionen)
3. [Erweiterte Features](#erweiterte-features)
4. [Workflows und Anwendungsfälle](#workflows-und-anwendungsfälle)
5. [Export und Visualisierung](#export-und-visualisierung)
6. [Ergebnis-Management](#ergebnis-management)
7. [Häufig gestellte Fragen (FAQ)](#häufig-gestellte-fragen-faq)
8. [Fehlerbehebung](#fehlerbehebung)
9. [Tipps und Best Practices](#tipps-und-best-practices)

## Erste Schritte

### Anwendung starten

1. **Desktop-Verknüpfung verwenden** (falls vorhanden)
   - Doppelklick auf das KI Analysetool-Symbol

2. **Über Kommandozeile starten**
   ```bash
   # Navigieren Sie zum Installationsverzeichnis
   cd /pfad/zum/ki-analysetool
   
   # Virtuelle Umgebung aktivieren
   source .venv/bin/activate  # macOS/Linux
   .venv\Scripts\activate     # Windows
   
   # Anwendung starten
   python main.py
   ```

3. **Erste Konfiguration prüfen**
   - Die Anwendung führt automatisch eine Setup-Validierung durch
   - Bei Fehlern werden Lösungsvorschläge angezeigt

### Benutzeroberfläche verstehen

```
┌─────────────────────────────────────────────────────────────┐
│                    KI Analysetool                           │
├─────────────────────────────────────────────────────────────┤
│ [Text] [YouTube] [Website] [Excel] [Bilder] [Multi-Files]  │ ← Input-Tabs
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Eingabebereich                                            │ ← Haupteingabe
│  (Text, Datei-Upload, URL)                                │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ [Zusammenfassung] [Schlüsselwörter] [Sentiment] [Custom]   │ ← Analysetypen
├─────────────────────────────────────────────────────────────┤
│                    [Analysieren]                            │ ← Aktions-Button
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Ergebnisbereich                                           │ ← Ausgabe
│  - Strukturierte Darstellung                               │
│  - Aktions-Buttons                                         │
│  - Visualisierungen                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Grundlegende Funktionen

### Text-Analyse

#### Direkte Texteingabe
1. **Text eingeben**
   - Klicken Sie auf den Tab "Text"
   - Geben Sie Ihren Text in das große Textfeld ein
   - Oder fügen Sie Text aus der Zwischenablage ein (Strg+V)

2. **Analysetyp wählen**
   - **Zusammenfassung**: Erstellt eine prägnante Zusammenfassung
   - **Schlüsselwörter**: Extrahiert wichtige Begriffe und Themen
   - **Sentiment**: Analysiert die emotionale Tonalität
   - **Custom**: Verwenden Sie einen eigenen Prompt

3. **Analyse starten**
   - Klicken Sie auf "Analysieren"
   - Warten Sie auf die Verarbeitung (Progress-Bar wird angezeigt)
   - Ergebnisse erscheinen im unteren Bereich

#### Beispiel: Zusammenfassung erstellen
```
Eingabetext: "Die Digitalisierung verändert unsere Arbeitswelt 
grundlegend. Neue Technologien wie KI und Automatisierung 
schaffen Effizienzgewinne, erfordern aber auch neue Kompetenzen..."

Analysetyp: Zusammenfassung

Ergebnis: Strukturierte Zusammenfassung mit Hauptpunkten,
Schlüsselerkenntnissen und Handlungsempfehlungen.
```

### URL-Analyse

#### YouTube-Videos analysieren
1. **YouTube-Tab auswählen**
2. **Video-URL eingeben**
   ```
   Beispiel: https://www.youtube.com/watch?v=dQw4w9WgXcQ
   ```
3. **Analysetyp wählen**
4. **Analysieren klicken**

**Hinweis**: Das Tool extrahiert automatisch das Transkript und analysiert den Inhalt.

#### Website-Inhalte analysieren
1. **Website-Tab auswählen**
2. **Website-URL eingeben**
   ```
   Beispiel: https://www.example.com/artikel
   ```
3. **Analysetyp wählen**
4. **Analysieren klicken**

**Hinweis**: Das Tool extrahiert den Haupttext der Website und ignoriert Navigation und Werbung.

### Datei-Upload und -Verarbeitung

#### Excel-Dateien verarbeiten
1. **Excel-Tab auswählen**
2. **Datei hochladen**
   - Klicken Sie auf "Datei auswählen"
   - Oder ziehen Sie die Datei per Drag & Drop
3. **Arbeitsblatt auswählen** (falls mehrere vorhanden)
4. **Vorschau prüfen**
   - Das Tool zeigt eine Vorschau der ersten Zeilen
   - Überprüfen Sie, ob die Daten korrekt erkannt wurden
5. **Analyse starten**

**Unterstützte Formate**: .xlsx, .xls, .xlsm

#### Bilder mit OCR verarbeiten
1. **Bilder-Tab auswählen**
2. **Bilddatei hochladen**
3. **OCR-Vorschau prüfen**
   - Das Tool zeigt den erkannten Text an
   - Bei schlechter Qualität: Bild verbessern oder manuell korrigieren
4. **Analyse starten**

**Unterstützte Formate**: PNG, JPG, JPEG, PDF (mit Bildern)

**OCR-Tipps**:
- Verwenden Sie hochauflösende Bilder (mindestens 300 DPI)
- Stellen Sie sicher, dass der Text gut lesbar ist
- Vermeiden Sie schräge oder verzerrte Aufnahmen

#### CSV-Dateien importieren
1. **Multi-Files-Tab auswählen**
2. **CSV-Datei hochladen**
3. **Delimiter-Erkennung prüfen**
   - Das Tool erkennt automatisch Komma, Semikolon oder Tab
   - Bei Bedarf manuell anpassen
4. **Spalten-Mapping überprüfen**
5. **Analyse starten**

#### Mehrere Dateien gleichzeitig verarbeiten
1. **Multi-Files-Tab auswählen**
2. **Mehrere Dateien auswählen**
   - Halten Sie Strg gedrückt für Mehrfachauswahl
   - Oder verwenden Sie Drag & Drop für mehrere Dateien
3. **Kombinationsmodus wählen**
   - **Zusammenführen**: Alle Inhalte werden kombiniert analysiert
   - **Einzeln**: Jede Datei wird separat analysiert
4. **Analyse starten**

## Erweiterte Features

### Interaktive Ergebnis-Verarbeitung

#### Folgeaktionen verwenden
Nach jeder Analyse erscheinen kontextuelle Aktions-Buttons:

1. **Zusammenfassen** 📝
   - Erstellt eine kürzere Zusammenfassung des Ergebnisses
   - Ideal für lange Analysen

2. **Vertiefen** 🔍
   - Führt eine detailliertere Analyse durch
   - Fügt zusätzliche Erkenntnisse hinzu

3. **Übersetzen** 🌐
   - Übersetzt das Ergebnis in andere Sprachen
   - Unterstützt alle gängigen Sprachen

4. **Analysieren** 📊
   - Führt eine Meta-Analyse des Ergebnisses durch
   - Identifiziert Muster und Trends

#### Analyse-Historie nutzen
- **Navigation**: Verwenden Sie die Pfeile, um zwischen Analyseschritten zu navigieren
- **Verzweigungen**: Erstellen Sie verschiedene Analyse-Pfade
- **Vergleich**: Vergleichen Sie verschiedene Analyseergebnisse

### Automatische Datenextraktion

#### Strukturierte Daten erkennen
Das Tool erkennt automatisch:

- **Tabellen**: Zeilen und Spalten mit Daten
- **Listen**: Aufzählungen und nummerierte Listen  
- **Numerische Werte**: Zahlen, Währungen, Prozentsätze
- **Entitäten**: Personen, Orte, Organisationen
- **Datumsangaben**: Verschiedene Datumsformate
- **Beziehungen**: Verbindungen zwischen Datenpunkten

#### Datenextraktion anpassen
1. **Extraktions-Panel öffnen**
   - Klicken Sie auf "Daten extrahieren" nach der Analyse
2. **Erkannte Daten prüfen**
   - Überprüfen Sie die automatisch erkannten Elemente
   - Korrigieren Sie falsch erkannte Daten
3. **Kategorien anpassen**
   - Weisen Sie Daten den richtigen Kategorien zu
   - Erstellen Sie neue Kategorien bei Bedarf

### Datenvisualisierung

#### Automatische Diagramm-Vorschläge
1. **Nach Datenextraktion**: Das Tool schlägt geeignete Diagrammtypen vor
2. **Vorschläge bewerten**: Jeder Vorschlag enthält eine Begründung
3. **Diagramm auswählen**: Klicken Sie auf den gewünschten Typ

#### Verfügbare Diagrammtypen

**Balkendiagramme** 📊
- Ideal für: Kategorische Daten, Vergleiche
- Beispiel: Verkaufszahlen nach Regionen

**Liniendiagramme** 📈
- Ideal für: Zeitreihen, Trends
- Beispiel: Umsatzentwicklung über Zeit

**Kreisdiagramme** 🥧
- Ideal für: Anteile, Prozentuale Verteilungen
- Beispiel: Marktanteile verschiedener Unternehmen

**Streudiagramme** 📍
- Ideal für: Korrelationen, Beziehungen
- Beispiel: Zusammenhang zwischen Preis und Qualität

**Histogramme** 📊
- Ideal für: Häufigkeitsverteilungen
- Beispiel: Altersverteilung in einer Gruppe

#### Diagramme anpassen
1. **Diagramm-Editor öffnen**
   - Klicken Sie auf "Anpassen" neben dem Diagramm
2. **Eigenschaften ändern**
   - **Titel**: Aussagekräftigen Titel eingeben
   - **Achsenbeschriftungen**: X- und Y-Achse benennen
   - **Farben**: Farbschema auswählen
   - **Stil**: Verschiedene Visualisierungsstile
3. **Vorschau aktualisieren**
   - Änderungen werden sofort angezeigt
4. **Speichern**: Angepasstes Diagramm übernehmen

## Workflows und Anwendungsfälle

### Anwendungsfall 1: Marktforschungsbericht analysieren

**Szenario**: Sie haben einen 50-seitigen PDF-Marktforschungsbericht und möchten die wichtigsten Erkenntnisse extrahieren und visualisieren.

**Schritt-für-Schritt-Anleitung**:

1. **Vorbereitung**
   ```
   Datei: marktforschung_2024.pdf
   Ziel: Zusammenfassung + Datenextraktion + Visualisierung
   ```

2. **Upload und Analyse**
   - PDF in Multi-Files-Tab hochladen
   - Analysetyp "Zusammenfassung" wählen
   - Analyse starten

3. **Ergebnis verarbeiten**
   - Strukturierte Zusammenfassung erhalten
   - "Vertiefen" klicken für detailliertere Analyse
   - Automatisch extrahierte Daten prüfen

4. **Datenvisualisierung**
   - Numerische Daten (Marktgrößen, Wachstumsraten) identifizieren
   - Balkendiagramm für Marktanteile erstellen
   - Liniendiagramm für Wachstumstrends generieren

5. **Export und Präsentation**
   - Excel-Export mit strukturierten Daten
   - Diagramme als PNG für Präsentationen
   - Zusammenfassung als PDF speichern

**Erwartetes Ergebnis**:
- Prägnante Zusammenfassung (2-3 Seiten)
- Excel-Datei mit Marktdaten
- 3-5 aussagekräftige Diagramme
- Handlungsempfehlungen

### Anwendungsfall 2: Social Media Content-Analyse

**Szenario**: Analyse von Kundenfeedback aus verschiedenen Quellen für Sentiment-Analyse und Trend-Erkennung.

**Workflow**:

1. **Datensammlung**
   - CSV-Export aus Social Media Tools
   - Screenshot-Sammlung von Posts
   - Website-URLs mit Bewertungen

2. **Multi-Source-Analyse**
   - CSV-Datei mit Kommentaren hochladen
   - Screenshots per OCR verarbeiten
   - Website-URLs einzeln analysieren

3. **Sentiment-Analyse**
   - Analysetyp "Sentiment" für alle Quellen
   - Ergebnisse vergleichen und kombinieren
   - Trends über Zeit identifizieren

4. **Visualisierung**
   - Sentiment-Verteilung als Kreisdiagramm
   - Zeitliche Entwicklung als Liniendiagramm
   - Top-Themen als Balkendiagramm

### Anwendungsfall 3: Wissenschaftliche Literatur-Review

**Szenario**: Systematische Analyse von 20 wissenschaftlichen Artikeln zu einem Forschungsthema.

**Workflow**:

1. **Batch-Processing**
   - Alle PDF-Artikel in Multi-Files-Tab laden
   - "Einzeln analysieren" wählen
   - Analysetyp "Schlüsselwörter" + "Zusammenfassung"

2. **Ergebnis-Aggregation**
   - Alle Einzelergebnisse im Results-Browser öffnen
   - Vergleichsfunktion nutzen
   - Gemeinsame Themen identifizieren

3. **Meta-Analyse**
   - Kombinierte Analyse aller Ergebnisse
   - "Analysieren" auf aggregierte Daten anwenden
   - Forschungslücken und Trends identifizieren

4. **Dokumentation**
   - Strukturierte Übersicht als Excel
   - Literatur-Matrix mit Schlüsselwörtern
   - Trend-Visualisierungen

### Anwendungsfall 4: Finanzberichte-Analyse

**Szenario**: Quartalsweise Analyse von Unternehmensberichten für Investment-Entscheidungen.

**Workflow**:

1. **Datenextraktion**
   - Excel-Dateien mit Finanzdaten
   - PDF-Berichte mit Textanalyse
   - Website-Investor-Relations-Seiten

2. **Strukturierte Analyse**
   - Automatische Extraktion von Kennzahlen
   - Sentiment-Analyse der Managementkommentare
   - Vergleich mit Vorquartalen

3. **Visualisierung**
   - Umsatz- und Gewinnentwicklung
   - Kennzahlen-Dashboard
   - Risiko-Indikatoren

4. **Investment-Report**
   - Zusammenfassung der Kernerkenntnisse
   - Handlungsempfehlungen
   - Risiko-Bewertung

## Export und Visualisierung

### Excel-Export

#### Automatischer Export
Nach der Datenextraktion:
1. **Export-Button erscheint** automatisch bei erkannten strukturierten Daten
2. **Ein-Klick-Export**: Standardformat mit optimaler Formatierung
3. **Datei-Speicherort**: Automatisch im `exports/` Verzeichnis

#### Erweiterte Export-Optionen
1. **Export-Dialog öffnen**
   - Klicken Sie auf den Pfeil neben "Excel exportieren"
2. **Optionen konfigurieren**
   ```
   ✓ Spaltenüberschriften einschließen
   ✓ Datentypen formatieren
   ✓ Leere Zeilen entfernen
   ✓ Duplikate markieren
   ✓ Zusammenfassung hinzufügen
   ```
3. **Template auswählen**
   - Standard: Einfache Tabelle
   - Erweitert: Mit Formatierung und Formeln
   - Dashboard: Mit integrierten Diagrammen

#### Excel-Datei-Struktur
```
Arbeitsblatt 1: "Rohdaten"
├── Spalte A: ID/Index
├── Spalte B-X: Extrahierte Datenfelder
└── Letzte Zeile: Zusammenfassung/Summen

Arbeitsblatt 2: "Metadaten"
├── Analysedatum
├── Datenquelle
├── Extraktionsparameter
└── Qualitätsindikatoren

Arbeitsblatt 3: "Visualisierungen" (optional)
├── Eingebettete Diagramme
└── Pivot-Tabellen
```

### Diagramm-Export

#### Export-Formate
- **PNG**: Für Präsentationen und Dokumente (Standard)
- **PDF**: Für hochwertige Drucke
- **SVG**: Für skalierbare Vektorgrafiken
- **HTML**: Für interaktive Web-Einbindung

#### Export-Qualität konfigurieren
```
Auflösung:
○ Standard (150 DPI) - für Bildschirm
○ Hoch (300 DPI) - für Druck
○ Sehr hoch (600 DPI) - für professionelle Publikationen

Größe:
○ Klein (800x600)
○ Mittel (1200x900) - Standard
○ Groß (1920x1440)
○ Benutzerdefiniert

Stil:
○ Hell - für helle Hintergründe
○ Dunkel - für dunkle Präsentationen
○ Transparent - ohne Hintergrund
```

#### Batch-Export
1. **Mehrere Diagramme auswählen**
2. **Batch-Export starten**
3. **Einheitliche Formatierung** wird automatisch angewendet
4. **ZIP-Archiv** mit allen Exporten wird erstellt

### PDF-Export

#### Vollständiger Analyse-Report
1. **Report-Generator öffnen**
   - Klicken Sie auf "PDF-Report erstellen"
2. **Inhalte auswählen**
   ```
   ✓ Zusammenfassung
   ✓ Detailanalyse
   ✓ Extrahierte Daten (Tabellen)
   ✓ Visualisierungen
   ✓ Metadaten und Quellen
   ```
3. **Layout konfigurieren**
   - Template auswählen (Business, Academic, Simple)
   - Firmenlogo hinzufügen (optional)
   - Farbschema anpassen

#### PDF-Struktur
```
Seite 1: Deckblatt
├── Titel der Analyse
├── Datum und Autor
├── Zusammenfassung (Executive Summary)
└── Inhaltsverzeichnis

Seiten 2-X: Hauptinhalt
├── Detailanalyse
├── Strukturierte Daten
├── Visualisierungen
└── Erkenntnisse

Letzte Seite: Anhang
├── Datenquellen
├── Methodik
├── Technische Details
└── Kontaktinformationen
```

## Ergebnis-Management

### Ergebnisse speichern

#### Automatisches Speichern
- **Jede Analyse** wird automatisch gespeichert
- **Eindeutige ID** für jedes Ergebnis
- **Metadaten** werden automatisch erfasst:
  ```
  - Analysedatum und -zeit
  - Datenquelle (Datei, URL, Text)
  - Analysetyp und Parameter
  - Verarbeitungszeit
  - Token-Verbrauch
  ```

#### Manuelles Speichern mit Namen
1. **"Speichern unter" klicken**
2. **Aussagekräftigen Namen eingeben**
   ```
   Beispiele:
   - "Marktanalyse Q4 2024"
   - "Kundenfeedback Social Media Jan"
   - "Literatur Review KI Trends"
   ```
3. **Tags hinzufügen** (optional)
   ```
   Tags: marktforschung, q4, 2024, automotive
   ```
4. **Beschreibung ergänzen** (optional)

### Results Browser verwenden

#### Ergebnisse finden
1. **Results Browser öffnen**
   - Klicken Sie auf "Gespeicherte Ergebnisse" im Hauptmenü
2. **Suchoptionen nutzen**
   ```
   Textsuche: Suche in Namen und Inhalten
   Datumsfilter: Letzte Woche, Monat, Jahr
   Typ-Filter: Nach Analysetyp filtern
   Tag-Filter: Nach zugewiesenen Tags
   Quelle-Filter: Nach Datenquelle (Excel, PDF, etc.)
   ```

#### Ergebnis-Liste verstehen
```
┌─────────────────────────────────────────────────────────────┐
│ 📊 Marktanalyse Q4 2024                    📅 15.12.2024   │
│ 📁 marktforschung.pdf → Zusammenfassung    ⏱️ 2 Min        │
│ 🏷️ marktforschung, automotive, q4          💾 2.3 MB       │
├─────────────────────────────────────────────────────────────┤
│ 📈 Social Media Sentiment                  📅 14.12.2024   │
│ 📁 comments.csv → Sentiment                ⏱️ 45 Sek       │
│ 🏷️ social-media, sentiment, dezember      💾 856 KB       │
└─────────────────────────────────────────────────────────────┘
```

**Symbole verstehen**:
- 📊 = Datenanalyse mit Visualisierungen
- 📈 = Trend-Analyse
- 📝 = Text-Zusammenfassung
- 🔍 = Detailanalyse
- 🌐 = Übersetzung

#### Ergebnisse verwalten
**Einzelne Aktionen**:
- **Öffnen**: Ergebnis in Hauptansicht laden
- **Duplizieren**: Kopie für weitere Bearbeitung
- **Exportieren**: Als PDF, Excel oder JSON
- **Löschen**: Permanent entfernen (mit Bestätigung)

**Batch-Aktionen**:
- **Mehrfachauswahl**: Strg+Klick für mehrere Ergebnisse
- **Batch-Export**: Alle ausgewählten Ergebnisse exportieren
- **Batch-Tagging**: Tags zu mehreren Ergebnissen hinzufügen
- **Archivieren**: Ältere Ergebnisse archivieren

### Ergebnis-Vergleich

#### Zwei Ergebnisse vergleichen
1. **Erstes Ergebnis auswählen** und öffnen
2. **"Vergleichen mit" klicken**
3. **Zweites Ergebnis aus Liste wählen**
4. **Vergleichsansicht** wird geöffnet:
   ```
   ┌─────────────────┬─────────────────┐
   │   Ergebnis A    │   Ergebnis B    │
   ├─────────────────┼─────────────────┤
   │ Inhalt A        │ Inhalt B        │
   │                 │                 │
   │ Unterschiede werden farblich      │
   │ hervorgehoben                     │
   └─────────────────┴─────────────────┘
   ```

#### Mehrere Ergebnisse kombinieren
1. **Mehrere Ergebnisse auswählen** (Strg+Klick)
2. **"Kombinieren" klicken**
3. **Kombinationsmodus wählen**:
   - **Zusammenführen**: Alle Inhalte in einem Dokument
   - **Vergleichen**: Nebeneinander-Darstellung
   - **Aggregieren**: Statistische Zusammenfassung
4. **Neues kombiniertes Ergebnis** wird erstellt

### Backup und Synchronisation

#### Automatisches Backup
- **Tägliche Backups** der Ergebnis-Datenbank
- **Backup-Speicherort**: `./backups/` Verzeichnis
- **Aufbewahrung**: 30 Tage (konfigurierbar)

#### Manuelles Backup
1. **Einstellungen öffnen**
2. **"Backup erstellen" klicken**
3. **Speicherort wählen**
4. **Backup-Umfang festlegen**:
   ```
   ✓ Alle Ergebnisse
   ✓ Visualisierungen
   ✓ Konfiguration
   ✓ Benutzereinstellungen
   ```

#### Backup wiederherstellen
1. **"Backup wiederherstellen" in Einstellungen**
2. **Backup-Datei auswählen**
3. **Wiederherstellungsoptionen**:
   - Vollständige Wiederherstellung (überschreibt alles)
   - Selektive Wiederherstellung (nur ausgewählte Elemente)
   - Merge-Modus (kombiniert mit vorhandenen Daten)

## Häufig gestellte Fragen (FAQ)

### Installation und Setup

**F: Die Anwendung startet nicht. Was kann ich tun?**

A: Prüfen Sie folgende Punkte:
1. Python 3.12+ ist installiert: `python --version`
2. Virtuelle Umgebung ist aktiviert
3. Alle Abhängigkeiten sind installiert: `pip list`
4. Führen Sie die Setup-Validierung aus: `python setup_validation.py`

**F: Ich erhalte einen "API Key nicht gefunden" Fehler.**

A: 
1. Prüfen Sie die `config.ini` Datei im Hauptverzeichnis
2. Stellen Sie sicher, dass der OpenAI API-Key korrekt eingetragen ist
3. Alternativ setzen Sie die Umgebungsvariable: `export OPENAI_API_KEY=sk-...`
4. Testen Sie den API-Key auf der OpenAI-Website

**F: Tesseract OCR wird nicht gefunden.**

A: Je nach Betriebssystem:
- **Windows**: Installieren Sie Tesseract und passen Sie den Pfad in `config.ini` an
- **macOS**: `brew install tesseract`
- **Linux**: `sudo apt-get install tesseract-ocr tesseract-ocr-deu`

### Verwendung und Funktionen

**F: Welche Dateiformate werden unterstützt?**

A: 
- **Text**: .txt, .md, direkte Eingabe
- **Excel**: .xlsx, .xls, .xlsm
- **Bilder**: .png, .jpg, .jpeg (mit OCR)
- **PDF**: .pdf (Text-Extraktion und OCR)
- **CSV**: .csv (automatische Delimiter-Erkennung)
- **Web**: URLs von Websites und YouTube-Videos

**F: Wie groß können die Dateien sein?**

A: 
- **Standard-Limit**: 100 MB pro Datei
- **Empfohlen**: Unter 50 MB für optimale Performance
- **Anpassung**: Limit kann in `config.ini` geändert werden
- **Große Dateien**: Werden automatisch in Chunks verarbeitet

**F: Kann ich mehrere Sprachen analysieren?**

A: 
- **Hauptsprache**: Deutsch (optimiert)
- **Unterstützt**: Alle Sprachen, die OpenAI GPT-4 versteht
- **OCR**: Deutsch, Englisch, weitere Sprachen konfigurierbar
- **Übersetzung**: Automatische Übersetzung in beliebige Sprachen

**F: Werden meine Daten an externe Server gesendet?**

A: 
- **OpenAI API**: Nur der zu analysierende Text wird an OpenAI gesendet
- **Lokale Speicherung**: Alle Ergebnisse bleiben auf Ihrem Computer
- **Keine Tracking**: Keine Übertragung von Nutzungsdaten
- **Datenschutz**: Siehe OpenAI's Datenschutzrichtlinien für API-Nutzung

### Performance und Optimierung

**F: Die Analyse dauert sehr lange. Wie kann ich sie beschleunigen?**

A: 
1. **Dateigröße reduzieren**: Große Dateien in kleinere Teile aufteilen
2. **Chunk-Größe anpassen**: In `config.ini` kleinere Chunks einstellen
3. **Parallel-Processing**: Aktivieren Sie Multi-Threading in den Einstellungen
4. **Cache nutzen**: Aktivieren Sie Caching für wiederholte Analysen

**F: Die Anwendung verbraucht viel Speicher.**

A: 
1. **Cache leeren**: Regelmäßig temporäre Dateien löschen
2. **Alte Ergebnisse archivieren**: Nicht mehr benötigte Analysen archivieren
3. **Speicher-Limit**: Konfigurieren Sie Speicher-Limits in den Einstellungen
4. **Neustart**: Starten Sie die Anwendung bei Speicherproblemen neu

### Datenextraktion und -export

**F: Die automatische Datenextraktion erkennt meine Tabellen nicht.**

A: 
1. **Format prüfen**: Stellen Sie sicher, dass Tabellen klar strukturiert sind
2. **Manuell korrigieren**: Nutzen Sie die manuelle Korrektur-Funktion
3. **Vorverarbeitung**: Bereinigen Sie die Daten vor der Analyse
4. **Alternative Formate**: Versuchen Sie CSV-Export aus der Originalquelle

**F: Excel-Export enthält nicht alle Daten.**

A: 
1. **Datentypen prüfen**: Stellen Sie sicher, dass alle Datentypen erkannt wurden
2. **Export-Optionen**: Überprüfen Sie die Export-Einstellungen
3. **Manuell hinzufügen**: Ergänzen Sie fehlende Daten manuell
4. **Template anpassen**: Verwenden Sie ein anderes Export-Template

### Visualisierung

**F: Warum werden keine Diagramme vorgeschlagen?**

A: 
- **Numerische Daten erforderlich**: Diagramme benötigen numerische Werte
- **Datenqualität**: Prüfen Sie, ob Zahlen korrekt erkannt wurden
- **Mindestanzahl**: Mindestens 3-5 Datenpunkte erforderlich
- **Manuell erstellen**: Nutzen Sie die manuelle Diagramm-Erstellung

**F: Diagramme werden nicht korrekt angezeigt.**

A: 
1. **Matplotlib-Backend**: Prüfen Sie die Matplotlib-Konfiguration
2. **Display-Einstellungen**: Passen Sie die Anzeige-Einstellungen an
3. **Neustart**: Starten Sie die Anwendung neu
4. **Alternative Formate**: Exportieren Sie Diagramme als Dateien

### Fehlerbehebung

**F: Ich erhalte einen "Unbekannter Fehler" beim Analysieren.**

A: 
1. **Log-Dateien prüfen**: Schauen Sie in `./logs/error.log`
2. **Input validieren**: Prüfen Sie die Eingabedaten auf Probleme
3. **API-Status**: Überprüfen Sie den OpenAI API-Status
4. **Support kontaktieren**: Senden Sie die Log-Dateien an den Support

**F: Die Anwendung friert ein oder reagiert nicht.**

A: 
1. **Task-Manager**: Beenden Sie den Prozess und starten Sie neu
2. **Speicher prüfen**: Überprüfen Sie den verfügbaren Arbeitsspeicher
3. **Große Dateien**: Versuchen Sie kleinere Dateien
4. **Debug-Modus**: Aktivieren Sie Debug-Logging für mehr Informationen

## Fehlerbehebung

### Häufige Probleme und Lösungen

#### Problem: Anwendung startet nicht

**Symptome**:
- Fehlermeldung beim Start
- Schwarzer Bildschirm
- Sofortiger Absturz

**Diagnose-Schritte**:
```bash
# 1. Python-Version prüfen
python --version
# Sollte 3.12 oder höher sein

# 2. Virtuelle Umgebung prüfen
which python  # macOS/Linux
where python   # Windows

# 3. Abhängigkeiten prüfen
pip list | grep -E "(openai|tkinter|pandas)"

# 4. Setup-Validierung ausführen
python setup_validation.py
```

**Lösungsansätze**:
1. **Virtuelle Umgebung neu erstellen**:
   ```bash
   rm -rf .venv
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Abhängigkeiten manuell installieren**:
   ```bash
   pip install --upgrade pip
   pip install openai pandas matplotlib tkinter
   ```

3. **Systemabhängigkeiten prüfen**:
   - **Linux**: `sudo apt-get install python3-tk`
   - **macOS**: Tkinter sollte mit Python installiert sein
   - **Windows**: Python von python.org verwenden

#### Problem: API-Verbindungsfehler

**Symptome**:
- "API Key ungültig"
- "Verbindung fehlgeschlagen"
- "Rate Limit erreicht"

**Diagnose**:
```bash
# API-Key testen
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models

# Netzwerk-Konnektivität prüfen
ping api.openai.com
```

**Lösungen**:
1. **API-Key validieren**:
   - Auf OpenAI-Dashboard prüfen
   - Gültigkeit und Guthaben überprüfen
   - Neuen Key generieren falls nötig

2. **Netzwerk-Probleme**:
   - Firewall-Einstellungen prüfen
   - Proxy-Konfiguration anpassen
   - VPN deaktivieren (temporär)

3. **Rate-Limits**:
   - Warten und erneut versuchen
   - Kleinere Requests senden
   - API-Plan upgraden

#### Problem: OCR funktioniert nicht

**Symptome**:
- "Tesseract nicht gefunden"
- Leere OCR-Ergebnisse
- Schlechte Texterkennung

**Diagnose**:
```bash
# Tesseract-Installation prüfen
tesseract --version

# Sprach-Pakete prüfen
tesseract --list-langs
```

**Lösungen**:
1. **Tesseract installieren**:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr tesseract-ocr-deu
   
   # macOS
   brew install tesseract
   
   # Windows
   # Download von: https://github.com/UB-Mannheim/tesseract/wiki
   ```

2. **Pfad konfigurieren**:
   ```ini
   # config.ini
   [OCR]
   tesseract_path = /usr/bin/tesseract  # Linux/macOS
   tesseract_path = C:\Program Files\Tesseract-OCR\tesseract.exe  # Windows
   ```

3. **Bildqualität verbessern**:
   - Höhere Auflösung verwenden (min. 300 DPI)
   - Kontrast erhöhen
   - Schräge korrigieren
   - Rauschen reduzieren

#### Problem: Speicher-/Performance-Probleme

**Symptome**:
- Langsame Verarbeitung
- Hoher RAM-Verbrauch
- Anwendung friert ein

**Diagnose**:
```bash
# Speicherverbrauch überwachen
top -p $(pgrep -f "python.*main.py")

# Festplattenspeicher prüfen
df -h

# Log-Dateien auf Fehler prüfen
tail -f logs/performance.log
```

**Lösungen**:
1. **Speicher-Optimierung**:
   ```ini
   # config.ini
   [PERFORMANCE]
   chunk_size_mb = 5          # Kleinere Chunks
   max_workers = 2            # Weniger parallele Prozesse
   cache_size_mb = 100        # Kleinerer Cache
   ```

2. **Dateien optimieren**:
   - Große Dateien vor Upload komprimieren
   - Unnötige Inhalte entfernen
   - Mehrere kleine Dateien statt einer großen

3. **System-Ressourcen**:
   - Andere Anwendungen schließen
   - Mehr RAM installieren
   - SSD für bessere I/O-Performance

#### Problem: Datenextraktion ungenau

**Symptome**:
- Tabellen nicht erkannt
- Falsche Datentypen
- Fehlende numerische Werte

**Diagnose**:
1. **Input-Qualität prüfen**:
   - Ist die Struktur klar erkennbar?
   - Sind Spalten/Zeilen eindeutig getrennt?
   - Gibt es störende Formatierungen?

2. **Extraktions-Log analysieren**:
   ```bash
   grep "extraction" logs/application.log
   ```

**Lösungen**:
1. **Input-Verbesserung**:
   - Klarere Tabellenstruktur verwenden
   - Einheitliche Formatierung
   - Störende Elemente entfernen

2. **Manuelle Korrektur**:
   - Extraktions-Editor verwenden
   - Datentypen manuell zuweisen
   - Fehlende Werte ergänzen

3. **Alternative Formate**:
   - CSV statt Excel verwenden
   - Strukturierte Textformate
   - JSON-Export aus Originalquelle

### Erweiterte Diagnose-Tools

#### Debug-Modus aktivieren

```ini
# config.ini
[DEBUG]
enabled = true
log_level = DEBUG
verbose_output = true
performance_monitoring = true
```

#### Log-Dateien verstehen

**application.log**: Allgemeine Anwendungs-Events
```
2024-12-15 10:30:15 INFO: Analysis started for file: report.pdf
2024-12-15 10:30:20 DEBUG: Data extraction found 3 tables, 15 entities
2024-12-15 10:30:25 INFO: Analysis completed successfully
```

**error.log**: Fehler und Exceptions
```
2024-12-15 10:35:10 ERROR: OCR failed for image.png
Traceback (most recent call last):
  File "image_handler.py", line 45, in extract_text
    result = pytesseract.image_to_string(image)
TesseractNotFoundError: tesseract is not installed
```

**performance.log**: Performance-Metriken
```
2024-12-15 10:30:15 PERF: File processing took 2.3s
2024-12-15 10:30:20 PERF: Data extraction took 1.8s
2024-12-15 10:30:25 PERF: Total analysis time: 5.1s
```

#### System-Informationen sammeln

```bash
# System-Info-Script ausführen
python system_requirements_check.py > system_info.txt

# Inhalt prüfen
cat system_info.txt
```

**Beispiel-Output**:
```
System Information Report
========================
OS: macOS 14.2.1
Python: 3.12.1
Available RAM: 16 GB
Free Disk Space: 250 GB

Dependency Check:
✓ openai: 1.3.7
✓ pandas: 2.1.4
✓ matplotlib: 3.8.2
✗ tesseract: Not found
✓ tkinter: Available

Configuration:
✓ API Key: Configured
✓ Database: Accessible
✗ OCR: Tesseract missing
```

### Support-Anfrage vorbereiten

Wenn Sie Hilfe benötigen, sammeln Sie folgende Informationen:

1. **System-Informationen**:
   ```bash
   python system_requirements_check.py > system_info.txt
   ```

2. **Relevante Log-Dateien**:
   ```bash
   # Letzte 100 Zeilen der wichtigsten Logs
   tail -100 logs/error.log > error_excerpt.txt
   tail -100 logs/application.log > app_excerpt.txt
   ```

3. **Reproduktions-Schritte**:
   - Genaue Beschreibung des Problems
   - Schritte zur Reproduktion
   - Erwartetes vs. tatsächliches Verhalten
   - Screenshots (falls relevant)

4. **Konfiguration** (ohne sensitive Daten):
   ```bash
   # config.ini ohne API-Keys
   grep -v "api_key" config.ini > config_sanitized.ini
   ```

## Tipps und Best Practices

### Optimale Nutzung der Analyse-Features

#### Text-Vorbereitung
1. **Struktur verbessern**:
   - Klare Absätze verwenden
   - Überschriften hervorheben
   - Listen strukturiert formatieren

2. **Qualität sicherstellen**:
   - Rechtschreibung prüfen
   - Vollständige Sätze verwenden
   - Kontext bereitstellen

3. **Länge optimieren**:
   - **Zu kurz** (< 100 Wörter): Wenig Analysematerial
   - **Optimal** (500-5000 Wörter): Beste Ergebnisse
   - **Zu lang** (> 10000 Wörter): Wird automatisch aufgeteilt

#### Analysetyp-Auswahl
- **Zusammenfassung**: Für lange Texte und Berichte
- **Schlüsselwörter**: Für Themen-Identifikation
- **Sentiment**: Für Bewertungen und Feedback
- **Custom Prompts**: Für spezifische Fragestellungen

#### Custom Prompts effektiv nutzen
**Gute Prompts**:
```
"Identifiziere die 5 wichtigsten Risiken in diesem Geschäftsbericht 
und bewerte deren Wahrscheinlichkeit."

"Extrahiere alle Zahlen und Statistiken und erkläre deren Bedeutung 
im Kontext des Textes."

"Vergleiche die Argumente für und gegen die vorgeschlagene Strategie."
```

**Vermeiden Sie**:
```
"Analysiere das."  # Zu unspezifisch
"Was denkst du?"   # Zu subjektiv
"Mach was Cooles." # Keine klare Anweisung
```

### Datenextraktion optimieren

#### Excel-Dateien vorbereiten
1. **Struktur standardisieren**:
   - Erste Zeile als Spaltenüberschriften
   - Einheitliche Datentypen pro Spalte
   - Keine leeren Zeilen zwischen Daten

2. **Formatierung bereinigen**:
   - Zahlen als Zahlen formatieren (nicht als Text)
   - Datumsangaben einheitlich formatieren
   - Währungen mit einheitlichen Symbolen

3. **Mehrere Arbeitsblätter**:
   - Aussagekräftige Namen verwenden
   - Ähnliche Strukturen für verwandte Daten
   - Zusammenfassungs-Blatt erstellen

#### Bilder für OCR optimieren
1. **Technische Qualität**:
   - Mindestens 300 DPI Auflösung
   - Hoher Kontrast zwischen Text und Hintergrund
   - Gerade Ausrichtung (nicht schräg)

2. **Inhaltliche Vorbereitung**:
   - Störende Elemente entfernen
   - Text-Bereiche fokussieren
   - Mehrere Bilder für verschiedene Bereiche

3. **Format-Wahl**:
   - PNG für Screenshots
   - JPEG für Fotos (hohe Qualität)
   - PDF für mehrseitige Dokumente

### Visualisierung Best Practices

#### Diagrammtyp-Auswahl
- **Balkendiagramme**: Kategorien vergleichen
- **Liniendiagramme**: Trends über Zeit zeigen
- **Kreisdiagramme**: Anteile darstellen (max. 7 Kategorien)
- **Streudiagramme**: Korrelationen visualisieren
- **Histogramme**: Verteilungen analysieren

#### Design-Prinzipien
1. **Klarheit vor Schönheit**:
   - Einfache, lesbare Schriftarten
   - Ausreichend Kontrast
   - Nicht zu viele Farben

2. **Aussagekräftige Beschriftungen**:
   - Präzise Titel verwenden
   - Achsen klar benennen
   - Einheiten angeben

3. **Zielgruppen-gerecht**:
   - **Präsentationen**: Große Schrift, wenig Text
   - **Berichte**: Detaillierte Beschriftungen
   - **Dashboards**: Kompakte Darstellung

### Workflow-Optimierung

#### Batch-Processing nutzen
1. **Ähnliche Dateien gruppieren**:
   - Alle Quartalsberichte zusammen
   - Kundenfeedback nach Zeiträumen
   - Verschiedene Datenquellen zu einem Thema

2. **Standardisierte Prozesse**:
   - Gleiche Analysetypen für ähnliche Inhalte
   - Einheitliche Namenskonventionen
   - Template-basierte Exports

#### Ergebnis-Organisation
1. **Naming Conventions**:
   ```
   Format: [Projekt]_[Typ]_[Datum]
   Beispiele:
   - MarktAnalyse_Zusammenfassung_2024-12-15
   - KundenFeedback_Sentiment_Q4-2024
   - Literatur_Review_KI-Trends_Dez2024
   ```

2. **Tag-System entwickeln**:
   ```
   Kategorien: projekt, typ, zeitraum, quelle, status
   Beispiele:
   - projekt:marktforschung, typ:analyse, zeitraum:q4-2024
   - quelle:social-media, typ:sentiment, status:final
   ```

3. **Ordner-Struktur**:
   ```
   exports/
   ├── 2024/
   │   ├── Q4/
   │   │   ├── marktanalyse/
   │   │   └── kundenfeedback/
   │   └── Q3/
   └── templates/
   ```

### Performance-Optimierung

#### Große Dateien handhaben
1. **Vor-Verarbeitung**:
   - Unnötige Inhalte entfernen
   - Komprimierung nutzen
   - Relevante Abschnitte extrahieren

2. **Chunk-Strategien**:
   ```ini
   # Für verschiedene Dateitypen optimieren
   [PERFORMANCE]
   text_chunk_size = 5000      # Wörter
   excel_chunk_rows = 1000     # Zeilen
   image_max_size_mb = 10      # MB
   ```

3. **Parallel-Processing**:
   - Mehrere kleine Dateien gleichzeitig
   - Unabhängige Analysen parallelisieren
   - System-Ressourcen optimal nutzen

#### Cache effektiv nutzen
1. **Cache-Strategien**:
   - Häufig verwendete Analysen cachen
   - Zwischenergebnisse speichern
   - Redundante API-Calls vermeiden

2. **Cache-Verwaltung**:
   ```bash
   # Cache-Status prüfen
   du -sh cache/
   
   # Cache leeren bei Problemen
   rm -rf cache/*
   ```

### Qualitätssicherung

#### Ergebnisse validieren
1. **Plausibilitätsprüfung**:
   - Stimmen extrahierte Zahlen?
   - Sind Entitäten korrekt erkannt?
   - Macht die Zusammenfassung Sinn?

2. **Stichproben-Kontrolle**:
   - 10% der Ergebnisse manuell prüfen
   - Kritische Analysen doppelt validieren
   - Feedback-Loop für Verbesserungen

#### Dokumentation pflegen
1. **Analyse-Protokoll**:
   - Ziel der Analyse dokumentieren
   - Verwendete Parameter notieren
   - Besonderheiten und Anpassungen festhalten

2. **Lessons Learned**:
   - Was funktioniert gut?
   - Welche Probleme traten auf?
   - Wie können Prozesse verbessert werden?

Diese umfassende Anleitung hilft Ihnen dabei, das KI Analysetool optimal zu nutzen und häufige Probleme zu vermeiden. Bei weiteren Fragen konsultieren Sie die technische Dokumentation oder kontaktieren Sie den Support.