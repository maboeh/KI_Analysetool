# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projektbeschreibung

KI-Analysetool — eine Python/tkinter-Desktop-Anwendung zur KI-gestützten Inhaltsanalyse. Nutzer können Webseiten, YouTube-Videos und PDF-Dateien analysieren lassen. Die Analyse erfolgt über die OpenAI API (GPT-4o).

## Ausführung

```bash
# Virtualenv aktivieren
source .venv/bin/activate

# App starten
python main.py
```

Es gibt kein `requirements.txt` oder `pyproject.toml`. Dependencies sind im `.venv` (Python 3.12) installiert. Wichtige Pakete: `openai`, `youtube-transcript-api`, `beautifulsoup4`, `requests`, `reportlab`, `PyPDF2`, `pytesseract`, `pdf2image`, `pandas`, `matplotlib`, `seaborn`, `pytest`, `pytest-cov`.

## Architektur

Die App folgt einer einfachen Schichtenarchitektur mit 5 Dateien:

- **`main.py`** — Einstiegspunkt, erstellt tkinter-Fenster und startet `Gui`
- **`Gui.py`** — Gesamte UI-Logik (tkinter). Tabs für Webseite/YouTube/PDF-Eingabe, Prompt-Auswahl (Zusammenfassung, Keywords, Sentiment, Themen oder freier Prompt), Ergebnisanzeige mit Markdown-Rendering, PDF-Export via reportlab
- **`analysis.py`** — Inhaltsextraktion und OpenAI-Aufrufe:
  - `text_extraction_youtube_website()` — Routing: YouTube → Transkript-API, HTTP-URL → BeautifulSoup, sonst Datei lesen
  - `real_ai_analyse_fortext()` — OpenAI Chat Completions für Textanalyse
  - `real_ai_analyse_forpdf()` — OpenAI Assistants API mit file_search für direkte PDF-Analyse
- **`config.py`** — API-Key-Verwaltung: Liest aus `config.ini` oder Umgebungsvariable `OPENAI_API_KEY`, speichert in `config.ini` mit eingeschränkten Dateiberechtigungen (0o600)
- **`markdown_formatter.py`** — Einfacher Markdown→tkinter-Text-Renderer (Headings, Bold, Code-Blöcke, Blockquotes)

### Datenfluss

```
Nutzer-Eingabe (URL/Datei) → start_analyse() → text_extraction/pdf_path
                           → get_prompt() → vorgefertigter oder freier Prompt
                           → real_ai_analyse_fortext() oder real_ai_analyse_forpdf()
                           → markdown_to_tkinter_text() → Anzeige
```

Wichtig: Bei PDFs wird der **Dateipfad** direkt an die Assistants API übergeben (Upload + file_search), bei Text wird der extrahierte Inhalt in den Prompt eingebettet.

## Sprache

UI und Kommentare sind auf Deutsch. Kommunikation mit dem Nutzer auf Deutsch.

## Bekannte TODOs im Code

- `analysis.py:35` — Flow für Text vs. PDF Extraktion muss überarbeitet werden
- `markdown_formatter.py:21` — Inline-Formatierung (italic, links) unvollständig
