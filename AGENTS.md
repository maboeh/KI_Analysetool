# AGENTS.md — KI Analysetool

## Build & Run
- **Starten:** `.venv/bin/python main.py` (oder `python main.py` mit aktiviertem venv)
- **Python:** 3.12+ (getestet mit 3.14)
- **venv:** `.venv/` liegt im Projekt; `source .venv/bin/activate`
- **Abhängigkeiten:** `pip install -r requirements.txt`; optional `tesseract` für OCR

## Verification
- **Syntax-Check aller Module:** `.venv/bin/python -m py_compile *.py`
- **Smoke-Tests (ohne pytest):** Siehe Verification-Sektion unten
- **pytest ist NICHT im venv installiert** — Tests manuell via `python -c` oder `python test_<modul>.py` laufen lassen
- **Zentraler Testlauf:** `.venv/bin/python run_tests.py --group all` (`unit`, `gui`, `integration` oder `all`; Timeout pro Datei mit `--timeout`)
- **GUI-Instanziierung testen:** `.venv/bin/python -c "import tkinter as tk; from enhanced_gui_integration_final import EnhancedGui; w=tk.Tk(); w.withdraw(); app=EnhancedGui(w); print('OK'); w.destroy()"`
- **Wichtige Tests:**
  - `PYTHONPATH=$(pwd) .venv/bin/python tests/test_security.py`
  - `PYTHONPATH=$(pwd) .venv/bin/python tests/test_analysis.py`
  - `PYTHONPATH=$(pwd) .venv/bin/python tests/test_critical_fixes.py`
  - `PYTHONPATH=$(pwd) .venv/bin/python test_data_models.py`
  - `PYTHONPATH=$(pwd) .venv/bin/python test_basic_integration.py`

## Architektur
- **Einstieg:** `main.py` → `enhanced_gui_integration_final.EnhancedGui` (erbt von `Gui`)
- **Basis-GUI:** `Gui.py` — Tabs Webseite/YouTube/PDF, Prompt-Eingabe, Output
- **Enhanced-GUI:** `enhanced_gui_integration_final.py` — erweitert um Excel/Bild/CSV/Multi/Text-Tabs, Ergebnisse, Visualisierung, Export, Browser, Backup, Tags, PDF-Report
- **Input-Tabs:** `extended_input_tabs.py` — fügt Tabs in bestehendes Notebook ein (Original-Tabs bleiben erhalten)
- **Analyse:** `analysis.py` — OpenAI-Calls, YouTube/Website-Extraktion, Token/Cost-Tracking
- **Config:** `config.py` — API-Key via Keyring/Env/config.ini (Key-Name: `openai_key`, Fallbacks für alte Namen)
- **Ergebnisse:** `results_manager.py` (SQLite+JSON, Ergebnisversionen), `results_browser.py`, `results_display.py`, `results_processor.py`
- **Schema:** `migrations.py` (versionierte SQLite-Migrationen, `schema_migrations`-Tabelle)
- **Projekte/Rezepte:** `projects.py` (Project CRUD + Ergebnis-Zuordnung), `recipes.py` (Rezept CRUD), `workspace_ui.py` (Dialoge für Projekte, Rezepte, Editieren, Versionen, Batch)
- **Batch:** `batch_queue.py` (persistente Jobs/Items, Pause/Resume/Cancel, begrenzte Parallelität, Retry nur für retryable Fehler, Privacy-Skip)
- **Folgeaktionen:** `follow_up_actions.py` (FollowUpActionSystem mit History), `action_buttons.py`
- **Export:** `excel_exporter.py`, `excel_export_ui.py`, `pdf_report_generator.py`
- **Visualisierung:** `visualization_panel.py`, `chart_generator.py`
- **Daten:** `data_models.py` (Single-Source für ActionType/ChartType Enums), `data_extractor.py`, `data_categorizer.py`
- **Sicherheit:** `security.py` (SSRF-Schutz mit DNS-Auflösung + Path-Validator + redirect-safe requests), `analysis.is_safe_url` nutzt beides
- **Backup:** `backup_manager.py` (ZIP aus results.db + results/ + manifest.json; Restore validiert Integrität/Zip-Slip und legt vorher ein Sicherungs-Backup an)
- **Datenschutz:** `privacy_scanner.py` (lokaler PII-/Secret-Scan + Redaction) und `transfer_confirmation.py` (kombinierte Bestätigung vor Provider-Transfer: Hinweis + Funde + Kostenschätzung + Budget)
- **Batch-Queue:** `batch_queue.py` (persistente Jobs/Items, Pause/Resume/Cancel, 1–4 Worker, Retry nur bei retryable Fehlern, PII-Skip)
- **Quellenbelege:** `evidence.py` (Zitat-/Referenz-Extraktion + Validierung gegen Quelltext; nur wörtliche Treffer sind „verified")
- **Smart Charts:** `column_analysis.py` (Spaltenrollen numeric/date/categorical/text, Fehlwert-Handling, begründete Diagrammvorschläge)
- **Workspace-UI:** `workspace_ui.py` (Projekte, Rezepte, Ergebnis-Editor, Versionen, Batch, Evidence, Daten-Editor, Chart-Vorschläge, Prompt-Playground)
- **Lernpfad:** `learning_path.py` (geführte Schritte vom Anfänger zum Experten)
- **Benutzerprofil:** `user_profile.py` (Erfahrungsgrad, Onboarding-Status, Fortschritt)
- **Prompt-Bibliothek:** `prompt_library.py` (wiederverwendbare Vorlagen mit Erklärungen)
- **Tutorial-Overlay:** `tutorial_overlay.py` (Schritt-für-Schritt-Hervorhebungen)
- **Hilfe:** `help_tooltip.py` (?-Indikatoren + Help-Fenster); zentrale Dokumentation in `HELP.md`

## Wichtige Konventionen
- **ActionType-Enum:** Single-Source in `data_models.py`; `action_buttons.py` importiert es + Aliase für alte deutsche Namen
- **Tab-Identifikation:** Per Referenz (`self.tab_frames` bzw. `self._tab_identifiers`), nicht per Index
- **Hilfe-Indikatoren:** `add_help_indicator(parent_frame, "Hilfetext")` aus `help_tooltip.py` (singleton-style Tooltip-Manager)
- **API-Key-Namen:** `openai_key` (Standard), Fallbacks `OpenAI_Key`/`openai_api_key` in `config.py`
- **Logging:** File-Handler nach `logs/application.log` (in `main.py` konfiguriert); Secrets werden durch `SecretFilter` maskiert

## Bekannte Limitierungen
- Drag & Drop ist optional (via `tkinterdnd2`); ohne die Bibliothek bleibt der `filedialog`-Fallback aktiv
- HEATMAP-Chart-Typ wurde aus dem Enum entfernt (war nicht implementiert)
- `data_categorizer.py` ist implementiert aber nur minimal in `results_processor` integriert
