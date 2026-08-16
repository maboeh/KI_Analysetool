# KI Analysetool - Enhanced Results Processing

Ein umfassendes Desktop-Tool zur KI-gestützten Analyse verschiedener Inhaltsquellen mit erweiterten Datenverarbeitungs- und Visualisierungsfunktionen.

## Überblick

Das KI Analysetool ist eine Desktop-Anwendung, die es Benutzern ermöglicht, Inhalte aus verschiedenen Quellen mit OpenAI's GPT-Modellen zu analysieren. Die Anwendung wurde von einem einfachen Analyse-Tool zu einer umfassenden Datenverarbeitungs- und Visualisierungsplattform erweitert.

### Zielgruppe

Deutschsprachige Benutzer, die schnell Erkenntnisse aus verschiedenen Inhaltsquellen extrahieren und diese visuell aufbereiten möchten:
- Forscher und Analysten
- Content-Manager und Redakteure
- Datenanalysten und Business Intelligence Professionals
- Studenten und Akademiker

## Hauptfunktionen

### 📊 Erweiterte Ergebnisdarstellung
- **Strukturierte Formatierung**: Überschriften, Aufzählungen und Hervorhebungen
- **Syntax-Highlighting**: Verschiedene Textformatierungen für bessere Lesbarkeit
- **Interaktive Navigation**: Benutzerfreundliche Scroll- und Zoom-Funktionalität
- **Responsive Layout**: Anpassung an verschiedene Inhaltstypen

### 🔄 Interaktive Weiterverarbeitung
- **Folgeaktionen**: Zusammenfassen, Vertiefen, Übersetzen von Ergebnissen
- **Analyse-Historie**: Nachverfolgung und Navigation durch Analyseschritte
- **Kontextuelle Aktionen**: Intelligente Vorschläge basierend auf Ergebnistyp
- **Iterative Vertiefung**: Aufbau auf vorherigen Analyseergebnissen

### 📈 Automatische Datenextraktion und -visualisierung
- **Strukturierte Datenextraktion**: Automatische Erkennung von Tabellen, Listen und numerischen Daten
- **Entitätserkennung**: Personen, Orte, Organisationen, Daten und Währungen
- **Excel-Export**: Strukturierte .xlsx-Dateien mit korrekter Formatierung
- **Automatische Diagrammerstellung**: Balken-, Linien-, Kreis- und Streudiagramme
- **Interaktive Visualisierungen**: Zoom, Pan und Export-Funktionen

### 📁 Erweiterte Input-Formate
- **Excel-Dateien**: .xlsx und .xls mit Tabellenvorschau
- **Bildverarbeitung**: PNG, JPG, PDF mit OCR-Texterkennung
- **CSV-Import**: Automatische Delimiter-Erkennung und Spalten-Mapping
- **Multi-File-Processing**: Gleichzeitige Verarbeitung mehrerer Dateien
- **Drag & Drop**: Intuitive Datei-Upload-Funktionalität

### 💾 Ergebnis-Management
- **Lokale Speicherung**: Sichere Aufbewahrung aller Analyseergebnisse
- **Durchsuchbare Historie**: Filterung nach Datum, Quelle und Analysetyp
- **Metadaten-Verwaltung**: Automatische Erfassung von Kontext und Zeitstempel
- **Export-Optionen**: PDF, Excel, PNG für verschiedene Verwendungszwecke
- **Ergebnis-Vergleich**: Kombinierung und Gegenüberstellung mehrerer Analysen

## Installation

### Systemanforderungen

- **Betriebssystem**: Windows 10/11, macOS 10.15+, oder Linux (Ubuntu 20.04+)
- **Python**: Version 3.12 oder höher
- **RAM**: Mindestens 4 GB (8 GB empfohlen für große Dateien)
- **Speicherplatz**: 2 GB für Installation und Abhängigkeiten
- **Internetverbindung**: Für OpenAI API-Zugriff erforderlich

### Externe Abhängigkeiten

#### Tesseract OCR (für Bildverarbeitung)

**Windows:**
```bash
# Mit Chocolatey
choco install tesseract

# Oder Download von: https://github.com/UB-Mannheim/tesseract/wiki
```

**macOS:**
```bash
# Mit Homebrew
brew install tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-deu
```

### Python-Installation

1. **Repository klonen:**
```bash
git clone <repository-url>
cd ki-analysetool
```

2. **Virtuelle Umgebung erstellen:**
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

3. **Abhängigkeiten installieren:**
```bash
pip install -r requirements.txt
```

4. **Setup-Validierung ausführen:**
```bash
python setup_validation.py
```

### Manuelle Abhängigkeiten-Installation

Falls `requirements.txt` nicht verfügbar ist:

```bash
# Core-Abhängigkeiten
pip install openai youtube-transcript-api beautifulsoup4 requests reportlab

# Erweiterte Funktionen
pip install pandas openpyxl pytesseract Pillow matplotlib seaborn plotly spacy python-dateutil

# NLP-Modell für deutsche Texte
python -m spacy download de_core_news_sm
```

## Konfiguration

### API-Schlüssel einrichten

1. **OpenAI API-Schlüssel erhalten:**
   - Registrierung bei [OpenAI](https://platform.openai.com/)
   - API-Schlüssel im Dashboard generieren

2. **Konfigurationsdatei erstellen:**
```bash
cp config.ini.example config.ini
```

3. **config.ini bearbeiten:**
```ini
[API]
openai_api_key = sk-your-api-key-here
model = gpt-4o
max_tokens = 4000
temperature = 0.7

[ANALYSIS]
default_language = de
enable_auto_export = true
max_file_size_mb = 100

[VISUALIZATION]
default_chart_style = seaborn
export_dpi = 300
interactive_charts = true

[OCR]
tesseract_path = /usr/bin/tesseract  # Anpassen je nach System
ocr_language = deu
preprocessing_enabled = true
```

### Umgebungsvariablen (Alternative)

```bash
# Windows
set OPENAI_API_KEY=sk-your-api-key-here

# macOS/Linux
export OPENAI_API_KEY=sk-your-api-key-here
```

### Erweiterte Konfigurationsoptionen

#### Datenbank-Einstellungen
```ini
[DATABASE]
results_db_path = ./results.db
backup_enabled = true
backup_interval_days = 7
max_results_stored = 1000
```

#### Performance-Optimierung
```ini
[PERFORMANCE]
chunk_size_mb = 10
parallel_processing = true
max_workers = 4
cache_enabled = true
cache_size_mb = 500
```

#### Sicherheitseinstellungen
```ini
[SECURITY]
encrypt_stored_results = true
api_timeout_seconds = 30
max_retries = 3
rate_limit_requests_per_minute = 60
```

## Schnellstart

1. **Anwendung starten:**
```bash
python main.py
```

2. **Erste Analyse durchführen:**
   - Text in das Eingabefeld eingeben oder Datei hochladen
   - Analysetyp auswählen (Zusammenfassung, Schlüsselwörter, etc.)
   - "Analysieren" klicken

3. **Ergebnisse erkunden:**
   - Strukturierte Darstellung der Analyseergebnisse
   - Folgeaktionen über die Aktions-Buttons ausführen
   - Daten extrahieren und als Excel exportieren
   - Visualisierungen erstellen und anpassen

## Verwendung

### Grundlegende Analyse-Workflows

#### Text-Analyse
1. Text direkt eingeben oder aus Zwischenablage einfügen
2. Analysetyp wählen oder benutzerdefinierten Prompt eingeben
3. Analyse starten und Ergebnisse in strukturierter Form erhalten
4. Folgeaktionen wie Zusammenfassung oder Vertiefung ausführen

#### Datei-Upload und -Verarbeitung
1. Dateien per Drag & Drop oder Datei-Dialog hochladen
2. Vorschau der extrahierten Inhalte prüfen
3. Analyse-Parameter anpassen
4. Verarbeitung starten und Ergebnisse erhalten

#### Datenextraktion und -export
1. Nach der Analyse automatisch erkannte Daten prüfen
2. Datentypen und Kategorien validieren
3. Excel-Export mit strukturierten Tabellen erstellen
4. Visualisierungen basierend auf numerischen Daten generieren

### Erweiterte Funktionen

#### Multi-File-Analyse
```python
# Beispiel für kombinierte Dateiverarbeitung
files = ["report1.xlsx", "data.csv", "summary.pdf"]
# Alle Dateien werden kombiniert analysiert
```

#### Benutzerdefinierte Visualisierungen
- Diagrammtyp basierend auf Datencharakteristika auswählen
- Farben, Stile und Beschriftungen anpassen
- Interaktive Features aktivieren
- Export in verschiedenen Formaten (PNG, PDF, SVG)

#### Ergebnis-Management
- Analysen mit aussagekräftigen Namen speichern
- Tags und Kategorien für bessere Organisation
- Suchfunktion für schnelles Wiederfinden
- Batch-Export mehrerer Ergebnisse

## Fehlerbehebung

### Häufige Probleme

#### Installation und Setup

**Problem**: `ModuleNotFoundError` beim Start
```bash
# Lösung: Virtuelle Umgebung aktivieren und Abhängigkeiten installieren
source .venv/bin/activate  # oder .venv\Scripts\activate auf Windows
pip install -r requirements.txt
```

**Problem**: Tesseract OCR nicht gefunden
```bash
# Windows: Pfad in config.ini anpassen
tesseract_path = C:\Program Files\Tesseract-OCR\tesseract.exe

# macOS/Linux: Installation prüfen
which tesseract
```

#### API und Netzwerk

**Problem**: OpenAI API-Fehler
- API-Schlüssel in config.ini prüfen
- Internetverbindung testen
- API-Limits und Guthaben überprüfen

**Problem**: Langsame Verarbeitung großer Dateien
- Datei-Chunk-Größe in config.ini reduzieren
- Parallel-Processing deaktivieren bei Speicherproblemen
- Temporäre Dateien regelmäßig löschen

#### Datenverarbeitung

**Problem**: OCR-Qualität schlecht
- Bildauflösung und -qualität verbessern
- OCR-Preprocessing in config.ini aktivieren
- Alternative OCR-Sprache testen

**Problem**: Excel-Export fehlerhaft
- Pandas und openpyxl Versionen aktualisieren
- Datentypen vor Export validieren
- Große Datasets in kleinere Chunks aufteilen

### Logs und Debugging

**Log-Dateien finden:**
```bash
# Standard-Log-Verzeichnis
./logs/application.log
./logs/error.log
./logs/performance.log
```

**Debug-Modus aktivieren:**
```ini
[DEBUG]
enabled = true
log_level = DEBUG
verbose_output = true
```

**Performance-Monitoring:**
```bash
# Memory-Usage prüfen
python -m memory_profiler main.py

# Profiling aktivieren
python -m cProfile -o profile.stats main.py
```

## Support und Community

### Dokumentation
- **Technische Dokumentation**: Siehe `docs/` Verzeichnis
- **API-Referenz**: Inline-Dokumentation in den Python-Modulen
- **Beispiele**: `examples/` Verzeichnis mit Anwendungsfällen

### Hilfe erhalten
- **Issues**: GitHub Issues für Bug-Reports und Feature-Requests
- **Diskussionen**: GitHub Discussions für allgemeine Fragen
- **Wiki**: Erweiterte Tutorials und Best Practices

### Beitragen
- **Code-Beiträge**: Pull Requests willkommen
- **Dokumentation**: Verbesserungen und Übersetzungen
- **Testing**: Bug-Reports und Qualitätssicherung
- **Feedback**: Usability-Tests und Feature-Vorschläge

## Lizenz

[Lizenz-Information hier einfügen]

## Changelog

### Version 2.0.0 (Enhanced Results Processing)
- ✨ Erweiterte Ergebnisdarstellung mit Syntax-Highlighting
- 🔄 Interaktive Folgeaktionen und Analyse-Historie
- 📊 Automatische Datenextraktion und Excel-Export
- 📈 Integrierte Visualisierungs-Engine mit verschiedenen Diagrammtypen
- 📁 Unterstützung für Excel, CSV und Bild-Dateien mit OCR
- 💾 Umfassendes Ergebnis-Management mit lokaler Speicherung
- 🎨 Verbesserte Benutzeroberfläche mit erweiterten Input-Tabs
- ⚡ Performance-Optimierungen für große Dateien
- 🛡️ Erweiterte Fehlerbehandlung und Benutzer-Feedback
- 📚 Umfassende Dokumentation und Setup-Validierung

### Version 1.0.0 (Basis-Version)
- 📝 Grundlegende Text-Analyse mit OpenAI GPT
- 🌐 YouTube und Website-Content-Extraktion
- 📄 PDF-Verarbeitung und -Analyse
- 🇩🇪 Deutsche Benutzeroberfläche
- 📋 Basis-Export-Funktionen (PDF, Zwischenablage)