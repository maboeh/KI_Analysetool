# Design Document: Enhanced Results Processing

## Overview

Diese Erweiterung transformiert die bestehende KI Analysetool-App von einem einfachen Text-in-Text-Analyse-Tool zu einer umfassenden Datenverarbeitungs- und Visualisierungsplattform. Das Design erweitert die bestehende Tkinter-basierte Architektur um neue Module für Datenextraktion, Visualisierung, erweiterte Input-Formate und interaktive Ergebnisverarbeitung.

## Architecture

### Bestehende Architektur (Basis)
```
main.py (Entry Point)
├── Gui.py (UI Layer)
├── analysis.py (Business Logic)
├── config.py (Configuration)
└── markdown_formatter.py (Text Formatting)
```

### Erweiterte Architektur
```
main.py (Entry Point)
├── Gui.py (Enhanced UI Layer)
├── analysis.py (Enhanced Analysis)
├── results_processor.py (NEW - Results Processing)
├── data_extractor.py (NEW - Data Extraction)
├── visualization.py (NEW - Chart Generation)
├── file_handlers.py (NEW - Extended File Support)
├── results_manager.py (NEW - Results Storage)
├── config.py (Configuration)
└── markdown_formatter.py (Enhanced Text Formatting)
```

## Components and Interfaces

### 1. Enhanced GUI Layer (Gui.py Erweiterungen)

#### ResultsDisplayWidget
- **Zweck**: Erweiterte Anzeige von Analyseergebnissen mit verbesserter Formatierung
- **Funktionen**:
  - Strukturierte Textdarstellung mit Syntax-Highlighting
  - Interaktive Buttons für Folgeaktionen
  - Tabbed Interface für verschiedene Ergebnisansichten
  - Scroll- und Zoom-Funktionalität

#### ActionButtonsFrame
- **Zweck**: Interaktive Buttons für Folgeaktionen auf Ergebnisse
- **Funktionen**:
  - Zusammenfassen, Vertiefen, Übersetzen, Analysieren
  - Dynamische Button-Generierung basierend auf Ergebnistyp
  - Kontextmenü für erweiterte Aktionen

#### DataVisualizationPanel
- **Zweck**: Anzeige von Diagrammen und Visualisierungen
- **Funktionen**:
  - Matplotlib-Integration in Tkinter
  - Interaktive Diagramme mit Zoom/Pan
  - Export-Funktionen für Grafiken

#### ExtendedInputTabs
- **Zweck**: Erweiterte Input-Tabs für neue Dateiformate
- **Funktionen**:
  - Excel-Upload-Tab mit Vorschau
  - Bild-Upload-Tab mit OCR-Vorschau
  - Multi-File-Upload mit Drag&Drop
  - CSV-Import mit Spalten-Mapping

### 2. Results Processor (results_processor.py)

#### ResultsProcessor Klasse
```python
class ResultsProcessor:
    def __init__(self):
        self.history = []
        self.current_result = None
    
    def process_result(self, raw_result: str) -> ProcessedResult
    def add_follow_up_action(self, action_type: str, context: str) -> str
    def get_action_suggestions(self, result_content: str) -> List[str]
    def format_result_display(self, result: ProcessedResult) -> FormattedResult
```

#### ProcessedResult Datenklasse
```python
@dataclass
class ProcessedResult:
    content: str
    extracted_data: Dict
    suggested_actions: List[str]
    visualization_options: List[str]
    metadata: Dict
    timestamp: datetime
```

### 3. Data Extractor (data_extractor.py)

#### DataExtractor Klasse
```python
class DataExtractor:
    def extract_structured_data(self, text: str) -> StructuredData
    def extract_entities(self, text: str) -> List[Entity]
    def extract_numerical_data(self, text: str) -> List[NumericValue]
    def extract_tables(self, text: str) -> List[Table]
    def extract_dates(self, text: str) -> List[DateValue]
```

#### StructuredData Datenklasse
```python
@dataclass
class StructuredData:
    tables: List[Table]
    entities: List[Entity]
    numeric_values: List[NumericValue]
    dates: List[DateValue]
    categories: Dict[str, List[str]]
```

### 4. Visualization Engine (visualization.py)

#### ChartGenerator Klasse
```python
class ChartGenerator:
    def suggest_chart_types(self, data: StructuredData) -> List[ChartType]
    def create_chart(self, data: StructuredData, chart_type: ChartType) -> Chart
    def export_chart(self, chart: Chart, format: str, path: str) -> bool
    def get_interactive_chart(self, chart: Chart) -> InteractiveChart
```

#### Unterstützte Diagrammtypen
- Balkendiagramme (horizontal/vertikal)
- Liniendiagramme (einfach/mehrfach)
- Kreisdiagramme
- Streudiagramme
- Histogramme
- Heatmaps (für Korrelationsdaten)

### 5. Extended File Handlers (file_handlers.py)

#### FileHandler Basis-Klasse
```python
class FileHandler:
    def can_handle(self, file_path: str) -> bool
    def extract_content(self, file_path: str) -> ExtractedContent
    def get_preview(self, file_path: str) -> str
```

#### Spezifische Handler
- **ExcelHandler**: .xlsx, .xls Dateien mit pandas
- **ImageHandler**: PNG, JPG, PDF mit OCR (pytesseract)
- **CSVHandler**: CSV-Dateien mit automatischer Delimiter-Erkennung
- **MultiFileHandler**: Kombinierte Verarbeitung mehrerer Dateien

### 6. Results Manager (results_manager.py)

#### ResultsManager Klasse
```python
class ResultsManager:
    def save_result(self, result: ProcessedResult, name: str) -> str
    def load_result(self, result_id: str) -> ProcessedResult
    def list_results(self, filter_criteria: Dict) -> List[ResultSummary]
    def delete_result(self, result_id: str) -> bool
    def export_result(self, result_id: str, format: str) -> str
```

#### Speicherformat
- SQLite-Datenbank für Metadaten
- JSON-Dateien für Ergebnisinhalte
- Separate Ordner für Visualisierungen und Exports

## Data Models

### ProcessedResult
```python
@dataclass
class ProcessedResult:
    id: str
    content: str
    source_info: SourceInfo
    extracted_data: StructuredData
    visualizations: List[Visualization]
    follow_up_actions: List[Action]
    metadata: ResultMetadata
    created_at: datetime
    updated_at: datetime
```

### StructuredData
```python
@dataclass
class StructuredData:
    tables: List[DataTable]
    entities: List[NamedEntity]
    numeric_values: List[NumericValue]
    temporal_data: List[TemporalValue]
    relationships: List[DataRelationship]
```

### Visualization
```python
@dataclass
class Visualization:
    id: str
    type: ChartType
    data_source: str
    config: ChartConfig
    file_path: str
    interactive: bool
```

### Action
```python
@dataclass
class Action:
    type: ActionType
    label: str
    description: str
    parameters: Dict
    enabled: bool
```

## Error Handling

### Hierarchische Fehlerbehandlung
1. **UI-Ebene**: Benutzerfreundliche Fehlermeldungen mit Lösungsvorschlägen
2. **Service-Ebene**: Detaillierte Logging und Fallback-Mechanismen
3. **Data-Ebene**: Validierung und Sanitization von Eingabedaten

### Spezifische Fehlerszenarien
- **Dateiformat nicht unterstützt**: Klare Meldung mit unterstützten Formaten
- **OCR-Fehler**: Fallback auf manuelle Texteingabe
- **API-Limits erreicht**: Warteschlange und Retry-Mechanismus
- **Speicher-/Performance-Probleme**: Chunking großer Dateien
- **Netzwerkfehler**: Offline-Modus für bereits geladene Daten

## Testing Strategy

### Unit Tests
- **DataExtractor**: Tests für verschiedene Textformate und Datentypen
- **ChartGenerator**: Tests für alle Diagrammtypen mit Mock-Daten
- **FileHandlers**: Tests für alle unterstützten Dateiformate
- **ResultsProcessor**: Tests für Aktionslogik und Formatierung

### Integration Tests
- **End-to-End Workflows**: Vollständige Analyse-Pipelines
- **UI-Integration**: Automatisierte GUI-Tests mit tkinter
- **File Processing**: Tests mit realen Dateien verschiedener Formate
- **API-Integration**: Tests mit OpenAI API (mit Mocking)

### Performance Tests
- **Große Dateien**: Tests mit Excel-Dateien >100MB
- **Viele Ergebnisse**: Skalierbarkeit der Ergebnisverwaltung
- **Visualisierung**: Performance bei komplexen Diagrammen
- **Memory Usage**: Speicherverbrauch bei verschiedenen Operationen

## Implementation Phases

### Phase 1: Core Infrastructure
- Erweiterte Datenmodelle
- Basis-Datenextraktion
- Erweiterte GUI-Komponenten

### Phase 2: File Processing
- Excel/CSV-Handler
- OCR-Integration für Bilder
- Multi-File-Processing

### Phase 3: Visualization
- Chart-Generation
- Interactive Visualizations
- Export-Funktionalität

### Phase 4: Advanced Features
- Results Management
- Follow-up Actions
- Performance Optimizations

## Technical Dependencies

### Neue Abhängigkeiten
```python
# Data Processing
pandas>=2.0.0          # Excel/CSV handling
openpyxl>=3.1.0        # Excel file support
pytesseract>=0.3.10    # OCR for images
Pillow>=10.0.0         # Image processing

# Visualization
matplotlib>=3.7.0      # Chart generation
seaborn>=0.12.0        # Statistical visualizations
plotly>=5.15.0         # Interactive charts

# Data Extraction
spacy>=3.6.0           # NLP for entity extraction
dateutil>=2.8.0        # Date parsing
regex>=2023.6.3        # Advanced text patterns

# Database
sqlite3                # Built-in (Results storage)
```

### Bestehende Abhängigkeiten (erweitert)
- tkinter (erweiterte Widgets)
- openai (bestehend)
- requests (bestehend)
- beautifulsoup4 (bestehend)
- reportlab (erweitert für Charts)

## Security Considerations

### Datenschutz
- Lokale Speicherung aller Ergebnisse (keine Cloud-Übertragung)
- Verschlüsselung sensibler Daten in der lokalen Datenbank
- Sichere API-Key-Verwaltung

### Input Validation
- Dateigröße-Limits für Uploads
- Malware-Scanning für hochgeladene Dateien
- Sanitization von extrahierten Daten

### Performance Security
- Rate-Limiting für API-Calls
- Memory-Limits für große Dateien
- Timeout-Mechanismen für lange Operationen