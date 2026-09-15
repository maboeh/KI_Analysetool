"""
Final enhanced GUI integration that combines all new components with the existing GUI.

This module provides a complete integration of the enhanced results processing
system with the existing KI Analysetool GUI, maintaining backward compatibility
while adding new features.
"""

import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext, messagebox
import os
import threading
import logging
import queue
from datetime import datetime
from typing import Optional, List, Dict, Any

# Import existing components
from Gui import Gui as BaseGui
from analysis import (AnalysisFailure, AVAILABLE_MODELS, analyze_text,
                     extract_transkript, extract_text_from_website,
                     text_extraction_youtube_website,
                     real_ai_analyse_fortext, real_ai_analyse_forpdf,
                     get_usage_stats, reset_usage_stats)
from config import check_api_key_exists, save_api_key, get_api_key
from markdown_formatter import configure_markdown_tags, markdown_to_tkinter_text
from user_profile import UserProfileManager
from learning_events import LearningEvent, LearningEventType
from learning_path import LearningPath
from prompt_library import PromptLibrary
from tutorial_overlay import TutorialOverlay

# Import enhanced components with error handling
try:
    from results_processor import ResultsProcessor
    from results_manager import ResultsManager
    from file_handler_router import FileHandlerRouter
    from extended_input_tabs import ExtendedInputTabs
    from results_display import ResultsDisplayWidget
    from action_buttons import ActionButtonsFrame
    from visualization_panel import DataVisualizationPanel
    from excel_export_ui import ExcelExportUI
    from results_browser import ResultsBrowser
    from progress_indicator import ProgressIndicator
    from error_handler import ErrorHandler
    from data_models import ProcessedResult, Action, ActionType
    from help_tooltip import show_help_window, add_help_indicator
    from follow_up_actions import FollowUpActionSystem
    from backup_manager import BackupManager
    from pdf_report_generator import PDFReportGenerator
    from command_registry import (Command, CommandRegistry,
                                  accelerator_label, tk_binding)
    ENHANCED_COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"Einige erweiterte Komponenten nicht verfügbar: {e}")
    ENHANCED_COMPONENTS_AVAILABLE = False


class EnhancedGui(BaseGui):
    """
    Enhanced GUI that extends the base GUI with new results processing features.
    
    This class maintains full backward compatibility with the existing GUI while
    adding enhanced features for data extraction, visualization, and results management.
    """
    
    def __init__(self, window):
        """Initialize the enhanced GUI."""
        if not ENHANCED_COMPONENTS_AVAILABLE:
            # Fall back to base GUI if components not available
            super().__init__(window)
            return
            
        # Initialize enhanced components first
        self.results_processor = ResultsProcessor()
        self.results_manager = ResultsManager()
        self.file_router = FileHandlerRouter()
        self.error_handler = ErrorHandler()
        self.follow_up_system = FollowUpActionSystem()
        self.backup_manager = BackupManager()
        self.pdf_report_generator = PDFReportGenerator()

        from projects import ProjectManager
        from recipes import RecipeManager
        self.project_manager = ProjectManager(self.results_manager.db_path)
        self.recipe_manager = RecipeManager(self.results_manager.db_path)
        
        # Current result tracking
        self.current_result: Optional[ProcessedResult] = None
        self.processing_thread: Optional[threading.Thread] = None

        # Zentrales Befehlsregister (Menüs, Shortcuts, Befehlspalette)
        self.commands = CommandRegistry()

        # Thread-safe queue for scheduling UI updates from worker threads
        self._ui_queue: queue.Queue = queue.Queue()

        # User profile, learning path, and prompt library
        self.user_profile_manager = UserProfileManager()
        self.learning_path = LearningPath(profile_manager=self.user_profile_manager)
        self.prompt_library = PromptLibrary()
        self.auto_save_enabled = self.user_profile_manager.get_setting("auto_save_enabled", True)
        self.auto_viz_enabled = self.user_profile_manager.get_setting("auto_viz_enabled", False)
        self.privacy_check_enabled = self.user_profile_manager.get_privacy_check_enabled()

        # Persistiertes Sitzungsbudget in die Analyse-Session laden
        from analysis import set_session_budget, set_provider, set_model
        set_session_budget(self.user_profile_manager.get_session_budget())
        provider_id = self.user_profile_manager.get_setting("provider_id", "openai")
        provider_url = self.user_profile_manager.get_setting("provider_base_url", "") or None
        set_provider(provider_id, provider_url)
        local_model = self.user_profile_manager.get_setting("local_model", "")
        if provider_id != "openai" and local_model:
            set_model(local_model, allow_unknown=True)

        # Initialize base GUI
        super().__init__(window)

        # Start processing the UI queue on the main thread
        self._poll_ui_queue()

        # Add enhanced components after base initialization
        self._setup_enhanced_components()

        # Tastatur-Shortcuts registrieren
        self._setup_keyboard_shortcuts()

    def _is_ui_alive(self) -> bool:
        """Return True if the main window still exists."""
        try:
            return self.window.winfo_exists()
        except tk.TclError:
            return False

    def _safe_after(self, delay_ms: int, callback, *args):
        """Schedule a callback on the main thread from any worker thread.

        Uses a thread-safe queue so Tkinter's after() is only called on the
        main thread. Callbacks are ignored if the UI has been destroyed.
        """
        try:
            self._ui_queue.put((delay_ms, callback, args))
        except Exception:
            pass

    def _poll_ui_queue(self):
        """Main-thread loop that drains the UI callback queue."""
        if not self._is_ui_alive():
            return
        try:
            while True:
                delay_ms, callback, args = self._ui_queue.get_nowait()
                try:
                    self.window.after(delay_ms, lambda cb=callback, a=args: cb(*a))
                except tk.TclError:
                    pass
        except queue.Empty:
            pass
        try:
            self.window.after(100, self._poll_ui_queue)
        except tk.TclError:
            pass

    def _safe_progress_start(self, message: str):
        """Start the progress indicator if the UI is still alive."""
        if self._is_ui_alive():
            try:
                self.progress_indicator.start(message)
            except tk.TclError:
                pass

    def _safe_progress_stop(self):
        """Stop the progress indicator if the UI is still alive."""
        if self._is_ui_alive():
            try:
                self.progress_indicator.stop()
            except tk.TclError:
                pass

    def _setup_keyboard_shortcuts(self):
        """Bindet alle im Befehlsregister hinterlegten Tastenkürzel global.

        tk_binding liefert auf macOS zusätzlich die ⌘-Variante.
        """
        for command in self.commands.all():
            if not command.shortcut:
                continue
            for sequence in tk_binding(command.shortcut):
                self.window.bind_all(
                    sequence,
                    lambda _event, cmd=command: self._dispatch_command(cmd))

    def _dispatch_command(self, command: "Command"):
        """Shortcut-Handler: führt den Befehl aus und schluckt das Event."""
        self._run_command(command)
        return "break"

    def _run_command(self, command: "Command"):
        """Führt einen registrierten Befehl aus (mit Ergebnis-Prüfung)."""
        if command.requires_result and self.current_result is None:
            messagebox.showinfo("Kein Ergebnis",
                                "Bitte wählen Sie zuerst ein Ergebnis aus.")
            return
        command.callback()

    def _show_command_palette(self):
        """Öffnet die Befehlspalette über dem Hauptfenster."""
        from command_palette import CommandPalette
        CommandPalette(
            self.window, self.commands,
            has_result=lambda: self.current_result is not None,
        )

    def _setup_enhanced_components(self):
        """Set up the enhanced components in the existing GUI structure."""
        # Replace the existing input tabs with enhanced version
        self._enhance_input_tabs()

        # Enhance the output area with new display components
        self._enhance_output_area()

        # Add learning path panel for beginners/intermediate users
        self._setup_learning_path_panel()
        self._apply_experience_level()

        # Add new menu items and toolbar
        self._add_enhanced_menu()

        # Show onboarding for first-time users
        self.window.after(100, self._maybe_show_onboarding)
        self.window.after(2000, self._maybe_check_updates)
        
    def _enhance_input_tabs(self):
        """Erweitert das bestehende Input-Notebook um neue Datei-Tabs,
        ohne die Original-Tabs (Webseite/YouTube/PDF) zu zerstören."""
        # Original-Notebook (Website/YouTube/PDF) bleibt erhalten.
        # ExtendedInputTabs fügt Excel/Bild-PDF/CSV-Text/Multi-Datei hinzu.
        self.enhanced_input_tabs = ExtendedInputTabs(
            self.input_tabs,
            status_callback=self._on_status_update
        )

        # Referenz für Backward-Compatibility
        self.enhanced_notebook = self.input_tabs
        
    def _enhance_output_area(self):
        """Enhance the output area with new display components."""
        # Store reference to original output text widget
        self.original_output_text = self.output_text
        
        # Create enhanced results display
        self.enhanced_output_frame = ttk.Frame(self.analysis_frame)
        self.enhanced_output_frame.grid(row=6, column=0, sticky=tk.W + tk.E + tk.N + tk.S, pady=(0, 10))
        self.analysis_frame.rowconfigure(6, weight=1)
        self.enhanced_output_frame.rowconfigure(0, weight=1)
        self.enhanced_output_frame.columnconfigure(0, weight=1)
        
        # Create tabbed interface for different result views
        self.result_notebook = ttk.Notebook(self.enhanced_output_frame)
        self.result_notebook.grid(row=0, column=0, sticky=tk.W + tk.E + tk.N + tk.S)
        
        # Text results tab (enhanced version of original)
        self.text_results_frame = ttk.Frame(self.result_notebook)
        self.result_notebook.add(self.text_results_frame, text="Textanalyse")
        self.text_results_frame.columnconfigure(0, weight=1)
        self.text_results_frame.columnconfigure(1, weight=0, minsize=240)
        self.text_results_frame.rowconfigure(0, weight=1)

        # Hilfe-Indikator für Textanalyse-Tab
        text_help_frame = ttk.Frame(self.text_results_frame)
        text_help_frame.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 2))
        add_help_indicator(text_help_frame,
                          "Hier wird das Analyseergebnis als strukturierter Text mit Markdown-Formatierung "
                          "angezeigt. Nutzen Sie die Zoom-Controls (oben rechts) zum Anpassen der Schriftgröße "
                          "und die Aktions-Buttons rechts für Folgeaktionen wie Zusammenfassen oder Übersetzen.")
        
        # Enhanced results display widget (left side)
        self.results_display = ResultsDisplayWidget(self.text_results_frame)
        self.results_display.grid(row=1, column=0, sticky=tk.W + tk.E + tk.N + tk.S, padx=(5, 0), pady=5)

        # Action buttons frame (right side)
        self.action_buttons = ActionButtonsFrame(
            self.text_results_frame,
            on_action_callback=self._handle_action_button
        )
        self.action_buttons.grid(row=1, column=1, sticky=tk.N + tk.S + tk.E + tk.W, padx=(5, 5), pady=5)

        # Move original note buttons (Notiz exportieren, In Zwischenablage) into the right column
        # below the action buttons
        if hasattr(self, 'note_buttons_frame'):
            self.note_buttons_frame.grid_forget()
            self.note_buttons_frame.grid(row=2, column=1, sticky=tk.EW, padx=(5, 5), pady=(0, 5))
            self.text_results_frame.rowconfigure(2, weight=0)
        
        # Visualization tab
        self.viz_frame = ttk.Frame(self.result_notebook)
        self.result_notebook.add(self.viz_frame, text="Visualisierung")
        
        self.visualization_panel = DataVisualizationPanel(
            self.viz_frame,
            on_chart_created=self._on_chart_created
        )
        
        # Add help indicator for visualization tab
        viz_help_frame = ttk.Frame(self.viz_frame)
        viz_help_frame.pack(fill=tk.X, padx=5, pady=2)
        add_help_indicator(viz_help_frame,
                          "Hier können Sie Diagramme und Visualisierungen aus den extrahierten Daten erstellen. "
                          "Wählen Sie den Diagrammtyp, passen Sie Titel und Achsen an und exportieren Sie als PNG/PDF/SVG.")
        
        # Data export tab
        self.export_frame = ttk.Frame(self.result_notebook)
        self.result_notebook.add(self.export_frame, text="Datenexport")
        
        self.excel_export_ui = ExcelExportUI(
            self.export_frame,
            on_export_completed=self._on_export_completed
        )
        
        # Add help indicator for export tab
        export_help_frame = ttk.Frame(self.export_frame)
        export_help_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(export_help_frame, text="Datenexport", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        add_help_indicator(export_help_frame,
                          "Hier können Sie Analyseergebnisse als Excel-Datei exportieren. "
                          "Die Daten werden strukturiert mit Metadaten, extrahierten Daten "
                          "und Visualisierungen gespeichert.")
        
        # Results browser tab
        self.browser_frame = ttk.Frame(self.result_notebook)
        self.result_notebook.add(self.browser_frame, text="Ergebnisverlauf")
        
        self.results_browser = ResultsBrowser(
            self.browser_frame,
            self.results_manager,
            on_result_selected=self._on_historical_result_selected,
            on_event=self._on_learning_event
        )
        
        # Add help indicator for results browser tab
        browser_help_frame = ttk.Frame(self.browser_frame)
        browser_help_frame.pack(fill=tk.X, padx=5, pady=2)
        add_help_indicator(browser_help_frame,
                          "Hier können Sie alle gespeicherten Analyseergebnisse durchsuchen, filtern und verwalten. "
                          "Nutzen Sie die Suchfunktion oder die Filter, um bestimmte Ergebnisse zu finden.")
        
        # Hide original output text widget but keep it for backward compatibility
        self.original_output_text.grid_remove()
        
        # Update the output_text reference to point to enhanced display
        self.output_text = self.results_display.text_widget
        
    def _add_enhanced_menu(self):
        """Add enhanced menu items and toolbar."""
        self._register_commands()

        # Create menu bar if it doesn't exist
        if not hasattr(self.window, 'menubar'):
            self.window.menubar = tk.Menu(self.window)
            self.window.config(menu=self.window.menubar)
            
        # Menüs werden vollständig aus dem Befehlsregister aufgebaut:
        # Separator zwischen den Kategorien in fester Reihenfolge.
        self.enhanced_menu = tk.Menu(self.window.menubar, tearoff=0)
        self.window.menubar.add_cascade(label="Erweiterte Funktionen", menu=self.enhanced_menu)
        self._fill_menu(self.enhanced_menu, (
            "Ergebnisse", "Export", "Analyse", "Arbeitsbereich",
            "Qualität", "Einstellungen",
        ))

        self.help_menu = tk.Menu(self.window.menubar, tearoff=0)
        self.window.menubar.add_cascade(label="Hilfe", menu=self.help_menu)
        self._fill_menu(self.help_menu, ("Hilfe", "Update"))

        self.view_menu = tk.Menu(self.window.menubar, tearoff=0)
        self.window.menubar.add_cascade(label="Ansicht", menu=self.view_menu)
        self._fill_menu(self.view_menu, ("Ansicht",))

        # Add prompt library button near the prompt field (reuses existing prompt frame)
        prompt_btn_frame = ttk.Frame(self.analysis_frame)
        prompt_btn_frame.grid(row=0, column=1, sticky=tk.E, pady=(0, 5))
        ttk.Button(prompt_btn_frame, text="Vorlagen",
                   command=self._show_prompt_library).pack()

        # Add progress indicator to status bar
        self.progress_indicator = ProgressIndicator(self.main_frame)

    def _register_commands(self):
        """Registriert alle Menü- und Shortcut-Befehle im zentralen Register.

        Neue Menüaktionen hier als Command registrieren, nicht direkt per
        add_command ins Menü schreiben – so bleiben Menü, Befehlspalette
        und Tastenkürzel synchron.
        """
        register = self.commands.register

        # Kategorie Ergebnisse
        register(Command(
            "results.manage", "Ergebnisse verwalten", "Ergebnisse",
            self._show_results_manager,
            keywords=("verlauf", "verwaltung")))
        register(Command(
            "results.compare", "Ergebnisse vergleichen", "Ergebnisse",
            self._compare_results,
            keywords=("vergleich", "diff")))
        register(Command(
            "results.tags", "Tags verwalten", "Ergebnisse",
            self._manage_tags,
            keywords=("tag", "schlagworte")))
        register(Command(
            "results.edit", "Ergebnis bearbeiten", "Ergebnisse",
            self._edit_current_result, requires_result=True,
            keywords=("editieren", "ändern")))
        register(Command(
            "results.versions", "Versionsverlauf", "Ergebnisse",
            self._show_versions_dialog, requires_result=True,
            keywords=("versionen", "wiederherstellen")))

        # Kategorie Export
        register(Command(
            "export.data", "Daten exportieren", "Export",
            self._show_export_dialog, requires_result=True,
            keywords=("excel", "csv", "json")))
        register(Command(
            "export.visualization", "Visualisierung erstellen", "Export",
            self._show_visualization_dialog, requires_result=True,
            keywords=("diagramm", "chart")))
        register(Command(
            "export.pdf_report", "PDF-Report erstellen", "Export",
            self._generate_pdf_report, requires_result=True,
            keywords=("bericht", "report")))
        register(Command(
            "export.batch_zip", "Batch-Export (ZIP)", "Export",
            self._batch_export, keywords=("zip", "archiv")))

        # Kategorie Analyse
        register(Command(
            "analysis.history", "Analyse-Historie anzeigen", "Analyse",
            self._show_analysis_history,
            keywords=("historie", "sitzung")))
        register(Command(
            "analysis.usage", "Token- & Kosten-Übersicht", "Analyse",
            self._show_usage_stats,
            keywords=("kosten", "token", "verbrauch", "budget")))

        # Kategorie Arbeitsbereich
        register(Command(
            "workspace.backup_create", "Backup erstellen", "Arbeitsbereich",
            self._create_backup, keywords=("sicherung",)))
        register(Command(
            "workspace.backup_restore", "Backup wiederherstellen",
            "Arbeitsbereich", self._restore_backup,
            keywords=("sicherung", "restore")))
        register(Command(
            "workspace.projects", "Projekte verwalten", "Arbeitsbereich",
            self._show_projects_dialog, keywords=("projekt",)))
        register(Command(
            "workspace.recipes", "Rezepte verwalten", "Arbeitsbereich",
            self._show_recipes_dialog, keywords=("rezept", "vorlage")))
        register(Command(
            "workspace.batch", "Batch-Verarbeitung", "Arbeitsbereich",
            self._show_batch_dialog, shortcut="Ctrl+B",
            keywords=("stapel", "mehrere dateien", "queue")))

        # Kategorie Qualität
        register(Command(
            "quality.evidence", "Quellenbelege prüfen", "Qualität",
            self._show_evidence_dialog, requires_result=True,
            keywords=("zitate", "belege", "quellen")))
        register(Command(
            "quality.edit_data", "Extrahierte Daten bearbeiten", "Qualität",
            self._edit_extracted_data, requires_result=True,
            keywords=("json", "daten", "strukturierte")))
        register(Command(
            "quality.chart_suggestions", "Diagramm-Vorschläge", "Qualität",
            self._show_chart_suggestions, requires_result=True,
            keywords=("charts", "vorschläge")))
        register(Command(
            "quality.playground", "Prompt-Playground", "Qualität",
            self._show_prompt_playground, shortcut="Ctrl+Shift+P",
            keywords=("prompt", "varianten", "modelle")))
        register(Command(
            "quality.evaluation", "Evaluationssuite", "Qualität",
            self._show_evaluation_dialog,
            keywords=("eval", "test", "qualität", "vergleich", "benchmark")))

        # Kategorie Einstellungen (inkl. Favoriten)
        register(Command(
            "settings.favorites", "Favoriten anzeigen", "Einstellungen",
            self._show_favorites, shortcut="Ctrl+F",
            keywords=("favorit", "gemerkt")))
        register(Command(
            "settings.open", "Einstellungen", "Einstellungen",
            self._show_settings_dialog, shortcut="Ctrl+,",
            keywords=("optionen", "provider", "budget")))

        # Kategorie Hilfe
        register(Command(
            "help.docs", "Dokumentation anzeigen", "Hilfe",
            lambda: show_help_window(self.window),
            keywords=("doku", "handbuch")))
        register(Command(
            "help.first_steps", "Hilfe: Erste Schritte", "Hilfe",
            lambda: show_help_window(self.window,
                                     anchor="Schnellstart für Anfänger"),
            keywords=("schnellstart", "einstieg")))
        register(Command(
            "help.onboarding", "Onboarding erneut starten", "Hilfe",
            self._show_onboarding, keywords=("einführung", "start")))

        # Kategorie Update (eigene Menügruppe im Hilfe-Menü)
        register(Command(
            "help.update_check", "Nach Updates suchen", "Update",
            self._check_for_updates,
            keywords=("aktualisierung", "version", "release")))

        # Kategorie Ansicht
        register(Command(
            "view.experience", "Erfahrungsgrad ändern", "Ansicht",
            self._show_experience_selector,
            keywords=("anfänger", "experte", "modus")))
        register(Command(
            "view.learning_path", "Lernpfad anzeigen/ausblenden", "Ansicht",
            self._toggle_learning_path_panel,
            keywords=("lernen", "panel")))
        register(Command(
            "view.command_palette", "Befehlspalette…", "Ansicht",
            self._show_command_palette, shortcut="Ctrl+K",
            keywords=("suche", "befehle", "commands", "palette")))

        # Globale Aktionen (nur Palette/Shortcuts, nicht in den Menüs)
        register(Command(
            "action.analyze", "Analyse starten", "Aktionen",
            self.send_question, shortcut="Ctrl+Return",
            keywords=("start", "ausführen")))
        register(Command(
            "action.save_note", "Aktuelles Ergebnis speichern", "Aktionen",
            self.save_note, shortcut="Ctrl+S",
            keywords=("notiz", "sichern")))
        register(Command(
            "action.export_pdf", "Aktuelles Ergebnis als PDF exportieren",
            "Aktionen",
            lambda: self._export_content_as_pdf(
                self.current_result.content if self.current_result
                else self.results_display.get_content()),
            shortcut="Ctrl+E", keywords=("pdf", "export")))

    def _fill_menu(self, menu: tk.Menu, categories):
        """Befüllt ein Menü kategorieweise aus dem Befehlsregister."""
        grouped = self.commands.by_category()
        first_group = True
        for category in categories:
            commands = grouped.get(category, [])
            if not commands:
                continue
            if not first_group:
                menu.add_separator()
            first_group = False
            for command in commands:
                self._add_menu_command(menu, command)

    def _add_menu_command(self, menu: tk.Menu, command: "Command"):
        """Fügt einen registrierten Befehl als Menüeintrag hinzu."""
        kwargs = {
            "label": command.label,
            "command": lambda cmd=command: self._run_command(cmd),
        }
        if command.shortcut:
            kwargs["accelerator"] = accelerator_label(command.shortcut)
        menu.add_command(**kwargs)

    def _on_status_update(self, message: str):
        """Handle status updates from enhanced components."""
        self.status_var.set(message)

    def _set_analysis_button_state(self, enabled: bool):
        if hasattr(self, "analysis_button"):
            self.analysis_button.configure(state=tk.NORMAL if enabled else tk.DISABLED)
        
    def _on_file_selected(self, file_paths: List[str], file_type: str):
        """Handle file selection from enhanced input tabs."""
        self.status_var.set(f"{len(file_paths)} Datei(en) ausgewählt: {file_type}")
        
    def _on_enhanced_analysis_requested(self, content: str, source_path: str, analysis_type: str):
        """Handle analysis request from enhanced input tabs."""
        # Read prompt values on the main thread before handing off to worker
        custom_prompt = self.question_text.get(1.0, tk.END).strip()
        is_custom_prompt = bool(custom_prompt)
        if custom_prompt:
            final_payload = f"{custom_prompt}\n\nInhalt: {content}"
        else:
            final_payload = self.get_prompt(content)

        # Lokale Datenschutzprüfung + kombinierte Übertragungsbestätigung
        from transfer_confirmation import confirm_transfer
        decision = confirm_transfer(
            self.window, final_payload,
            source_type=self._source_type_for_analysis(analysis_type),
            privacy_check=self.privacy_check_enabled,
        )
        if not decision.proceed:
            self.status_var.set("Analyse abgebrochen – keine Daten übertragen")
            return
        final_payload = decision.content

        # Start analysis in background thread
        self._set_analysis_button_state(False)
        self.processing_thread = threading.Thread(
            target=self._process_enhanced_analysis,
            args=(content, source_path, analysis_type, is_custom_prompt, final_payload)
        )
        self.processing_thread.daemon = True
        self.processing_thread.start()

    @staticmethod
    def _source_type_for_analysis(analysis_type: str) -> str:
        """Mappt interne Analysetypen auf Quelltypen für Übertragungshinweise."""
        mapping = {
            "pdf": "pdf", "image": "image", "website": "website",
            "youtube": "youtube", "file_analysis": "file",
            "excel": "file", "csv": "file", "multi": "file",
        }
        return mapping.get(analysis_type, "default")

    def _process_enhanced_analysis(self, content: str, source_path: str, analysis_type: str,
                                   is_custom_prompt: bool, final_payload: str):
        """Process analysis with enhanced features in background thread."""
        try:
            # Show progress
            self._safe_after(0, self._safe_progress_start, "Analyse wird durchgeführt...")

            outcome = analyze_text(final_payload)

            # Process result through enhanced processor
            processed_result = self.results_processor.process_analysis_outcome(
                outcome,
                source_path,
                analysis_type
            )

            # Update learning path for file-based analyses
            if is_custom_prompt:
                self.learning_path.record_event(LearningEvent(
                    LearningEventType.CUSTOM_PROMPT_SUCCEEDED,
                    operation_id=processed_result.id
                ))
            if analysis_type in ("file_analysis", "pdf", "excel", "csv", "image", "multi"):
                try:
                    self.learning_path.record_event(LearningEvent(
                        LearningEventType.FILE_ANALYZED,
                        operation_id=processed_result.id
                    ))
                except Exception:
                    pass

            # Update UI in main thread
            self._safe_after(0, self._display_enhanced_result, processed_result)

        except AnalysisFailure as e:
            self._safe_after(0, self._show_error, e.error.user_message)
        except Exception as e:
            error_msg = self.error_handler.create_user_friendly_message(
                self.error_handler.handle_error(e, {"operation": "analysis"})
            )
            self._safe_after(0, self._show_error, error_msg)
        finally:
            self._safe_after(0, self._safe_progress_stop)
            self._safe_after(0, self._set_analysis_button_state, True)
            
    def _display_enhanced_result(self, result: ProcessedResult):
        """Display enhanced analysis result."""
        self.current_result = result

        # In Analyse-History aufnehmen (falls nicht schon durch FollowUpSystem geschehen)
        try:
            history = self.follow_up_system.history_manager
            if not history.get_step_by_id(result.id):
                history.add_step(result=result, parent_step_id=None)
        except Exception as e:
            logging.error(f"Fehler beim Aufnehmen in die History: {e}")

        # Auto-Save: Ergebnis automatisch in Datenbank speichern
        if getattr(self, 'auto_save_enabled', True):
            try:
                self.results_manager.save_result(result)
            except Exception as e:
                logging.error(f"Fehler beim Auto-Save: {e}")

        # Update text display
        try:
            self.results_display.display_content(result.content, "markdown")
        except Exception as e:
            logging.error(f"Fehler beim Aktualisieren der Textanzeige: {e}")

        # Update action buttons
        try:
            self.action_buttons.update_actions(result.follow_up_actions)
            self.action_buttons.update_content(result.content, "text")
        except Exception as e:
            logging.error(f"Fehler beim Aktualisieren der Action-Buttons: {e}")

        # Update visualization panel
        try:
            if result.extracted_data:
                self.visualization_panel.load_data(result.extracted_data)
        except Exception as e:
            logging.error(f"Fehler beim Aktualisieren der Visualisierung: {e}")

        # Update export UI
        try:
            if result.extracted_data and hasattr(self.excel_export_ui, 'update_data'):
                self.excel_export_ui.update_data(result.extracted_data)
        except Exception as e:
            logging.error(f"Fehler beim Aktualisieren des Export-UI: {e}")

        # Refresh results browser
        try:
            self.results_browser.refresh_results()
        except Exception as e:
            logging.error(f"Fehler beim Aktualisieren des Ergebnis-Browsers: {e}")

        # Update learning path progress
        try:
            self.learning_path.record_event(LearningEventType.ANALYSIS_SUCCEEDED)
            self._update_learning_path_panel()
        except Exception:
            pass

        # Update status with cost/usage info
        try:
            from analysis import get_usage_stats
            stats = get_usage_stats()
            self.status_var.set(
                f"Analyse abgeschlossen | Gesamtkosten bisher: ${stats['total_cost']:.4f} "
                f"({stats['total_tokens']:,} Tokens)"
            )
        except Exception:
            self.status_var.set("Analyse abgeschlossen - Erweiterte Funktionen verfügbar")

    def _handle_action_button(self, action_name: str, content: str, content_type: str):
        """Handle action button click from the action buttons frame.

        Standardaktionen (zusammenfassen, vertiefen, uebersetzen, analysieren)
        werden über FollowUpActionSystem ausgeführt (mit Context-Preservation
        und History-Tracking). Andere Aktionen nutzen direkte Prompts.
        """
        if not content:
            if self.current_result:
                content = self.current_result.content
            else:
                # Read from the results text widget if no explicit content
                # (get_content liefert "" solange nur der Leer-Hinweis steht)
                content = self.results_display.get_content()

        if not content or content == "Das Ergebnis wird hier angezeigt...":
            messagebox.showinfo("Kein Inhalt", "Bitte führen Sie zuerst eine Analyse durch.")
            return

        # Handle non-AI actions first
        if action_name == "copy_to_clipboard":
            self.window.clipboard_clear()
            self.window.clipboard_append(content)
            self.window.update()
            self.status_var.set("Inhalt in Zwischenablage kopiert")
            return

        if action_name == "export_pdf":
            self._export_content_as_pdf(content)
            return

        if action_name == "create_visualization":
            self.result_notebook.select(self.viz_frame)
            self.status_var.set("Visualisierungs-Tab geöffnet")
            return

        # Mapping action_name -> ActionType für FollowUpActionSystem
        action_type_map = {
            "zusammenfassen": ActionType.SUMMARIZE,
            "vertiefen": ActionType.DEEPEN,
            "uebersetzen": ActionType.TRANSLATE,
            "analysieren": ActionType.ANALYZE,
            "einfach_erklären": ActionType.EXPLAIN,
        }

        # Übersetzungs-/Analyse-Varianten mit Parameter
        if action_name.startswith("uebersetzen_"):
            target_lang = action_name.split("_", 1)[1]
            self._execute_via_follow_up_system(
                ActionType.TRANSLATE, {"target_language": target_lang.title()})
            return
        if action_name.startswith("analysieren_"):
            analysis_focus = action_name.split("_", 1)[1].replace("_", " ")
            self._execute_via_follow_up_system(
                ActionType.ANALYZE, {"focus": analysis_focus})
            return

        # Standardaktionen über FollowUpActionSystem
        if action_name in action_type_map:
            self._execute_via_follow_up_system(action_type_map[action_name], {})
            return

        # Nicht-Standard-Aktionen: direkter Prompt
        if action_name == "extract_data":
            prompt = f"Extrahiere alle strukturierten Daten (Zahlen, Datumsangaben, Namen, Orte, Organisationen) aus folgendem Text und stelle sie tabellarisch dar:\n\n{content}"
        elif action_name == "find_similar":
            prompt = f"Finde und beschreibe ähnliche Inhalte, Themen oder Konzepte wie in folgendem Text:\n\n{content}"
        elif action_name == "add_tags":
            prompt = f"Extrahiere die wichtigsten Tags/Schlüsselwörter aus folgendem Text und gib sie als kommagetrennte Liste aus:\n\n{content}"
        elif action_name == "analyze_data":
            prompt = f"Analysiere die numerischen Daten und Statistiken im folgenden Text, interpretiere sie und gib eine Einschätzung ab:\n\n{content}"
        elif action_name == "explain_code":
            prompt = f"Erkläre den folgenden Code bzw. die technischen Inhalte verständlich, Schritt für Schritt:\n\n{content}"
        elif action_name == "einfach_erklären":
            prompt = f"Erkläre den folgenden Text so einfach und verständlich wie möglich. Vermeide Fachjargon oder erkläre ihn kurz:\n\n{content}"
        elif action_name == "check_sources":
            prompt = f"Prüfe den folgenden Text auf Quellenangaben, überprüfe die Plausibilität der Behauptungen und gib Hinweise auf mögliche Quellen:\n\n{content}"
        else:
            prompt = self._build_follow_up_prompt(action_name, content)

        if not prompt:
            messagebox.showinfo("Aktion", f"Aktion '{action_name}' ist noch nicht implementiert.")
            return

        # Execute in background thread
        self.progress_indicator.start(f"Führe {action_name} aus...")
        threading.Thread(
            target=self._run_action_button_analysis,
            args=(action_name, prompt),
            daemon=True
        ).start()

    def _execute_via_follow_up_system(self, action_type: ActionType, parameters: Dict[str, Any]):
        """Führt eine Folgeaktion über FollowUpActionSystem aus (mit History)."""
        if not self.current_result:
            messagebox.showinfo("Kein Inhalt", "Bitte führen Sie zuerst eine Analyse durch.")
            return

        action = Action(
            action_type=action_type,
            label=action_type.value,
            description=f"Follow-up: {action_type.value}",
            parameters=parameters
        )

        parent_step_id = self.current_result.id

        self.progress_indicator.start(f"Führe {action_type.value} aus...")
        threading.Thread(
            target=self._run_follow_up_system_action,
            args=(action, parent_step_id),
            daemon=True
        ).start()

    def _run_follow_up_system_action(self, action: Action, parent_step_id: Optional[str]):
        """Background-Thread: FollowUpActionSystem-Aktion ausführen."""
        try:
            new_result = self.follow_up_system.execute_follow_up_action(
                self.current_result, action, parent_step_id
            )
            self._safe_after(0, self._display_enhanced_result, new_result)
        except Exception as e:
            error_msg = self.error_handler.create_user_friendly_message(
                self.error_handler.handle_error(e, {"operation": "follow_up_system"})
            )
            self._safe_after(0, self._show_error, error_msg)
        finally:
            self._safe_after(0, self._safe_progress_stop)

    def _export_content_as_pdf(self, content: str):
        """Export content as a PDF file."""
        from tkinter import filedialog as fd
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Spacer, Paragraph
        from xml.sax.saxutils import escape as xml_escape

        file_path = fd.asksaveasfilename(
            title="PDF exportieren",
            defaultextension=".pdf",
            filetypes=[("PDF-Dateien", "*.pdf")]
        )
        if not file_path:
            return

        try:
            pdf = SimpleDocTemplate(file_path, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            story.append(Paragraph("Analyse-Ergebnis", styles["Heading1"]))
            story.append(Spacer(1, 0.25 * inch))
            # XML-escapen für ReportLab, dann Newlines als <br/> umwandeln
            safe_content = xml_escape(content).replace('\n', '<br/>')
            story.append(Paragraph(safe_content, styles["Normal"]))
            pdf.build(story)
            messagebox.showinfo("Export erfolgreich", f"PDF wurde gespeichert:\n{file_path}")
            self.status_var.set("PDF exportiert")
        except Exception as e:
            messagebox.showerror("Export-Fehler", f"Fehler beim PDF-Export: {str(e)}")

    def _build_follow_up_prompt(self, action_name: str, content: str) -> Optional[str]:
        """Build a prompt for a follow-up action."""
        if action_name == "zusammenfassen":
            return f"Fasse folgenden Text zusammen:\n\n{content}"
        elif action_name == "vertiefen":
            return f"Vertiefe und erweitere folgenden Inhalt:\n\n{content}"
        elif action_name.startswith("uebersetzen_"):
            target_lang = action_name.split("_", 1)[1].title()
            return f"Übersetze folgenden Text ins {target_lang}:\n\n{content}"
        elif action_name == "uebersetzen":
            return f"Übersetze folgenden Text:\n\n{content}"
        elif action_name.startswith("analysieren_"):
            analysis_type = action_name.split("_", 1)[1].replace("_", " ").title()
            return f"Führe eine {analysis_type} für folgenden Text durch:\n\n{content}"
        elif action_name == "analysieren":
            return f"Analysiere folgenden Text:\n\n{content}"
        elif action_name == "einfach_erklären":
            return f"Erkläre folgenden Text so einfach wie möglich. Vermeide Fachjargon oder erkläre ihn kurz:\n\n{content}"
        elif action_name == "exportieren" or action_name == "visualisieren":
            return None  # Not supported via simple text prompt
        else:
            return f"{action_name.replace('_', ' ').title()} folgenden Text:\n\n{content}"

    def _run_action_button_analysis(self, action_name: str, prompt: str):
        """Run the AI analysis for an action button in a background thread."""
        try:
            outcome = analyze_text(prompt)
            if not outcome.success:
                self._safe_after(0, self._show_error, outcome.error.user_message)
                return
            self._safe_after(0, self._display_action_button_result, action_name, outcome.content)
        except Exception as e:
            error_msg = self.error_handler.create_user_friendly_message(
                self.error_handler.handle_error(e, {"operation": "action_button"})
            )
            self._safe_after(0, self._show_error, error_msg)
        finally:
            self._safe_after(0, self._safe_progress_stop)

    def _display_action_button_result(self, action_name: str, result: str):
        """Display the result of an action button analysis."""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, f"=== {action_name.replace('_', ' ').title()} ===\n\n")
        markdown_to_tkinter_text(result, self.output_text)
        self.output_text.config(state=tk.DISABLED)
        self.status_var.set(f"{action_name.replace('_', ' ').title()} abgeschlossen")

        # Save to current result if available
        if self.current_result:
            self.current_result.content = f"=== {action_name.replace('_', ' ').title()} ===\n\n{result}"

        # Update learning path for follow-up actions
        try:
            event_type = (
                LearningEventType.DATA_EXTRACTED
                if action_name == "extract_data"
                else LearningEventType.FOLLOW_UP_SUCCEEDED
            )
            self.learning_path.record_event(event_type)
            self._update_learning_path_panel()
        except Exception:
            pass

    def _on_action_requested(self, action_type: str):
        """Handle action request from results display."""
        if self.current_result:
            self._execute_follow_up_action(action_type, self.current_result.content)
            
    def _on_follow_up_action(self, action_type: str, context: str):
        """Handle follow-up action execution."""
        self._execute_follow_up_action(action_type, context)
        
    def _execute_follow_up_action(self, action_type: str, context: str):
        """Execute a follow-up action."""
        try:
            # Show progress
            self.progress_indicator.start(f"Führe {action_type} aus...")
            
            # Execute action through results processor
            result = self.results_processor.execute_follow_up_action(action_type, context)
            
            if result:
                self._display_enhanced_result(result)
            
        except Exception as e:
            error_msg = self.error_handler.create_user_friendly_message(
                self.error_handler.handle_error(e, {"operation": "follow_up_action"})
            )
            self._show_error(error_msg)
        finally:
            self.progress_indicator.stop()
            
    def _on_learning_event(self, event_name: str):
        self.learning_path.record_event(event_name)
        self._update_learning_path_panel()

    def _on_chart_created(self, visualization):
        """Handle chart creation completion."""
        self.learning_path.record_event(LearningEventType.CHART_CREATED)
        self._update_learning_path_panel()
        chart_name = visualization.file_path or visualization.chart_type.value
        self.status_var.set(f"Diagramm erstellt: {os.path.basename(chart_name)}")
        
    def _on_export_completed(self, export_path: str):
        """Handle export completion."""
        self.learning_path.record_event(LearningEventType.EXCEL_EXPORTED)
        self._update_learning_path_panel()
        self.status_var.set(f"Export abgeschlossen: {os.path.basename(export_path)}")
        messagebox.showinfo("Export erfolgreich", f"Daten wurden exportiert nach:\n{export_path}")
        
    def _on_historical_result_selected(self, result: ProcessedResult):
        """Handle selection of historical result."""
        self._display_enhanced_result(result)
        
    def _show_error(self, error_msg: str):
        """Show error message to user safely from any thread."""
        if not self._is_ui_alive():
            return
        try:
            messagebox.showerror("Fehler", error_msg)
            self.status_var.set("Fehler aufgetreten")
        except tk.TclError:
            pass
        
    def _show_results_manager(self):
        """Show results management dialog."""
        # Switch to results browser tab
        self.result_notebook.select(self.browser_frame)
        
    def _show_export_dialog(self):
        """Show export dialog."""
        # Switch to export tab
        self.result_notebook.select(self.export_frame)
        
    def _show_visualization_dialog(self):
        """Show visualization dialog."""
        # Switch to visualization tab
        self.result_notebook.select(self.viz_frame)

    def _show_analysis_history(self):
        """Zeigt die Analyse-Historie als Dialog mit Verzweigungs-Info."""
        history = self.follow_up_system.history_manager
        steps = history.current_session

        dialog = tk.Toplevel(self.window)
        dialog.title("Analyse-Historie")
        dialog.geometry("700x500")
        dialog.transient(self.window)

        ttk.Label(dialog, text="Analyse-Historie (aktueller Sitzung)",
                  font=("Segoe UI", 12, "bold")).pack(pady=10)

        text_widget = scrolledtext.ScrolledText(dialog, wrap=tk.WORD,
                                                font=("Segoe UI", 10), state=tk.DISABLED)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        content_lines = []
        if not steps:
            content_lines.append("Noch keine Analyseschritte in dieser Sitzung.")
        else:
            for i, step in enumerate(steps, 1):
                created = step.context.created_at.strftime("%H:%M:%S")
                chain = " → ".join(a.value for a in step.context.action_chain) or "Erstanalyse"
                parent = f" (Parent: {step.parent_step_id[:8]}...)" if step.parent_step_id else ""
                content_lines.append(
                    f"{i}. [{created}] Schritt {step.context.step_number} | {chain}{parent}\n"
                    f"   ID: {step.result.id[:8]}... | Quelle: {step.result.source_info.file_path or step.result.source_info.url or '—'}\n"
                )

        text_widget.config(state=tk.NORMAL)
        text_widget.insert(tk.END, "\n".join(content_lines))
        text_widget.config(state=tk.DISABLED)

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=(5, 10))

        if steps:
            def save_session():
                from tkinter import filedialog as fd
                name = f"Sitzung_{len(steps)}_Schritte"
                try:
                    path = self.follow_up_system.save_session(name)
                    messagebox.showinfo("Gespeichert", f"Sitzung gespeichert:\n{path}")
                except Exception as e:
                    messagebox.showerror("Fehler", f"Speichern fehlgeschlagen: {e}")

            ttk.Button(btn_frame, text="Sitzung speichern", command=save_session).pack(side=tk.LEFT)

        ttk.Button(btn_frame, text="Schließen", command=dialog.destroy).pack(side=tk.RIGHT)

    def _show_usage_stats(self):
        """Zeigt Token-Verbrauch und geschätzte Kosten der aktuellen Sitzung."""
        stats = get_usage_stats()

        dialog = tk.Toplevel(self.window)
        dialog.title("Token- & Kosten-Übersicht")
        dialog.geometry("420x280")
        dialog.transient(self.window)
        dialog.grab_set()

        ttk.Label(dialog, text="API-Nutzung (aktuelle Sitzung)",
                  font=("Segoe UI", 12, "bold")).pack(pady=10)

        info_frame = ttk.Frame(dialog, padding=15)
        info_frame.pack(fill=tk.X)

        from analysis import get_budget_status
        budget = get_budget_status()
        rows = [
            ("Aktuelles Modell", stats.get("model", "—")),
            ("Verbrauchte Tokens", f"{stats.get('total_tokens', 0):,}"),
            ("Geschätzte Kosten", f"${stats.get('total_cost', 0.0):.4f}"),
        ]
        if budget.get("limit"):
            rows.append((
                "Sitzungsbudget",
                f"${budget['spent']:.4f} / ${budget['limit']:.4f} "
                f"({budget['fraction'] * 100:.0f} %)"
            ))
        for label, value in rows:
            row = ttk.Frame(info_frame)
            row.pack(fill=tk.X, pady=3)
            ttk.Label(row, text=f"{label}:", width=22, anchor=tk.W).pack(side=tk.LEFT)
            ttk.Label(row, text=value, font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=15, pady=(5, 15))

        def do_reset():
            reset_usage_stats()
            messagebox.showinfo("Zurückgesetzt", "Token-Zähler wurde zurückgesetzt.")
            dialog.destroy()

        ttk.Button(btn_frame, text="Zurücksetzen", command=do_reset).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Schließen", command=dialog.destroy).pack(side=tk.RIGHT)

    def _create_backup(self):
        """Erstellt ein ZIP-Backup aus Datenbank und Ergebnis-Dateien."""
        include_config = messagebox.askyesno(
            "Backup erstellen",
            "Soll die Konfiguration (ohne API-Key) ins Backup aufgenommen werden?"
        )
        try:
            path = self.backup_manager.create_backup(include_config=include_config)
            messagebox.showinfo("Backup erfolgreich",
                                f"Backup wurde erstellt:\n{path}")
            self.status_var.set(f"Backup erstellt: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Backup-Fehler", f"Fehler beim Backup: {str(e)}")

    def _restore_backup(self):
        """Stellt ein Backup aus einer ZIP-Datei wieder her."""
        from tkinter import filedialog as fd
        backup_file = fd.askopenfilename(
            title="Backup-Datei auswählen",
            filetypes=[("ZIP-Backups", "*.zip"), ("Alle Dateien", "*.*")],
            initialdir=str(self.backup_manager.backup_dir)
        )
        if not backup_file:
            return

        confirm = messagebox.askyesno(
            "Backup wiederherstellen",
            "Achtung: Dies überschreibt die aktuelle Datenbank und alle Ergebnisse.\n"
            "Möchten Sie fortfahren?"
        )
        if not confirm:
            return

        try:
            result = self.backup_manager.restore_backup(backup_file, overwrite=True)
            self.results_browser.refresh_results()
            message = f"Backup wurde wiederhergestellt aus:\n{backup_file}"
            if result.get("safety_backup"):
                message += (f"\n\nDer vorherige Stand wurde gesichert unter:\n"
                            f"{result['safety_backup']}")
            messagebox.showinfo("Restore erfolgreich", message)
            self.status_var.set("Backup wiederhergestellt")
        except Exception as e:
            messagebox.showerror("Restore-Fehler", f"Fehler beim Restore: {str(e)}")

    def _batch_export(self):
        """Exportiert mehrere ausgewählte Ergebnisse in ein ZIP-Archiv."""
        # Zum Ergebnisverlauf-Tab wechseln und Anleitung zeigen
        self.result_notebook.select(self.browser_frame)
        messagebox.showinfo(
            "Batch-Export",
            "Im Ergebnisverlauf-Tab können Sie mehrere Ergebnisse mit Strg+Klick auswählen.\n"
            "Klicken Sie dann rechts auf einen Eintrag und wählen Sie 'Exportieren' für den Batch-Export."
        )

    def _compare_results(self):
        """Öffnet den Ergebnisverlauf zum Vergleichen von Ergebnissen."""
        self.result_notebook.select(self.browser_frame)
        messagebox.showinfo(
            "Ergebnisse vergleichen",
            "Im Ergebnisverlauf-Tab können Sie zwei oder mehr Ergebnisse mit Strg+Klick auswählen.\n"
            "Klicken Sie dann rechts auf einen Eintrag und wählen Sie 'Vergleichen'."
        )

    def _generate_pdf_report(self):
        """Generiert einen vollständigen PDF-Report mit Deckblatt, TOC, Daten und Charts."""
        if not self.current_result:
            messagebox.showinfo("Kein Ergebnis", "Bitte führen Sie zuerst eine Analyse durch.")
            return

        from tkinter import filedialog as fd
        file_path = fd.asksaveasfilename(
            title="PDF-Report speichern",
            defaultextension=".pdf",
            filetypes=[("PDF-Dateien", "*.pdf")],
            initialfile=f"analyse_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
        if not file_path:
            return

        include_charts = messagebox.askyesno(
            "PDF-Report",
            "Sollen verfügbare Visualisierungen in den Report eingebettet werden?"
        )

        try:
            self.progress_indicator.start("PDF-Report wird erstellt...")
            path = self.pdf_report_generator.generate_report(
                self.current_result,
                output_path=file_path,
                include_charts=include_charts,
                include_data_tables=True
            )
            messagebox.showinfo("Report erstellt",
                                f"PDF-Report wurde gespeichert:\n{path}")
            self.status_var.set(f"PDF-Report erstellt: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Report-Fehler", f"Fehler beim Erstellen des Reports: {str(e)}")
        finally:
            self.progress_indicator.stop()

    def _manage_tags(self):
        """Dialog zur Tag-Verwaltung für das aktuelle Ergebnis."""
        if not self.current_result:
            messagebox.showinfo("Kein Ergebnis", "Bitte führen Sie zuerst eine Analyse durch.")
            return

        result_id = self.current_result.id
        current_tags = self.current_result.metadata.tags

        dialog = tk.Toplevel(self.window)
        dialog.title("Tags verwalten")
        dialog.geometry("450x400")
        dialog.transient(self.window)
        dialog.grab_set()

        ttk.Label(dialog, text="Tags für aktuelles Ergebnis",
                  font=("Segoe UI", 12, "bold")).pack(pady=10)

        # Aktuelle Tags anzeigen
        tags_frame = ttk.LabelFrame(dialog, text="Aktuelle Tags", padding=10)
        tags_frame.pack(fill=tk.X, padx=15, pady=5)

        tags_var = tk.StringVar(value=", ".join(current_tags) if current_tags else "(keine)")
        ttk.Label(tags_frame, textvariable=tags_var, wraplength=400).pack(anchor=tk.W)

        # Alle verfügbaren Tags
        all_tags_frame = ttk.LabelFrame(dialog, text="Alle verwendeten Tags", padding=10)
        all_tags_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        all_tags_listbox = tk.Listbox(all_tags_frame, height=8)
        all_tags_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        all_tags_scrollbar = ttk.Scrollbar(all_tags_frame, command=all_tags_listbox.yview)
        all_tags_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        all_tags_listbox.config(yscrollcommand=all_tags_scrollbar.set)

        def refresh_tags():
            all_tags_listbox.delete(0, tk.END)
            for tag in self.results_manager.get_all_tags():
                all_tags_listbox.insert(tk.END, tag)
            current = self.results_manager.load_result(result_id)
            if current:
                tags_var.set(", ".join(current.metadata.tags) if current.metadata.tags else "(keine)")

        refresh_tags()

        # Eingabe für neues Tag
        input_frame = ttk.Frame(dialog)
        input_frame.pack(fill=tk.X, padx=15, pady=5)

        new_tag_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=new_tag_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        def add_tag():
            tag = new_tag_var.get().strip()
            if tag:
                self.results_manager.add_tag(result_id, tag)
                new_tag_var.set("")
                refresh_tags()
                self.status_var.set(f"Tag hinzugefügt: {tag}")

        ttk.Button(input_frame, text="Hinzufügen", command=add_tag).pack(side=tk.LEFT)

        def remove_selected_tag():
            selection = all_tags_listbox.curselection()
            if selection:
                tag = all_tags_listbox.get(selection[0])
                self.results_manager.remove_tag(result_id, tag)
                refresh_tags()
                self.status_var.set(f"Tag entfernt: {tag}")

        ttk.Button(dialog, text="Ausgewähltes Tag entfernen",
                   command=remove_selected_tag).pack(pady=5)

        ttk.Button(dialog, text="Schließen", command=dialog.destroy).pack(pady=10)

    def _show_favorites(self):
        """Zeigt alle als Favorit markierten Ergebnisse an."""
        favorites = self.results_manager.get_favorites()

        dialog = tk.Toplevel(self.window)
        dialog.title("Favoriten")
        dialog.geometry("600x400")
        dialog.transient(self.window)

        ttk.Label(dialog, text="Favoriten", font=("Segoe UI", 12, "bold")).pack(pady=10)

        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        tree = ttk.Treeview(list_frame, columns=("title", "type", "date"),
                            show="headings", height=12)
        tree.heading("title", text="Titel")
        tree.heading("type", text="Typ")
        tree.heading("date", text="Erstellt am")
        tree.column("title", width=300)
        tree.column("type", width=120)
        tree.column("date", width=150)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, command=tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=scrollbar.set)

        for fav in favorites:
            tree.insert("", tk.END, values=(
                fav.title,
                fav.analysis_type,
                fav.created_at.strftime("%d.%m.%Y %H:%M")
            ), iid=fav.id)

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=15, pady=(5, 15))

        def open_selected():
            selected = tree.selection()
            if selected:
                result_id = selected[0]
                result = self.results_manager.load_result(result_id)
                if result:
                    self._display_enhanced_result(result)
                    dialog.destroy()

        def toggle_fav():
            selected = tree.selection()
            if selected:
                result_id = selected[0]
                new_state = self.results_manager.toggle_favorite(result_id)
                if not new_state:
                    # Favorit entfernt → aus Liste löschen
                    tree.delete(result_id)
                self.status_var.set("Favorit aktualisiert")

        ttk.Button(btn_frame, text="Öffnen", command=open_selected).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Favorit entfernen", command=toggle_fav).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Schließen", command=dialog.destroy).pack(side=tk.RIGHT)

    def _show_settings_dialog(self):
        """Show settings dialog with functional auto-save/auto-viz options."""
        # Default-Werte initialisieren (beim ersten Aufruf)
        if not hasattr(self, 'auto_save_enabled'):
            self.auto_save_enabled = True
        if not hasattr(self, 'auto_viz_enabled'):
            self.auto_viz_enabled = False

        dialog = tk.Toplevel(self.window)
        dialog.title("Einstellungen")
        dialog.geometry("480x640")
        dialog.transient(self.window)
        dialog.grab_set()

        ttk.Label(dialog, text="Erweiterte Einstellungen",
                  font=("Segoe UI", 12, "bold")).pack(pady=10)

        auto_save_var = tk.BooleanVar(value=self.auto_save_enabled)
        auto_viz_var = tk.BooleanVar(value=self.auto_viz_enabled)
        privacy_var = tk.BooleanVar(value=self.privacy_check_enabled)
        current_budget = self.user_profile_manager.get_session_budget()
        budget_var = tk.StringVar(
            value=f"{current_budget:.2f}" if current_budget else ""
        )

        ttk.Checkbutton(
            dialog,
            text="Ergebnisse automatisch speichern",
            variable=auto_save_var
        ).pack(anchor=tk.W, padx=20, pady=5)
        add_help_indicator(
            dialog,
            "Wenn aktiviert, wird jedes Analyseergebnis nach Abschluss automatisch "
            "in der Ergebnis-Datenbank gespeichert."
        )

        ttk.Checkbutton(
            dialog,
            text="Visualisierungen automatisch erstellen",
            variable=auto_viz_var
        ).pack(anchor=tk.W, padx=20, pady=5)
        add_help_indicator(
            dialog,
            "Wenn aktiviert, werden nach jeder Analyse mit numerischen Daten automatisch "
            "Diagramme im Visualisierungs-Tab erstellt."
        )

        ttk.Checkbutton(
            dialog,
            text="Datenschutzprüfung vor Übertragung",
            variable=privacy_var
        ).pack(anchor=tk.W, padx=20, pady=5)
        add_help_indicator(
            dialog,
            "Wenn aktiviert, wird jeder an die KI gesendete Inhalt lokal auf "
            "personenbezogene Daten und mögliche Secrets (API-Keys, Passwörter) "
            "geprüft. Bei Funden können Sie schwärzen oder abbrechen."
        )

        update_check_var = tk.BooleanVar(
            value=bool(self.user_profile_manager.get_setting(
                "update_check_on_start", False)))
        ttk.Checkbutton(
            dialog,
            text="Beim Start nach Updates suchen",
            variable=update_check_var
        ).pack(anchor=tk.W, padx=20, pady=5)
        add_help_indicator(
            dialog,
            "Wenn aktiviert, wird beim App-Start einmalig die GitHub-Releases-"
            "Seite nach einer neueren Version abgefragt. Es werden keine "
            "Nutzungsdaten übertragen. Standardmäßig deaktiviert."
        )

        budget_frame = ttk.Frame(dialog)
        budget_frame.pack(anchor=tk.W, padx=20, pady=5)
        ttk.Label(budget_frame, text="Sitzungsbudget (USD, leer = unbegrenzt):"
                  ).pack(side=tk.LEFT)
        budget_entry = ttk.Entry(budget_frame, textvariable=budget_var, width=10)
        budget_entry.pack(side=tk.LEFT, padx=5)
        add_help_indicator(
            budget_frame,
            "Optionales Kostenlimit pro Sitzung. Ab 80 % Auslastung warnt die App "
            "vor jeder weiteren Anfrage; bei Überschreitung ist eine explizite "
            "Bestätigung erforderlich."
        )

        # --- Provider-Auswahl (M9) ---------------------------------------
        from providers import PROVIDERS
        provider_ids = list(PROVIDERS.keys())
        provider_names = {pid: PROVIDERS[pid].name for pid in provider_ids}
        name_to_id = {v: k for k, v in provider_names.items()}

        saved_provider = self.user_profile_manager.get_setting("provider_id", "openai")
        saved_base_url = self.user_profile_manager.get_setting("provider_base_url", "")
        saved_local_model = self.user_profile_manager.get_setting("local_model", "")

        provider_var = tk.StringVar(
            value=provider_names.get(saved_provider, provider_names["openai"]))
        base_url_var = tk.StringVar(
            value=saved_base_url or PROVIDERS["ollama"].base_url)
        local_model_var = tk.StringVar(value=saved_local_model)

        provider_frame = ttk.LabelFrame(dialog, text="Analyse-Provider", padding=8)
        provider_frame.pack(fill=tk.X, padx=20, pady=8)

        provider_combo = ttk.Combobox(
            provider_frame, textvariable=provider_var, state="readonly",
            values=list(provider_names.values()), width=32)
        provider_combo.pack(anchor=tk.W)

        url_row = ttk.Frame(provider_frame)
        url_row.pack(fill=tk.X, pady=(6, 0))
        ttk.Label(url_row, text="Base-URL:").pack(side=tk.LEFT)
        ttk.Entry(url_row, textvariable=base_url_var, width=30).pack(
            side=tk.LEFT, padx=4)

        model_row = ttk.Frame(provider_frame)
        model_row.pack(fill=tk.X, pady=(4, 0))
        ttk.Label(model_row, text="Lokales Modell:").pack(side=tk.LEFT)
        local_model_combo = ttk.Combobox(
            model_row, textvariable=local_model_var, width=24)
        local_model_combo.pack(side=tk.LEFT, padx=4)

        def detect_models():
            from providers import detect_models, get_provider
            pid = name_to_id.get(provider_var.get(), "openai")
            provider = get_provider(pid, base_url_var.get().strip())
            if provider is None or not provider.base_url:
                messagebox.showinfo("Kein lokaler Server",
                                    "Dieser Provider hat keine abfragbare URL.",
                                    parent=dialog)
                return
            models = detect_models(provider)
            if models:
                local_model_combo["values"] = models
                if not local_model_var.get():
                    local_model_var.set(models[0])
                self.status_var.set(f"{len(models)} lokale Modelle gefunden")
            else:
                messagebox.showinfo(
                    "Keine Modelle",
                    "Der Server antwortet nicht oder listet keine Modelle. "
                    "Läuft z. B. Ollama?", parent=dialog)

        ttk.Button(provider_frame, text="Modelle erkennen",
                   command=detect_models).pack(anchor=tk.W, pady=(4, 0))
        provider_hint_var = tk.StringVar(value=PROVIDERS[saved_provider].hint
                                       if saved_provider in PROVIDERS else "")
        ttk.Label(provider_frame, textvariable=provider_hint_var,
                  wraplength=380, justify=tk.LEFT,
                  foreground="#555").pack(anchor=tk.W, pady=(4, 0))

        model_warning_var = tk.StringVar(value="")
        ttk.Label(provider_frame, textvariable=model_warning_var,
                  wraplength=380, justify=tk.LEFT,
                  foreground="#a06000").pack(anchor=tk.W, pady=(2, 0))

        def refresh_model_warning(_event=None):
            from providers import get_provider, looks_like_cloud_model
            pid = name_to_id.get(provider_var.get(), "openai")
            provider = get_provider(pid, base_url_var.get().strip() or None)
            if pid != "openai" and provider and provider.is_local \
                    and looks_like_cloud_model(local_model_var.get()):
                model_warning_var.set(
                    "Warnung: Der Modellname sieht wie ein OpenAI-Cloud-Modell "
                    "aus und ist auf dem lokalen Server vermutlich nicht "
                    "installiert. Lokale Server benötigen lokal installierte "
                    "Modelle (z. B. 'llama3:latest').")
            else:
                model_warning_var.set("")

        def on_provider_change(_event=None):
            pid = name_to_id.get(provider_var.get(), "openai")
            provider_hint_var.set(PROVIDERS[pid].hint)
            if pid == "ollama" and not base_url_var.get().strip():
                base_url_var.set(PROVIDERS["ollama"].base_url)
            refresh_model_warning()

        provider_combo.bind("<<ComboboxSelected>>", on_provider_change)
        local_model_combo.bind("<KeyRelease>", refresh_model_warning)
        local_model_combo.bind("<<ComboboxSelected>>", refresh_model_warning)
        refresh_model_warning()

        def apply_and_close():
            raw_budget = budget_var.get().strip().replace(",", ".")
            budget_value = None
            if raw_budget:
                try:
                    budget_value = float(raw_budget)
                    if budget_value <= 0:
                        raise ValueError
                except ValueError:
                    messagebox.showerror(
                        "Ungültiges Budget",
                        "Bitte geben Sie eine positive Zahl in USD ein oder lassen Sie das Feld leer.",
                        parent=dialog
                    )
                    return
            self.auto_save_enabled = auto_save_var.get()
            self.auto_viz_enabled = auto_viz_var.get()
            self.privacy_check_enabled = privacy_var.get()
            self.user_profile_manager.set_setting("auto_save_enabled", self.auto_save_enabled)
            self.user_profile_manager.set_setting("auto_viz_enabled", self.auto_viz_enabled)
            self.user_profile_manager.set_privacy_check_enabled(self.privacy_check_enabled)
            self.user_profile_manager.set_setting(
                "update_check_on_start", update_check_var.get())
            self.user_profile_manager.set_session_budget(budget_value)
            from analysis import set_session_budget, set_provider, set_model
            set_session_budget(budget_value)

            provider_id = name_to_id.get(provider_var.get(), "openai")
            provider_url = base_url_var.get().strip() or None
            self.user_profile_manager.set_setting("provider_id", provider_id)
            self.user_profile_manager.set_setting("provider_base_url", provider_url or "")
            self.user_profile_manager.set_setting("local_model", local_model_var.get().strip())
            set_provider(provider_id, provider_url)
            if provider_id != "openai" and local_model_var.get().strip():
                set_model(local_model_var.get().strip(), allow_unknown=True)
            self.status_var.set(
                f"Einstellungen gespeichert (Auto-Save: {'an' if self.auto_save_enabled else 'aus'})"
            )
            dialog.destroy()

        ttk.Button(dialog, text="Übernehmen", command=apply_and_close).pack(pady=10)
        ttk.Button(dialog, text="Abbrechen", command=dialog.destroy).pack()

    # ------------------------------------------------------------------
    # Projekte, Rezepte und Ergebnis-Versionen
    # ------------------------------------------------------------------

    def _show_projects_dialog(self):
        """Öffnet die Projektverwaltung."""
        from workspace_ui import ProjectsDialog
        ProjectsDialog(
            self.window,
            self.project_manager,
            self.results_manager,
            current_result_id=self.current_result.id if self.current_result else None,
            on_change=lambda: self.results_browser.refresh_results(),
        )

    def _show_recipes_dialog(self):
        """Öffnet die Rezeptverwaltung."""
        from workspace_ui import RecipesDialog
        RecipesDialog(
            self.window,
            self.recipe_manager,
            on_apply=self._apply_recipe,
            current_prompt=self.question_text.get(1.0, tk.END),
            current_model=self.model_var.get(),
        )

    def _apply_recipe(self, recipe):
        """Übernimmt Modell und Prompt-Vorlage eines Rezepts in die Oberfläche."""
        if recipe.model and recipe.model in AVAILABLE_MODELS:
            self.model_var.set(recipe.model)
            self._on_model_changed()
        self.question_text.delete(1.0, tk.END)
        self.question_text.insert(1.0, recipe.prompt_template)
        extras = []
        if recipe.follow_up_actions:
            extras.append(f"Folgeaktionen: {', '.join(recipe.follow_up_actions)}")
        if recipe.export_format:
            extras.append(f"Export: {recipe.export_format}")
        suffix = f" ({'; '.join(extras)})" if extras else ""
        self.status_var.set(f"Rezept '{recipe.name}' geladen{suffix}")

    def _edit_current_result(self):
        """Öffnet den Editor für den Inhalt des aktuellen Ergebnisses."""
        if not self.current_result:
            messagebox.showinfo("Kein Ergebnis",
                                "Bitte wählen Sie zuerst ein Ergebnis aus.")
            return
        from workspace_ui import EditResultDialog
        EditResultDialog(
            self.window, self.results_manager, self.current_result.id,
            on_saved=self._reload_current_result,
        )

    def _show_versions_dialog(self):
        """Öffnet den Versionsverlauf des aktuellen Ergebnisses."""
        if not self.current_result:
            messagebox.showinfo("Kein Ergebnis",
                                "Bitte wählen Sie zuerst ein Ergebnis aus.")
            return
        from workspace_ui import VersionsDialog
        VersionsDialog(
            self.window, self.results_manager, self.current_result.id,
            on_change=self._reload_current_result,
        )

    def _show_batch_dialog(self):
        """Öffnet die Batch-Queue-Verwaltung."""
        if not hasattr(self, "_batch_queue"):
            from batch_queue import BatchQueue
            self._batch_queue = BatchQueue(
                self.results_manager.db_path,
                results_manager=self.results_manager,
            )
        from workspace_ui import BatchDialog
        BatchDialog(
            self.window, self._batch_queue,
            on_result_saved=lambda: self.results_browser.refresh_results(),
        )

    def _load_source_document(self):
        """Lädt die Originalquelle des aktuellen Ergebnisses als SourceDocument.

        Unterstützt lokale Textdateien, PDFs (Seiten via OCR) und
        YouTube-URLs (Transkript mit Dauer). Websites werden nicht erneut
        abgerufen – ohne Quelle bleiben Belege ehrlich 'nicht prüfbar'.
        Kann langsam sein (OCR) – Aufruf nur in Worker-Threads.
        """
        from evidence import SourceDocument
        result = self.current_result
        if not result or not result.source_info:
            return None
        info = result.source_info

        if info.file_path:
            path = info.file_path
            if not os.path.isfile(path):
                return None
            ext = os.path.splitext(path)[1].lower()
            try:
                if ext in (".txt", ".md", ".csv", ".json", ".log", ".xml", ".html"):
                    text = open(path, "r", encoding="utf-8",
                                errors="replace").read()
                    return SourceDocument(text=text)
                if ext == ".pdf":
                    return self._load_pdf_source_document(path)
            except Exception:
                logger.info("Quelldokument konnte nicht geladen werden: %s",
                            path, exc_info=True)
                return None
            return None

        if info.url and info.type == "youtube":
            try:
                from analysis import extract_transkript_entries
                entries = extract_transkript_entries(info.url)
                if not entries:
                    return None
                text = " ".join(e["text"] for e in entries)
                duration = max(e["start"] + e["duration"] for e in entries)
                return SourceDocument(text=text, duration=duration)
            except Exception:
                logger.info("YouTube-Transkript für Belegprüfung nicht ladbar",
                            exc_info=True)
                return None

        if info.url:
            try:
                from analysis import extract_content
                outcome = extract_content(info.url)
                if outcome.success:
                    return SourceDocument(text=outcome.content)
            except Exception:
                pass
        return None

    def _load_pdf_source_document(self, path: str):
        """Extrahiert PDF-Seiten per OCR für die Belegprüfung.

        Benötigt poppler + tesseract; bei fehlenden Tools oder Fehlern wird
        None zurückgegeben (Belege bleiben ehrlich 'nicht prüfbar').
        """
        from evidence import SourceDocument
        try:
            from pdf2image import convert_from_path
            import pytesseract
        except ImportError:
            return None
        try:
            images = convert_from_path(path, dpi=200)
        except Exception:
            return None
        pages = []
        for image in images:
            try:
                pages.append(pytesseract.image_to_string(image, lang="deu+eng"))
            except Exception:
                pages.append("")
        if not any(p.strip() for p in pages):
            return None
        return SourceDocument(text="\n\n".join(pages), pages=pages)

    def _show_evidence_dialog(self):
        """Öffnet die Quellenbeleg-Prüfung für das aktuelle Ergebnis."""
        if not self.current_result:
            messagebox.showinfo("Kein Ergebnis",
                                "Bitte wählen Sie zuerst ein Ergebnis aus.")
            return
        from workspace_ui import EvidenceDialog
        source_name = ""
        if self.current_result.source_info:
            source_name = (self.current_result.source_info.file_name
                           or self.current_result.source_info.url or "")
        EvidenceDialog(
            self.window, self.current_result.content or "",
            source_loader=self._load_source_document,
            source_name=source_name,
        )

    def _edit_extracted_data(self):
        """Öffnet den Editor für die extrahierten strukturierten Daten."""
        if not self.current_result:
            messagebox.showinfo("Kein Ergebnis",
                                "Bitte wählen Sie zuerst ein Ergebnis aus.")
            return
        from workspace_ui import EditDataDialog
        EditDataDialog(
            self.window, self.results_manager, self.current_result.id,
            on_saved=self._reload_current_result,
        )

    def _show_chart_suggestions(self):
        """Zeigt begründete Diagrammvorschläge für die erste extrahierte Tabelle."""
        if not self.current_result:
            messagebox.showinfo("Kein Ergebnis",
                                "Bitte wählen Sie zuerst ein Ergebnis aus.")
            return
        tables = self.current_result.extracted_data.tables
        if not tables:
            messagebox.showinfo("Keine Tabelle",
                                "Das Ergebnis enthält keine extrahierte Tabelle.")
            return
        from workspace_ui import ChartSuggestionsDialog
        ChartSuggestionsDialog(
            self.window, tables[0],
            table_name=tables[0].title or "Tabelle 1",
        )

    def _check_for_updates(self, silent: bool = False):
        """Prüft im Hintergrund, ob eine neuere Release-Version existiert.

        silent=True (Start-Check): nur bei vorhandenem Update eine Meldung.
        """
        import threading

        def worker():
            from update_checker import check_for_update
            from main import __version__
            info = check_for_update(__version__)
            self.window.after(0, self._show_update_result, info, silent)

        threading.Thread(target=worker, daemon=True).start()

    def _show_update_result(self, info, silent: bool):
        """Zeigt das Ergebnis der Update-Prüfung an."""
        import webbrowser
        if not info.update_available:
            if not silent:
                if info.error:
                    messagebox.showinfo("Update-Prüfung", info.error)
                else:
                    messagebox.showinfo(
                        "Update-Prüfung",
                        f"Die App ist aktuell (Version {info.current_version}).")
            return

        from update_checker import pick_platform_asset
        asset = pick_platform_asset(info)

        dialog = tk.Toplevel(self.window)
        dialog.title("Update verfügbar")
        dialog.transient(self.window)
        dialog.resizable(False, False)
        frame = ttk.Frame(dialog, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(
            frame,
            text=f"Version {info.latest_version} ist verfügbar "
                 f"(installiert: {info.current_version}).",
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor=tk.W)
        if info.release_notes:
            notes = info.release_notes.strip()
            preview = notes[:800] + ("…" if len(notes) > 800 else "")
            note_box = scrolledtext.ScrolledText(frame, height=8, width=60,
                                                 wrap=tk.WORD)
            note_box.insert("1.0", preview)
            note_box.configure(state=tk.DISABLED)
            note_box.pack(fill=tk.BOTH, expand=True, pady=8)

        progress_var = tk.StringVar(value="")
        ttk.Label(frame, textvariable=progress_var).pack(anchor=tk.W)

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill=tk.X, pady=(10, 0))

        def open_page():
            webbrowser.open(info.release_url)
            dialog.destroy()

        def download():
            from update_checker import download_release_asset, open_in_file_manager
            import threading
            progress_var.set(f"Lade {asset['name']} herunter …")
            for widget in btn_row.winfo_children():
                widget.configure(state=tk.DISABLED)

            def on_progress(received, total):
                mb = received / 1_048_576
                text = (f"{mb:.1f} MB von {total / 1_048_576:.1f} MB"
                        if total else f"{mb:.1f} MB")
                self.window.after(0, progress_var.set, text)

            def worker():
                path = download_release_asset(asset, progress=on_progress)
                self.window.after(0, finish, path)

            def finish(path):
                if path:
                    progress_var.set(f"Gespeichert: {path}")
                    open_in_file_manager(path)
                else:
                    progress_var.set("Download fehlgeschlagen.")
                    for widget in btn_row.winfo_children():
                        widget.configure(state=tk.NORMAL)

            threading.Thread(target=worker, daemon=True).start()

        ttk.Button(btn_row, text="Release-Seite öffnen",
                   command=open_page).pack(side=tk.LEFT)
        if asset:
            ttk.Button(btn_row, text=f"Herunterladen ({asset['name']})",
                       command=download).pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_row, text="Schließen",
                   command=dialog.destroy).pack(side=tk.RIGHT)
        dialog.bind("<Escape>", lambda _e: dialog.destroy())

    def _playground_analyze(self, content, prompt, model):
        """Analyse-Funktion für den Prompt-Playground (läuft im Worker-Thread)."""
        from analysis import analyze_with_prompt
        return analyze_with_prompt(content, prompt, model=model)

    def _show_prompt_playground(self):
        """Öffnet den Prompt-Playground mit dem Inhalt des aktuellen Ergebnisses."""
        content = ""
        if self.current_result and self.current_result.content:
            content = self.current_result.content
        elif hasattr(self, "enhanced_input_tabs"):
            try:
                content = self.enhanced_input_tabs.get_current_content() or ""
            except Exception:
                content = ""
        if not content.strip():
            messagebox.showinfo(
                "Kein Inhalt",
                "Bitte laden Sie zuerst ein Ergebnis oder geben Sie Inhalt ein.")
            return
        from analysis import AVAILABLE_MODELS
        from workspace_ui import PromptPlaygroundDialog
        models = [m["id"] if isinstance(m, dict) else m for m in AVAILABLE_MODELS]
        PromptPlaygroundDialog(self.window, content, models,
                               self._playground_analyze)

    def _show_evaluation_dialog(self):
        """Öffnet die Evaluationssuite (gespeicherte Testfälle × Varianten)."""
        from analysis import analyze_with_prompt, get_model
        from evaluation import EvaluationStore
        from evaluation_ui import EvaluationDialog
        store = EvaluationStore(self.results_manager.db_path)
        models = [m["id"] if isinstance(m, dict) else m for m in AVAILABLE_MODELS]
        EvaluationDialog(
            self.window, store, models,
            analyze_fn=analyze_with_prompt,
            default_model=get_model(),
            privacy_check=self.privacy_check_enabled,
        )

    def _reload_current_result(self):
        """Lädt das aktuelle Ergebnis nach Bearbeitung/Rollback neu."""
        if not self.current_result:
            return
        reloaded = self.results_manager.load_result(self.current_result.id)
        if reloaded:
            self.current_result = reloaded
            self.results_display.display_content(reloaded.content, "markdown")
            self.results_browser.refresh_results()
            self.status_var.set("Ergebnis aktualisiert")

    # Override send_question to use enhanced processing
    def send_question(self):
        """Enhanced version of send_question that uses new processing pipeline."""
        try:
            # Try to get content from enhanced input tabs first
            if hasattr(self, 'enhanced_input_tabs') and hasattr(self.enhanced_input_tabs, 'get_current_content'):
                content = self.enhanced_input_tabs.get_current_content()
                if content:
                    # Enhanced tabs return just content, we need to determine source and type
                    analysis_type = self.enhanced_input_tabs.get_current_type() or "enhanced_analysis"
                    source_path = analysis_type
                    self._on_enhanced_analysis_requested(content, source_path, analysis_type)
                    return
            
            # Fallback to original method for backward compatibility
            if not super().send_question():
                return

            # Track the basic analysis step after a successful run.
            try:
                self.learning_path.record_event(LearningEventType.ANALYSIS_SUCCEEDED)
                self._update_learning_path_panel()
            except Exception:
                pass

        except Exception as e:
            if hasattr(self, 'error_handler'):
                error_msg = self.error_handler.create_user_friendly_message(
                    self.error_handler.handle_error(e, {"operation": "send_question"})
                )
                self._show_error(error_msg)
            else:
                # Fallback error handling
                messagebox.showerror("Fehler", f"Fehler bei der Analyse: {e}")
                self.status_var.set("Fehler bei der Analyse")
            
    # Maintain backward compatibility for existing methods
    def save_note(self):
        """Enhanced save_note that also saves to results manager."""
        # Leer-Hinweis ist kein speicherbarer Inhalt
        if getattr(getattr(self, "results_display", None),
                   "_showing_placeholder", False):
            self.notes = []
            self.status_var.set("Kein Text zum Speichern gefunden")
            return

        # Call original save_note
        super().save_note()
        
        # Also save current result if available
        if self.current_result:
            try:
                result_id = self.results_manager.save_result(
                    self.current_result,
                    f"Analyse vom {self.current_result.created_at.strftime('%d.%m.%Y %H:%M')}"
                )
                self.learning_path.record_event(LearningEventType.RESULT_SAVED)
                self._update_learning_path_panel()
                self.status_var.set(f"Ergebnis gespeichert (ID: {result_id[:8]}...)")
            except Exception as e:
                self.status_var.set("Fehler beim Speichern des Ergebnisses")

    # ------------------------------------------------------------------
    # Onboarding, learning path, and prompt library integration
    # ------------------------------------------------------------------

    def _maybe_show_onboarding(self):
        """Show the onboarding dialog if the user has not completed it yet."""
        profile = self.user_profile_manager.profile
        if profile.onboarding_completed or profile.onboarding_skipped:
            return
        self._show_onboarding()

    def _maybe_check_updates(self):
        """Start-Update-Check, nur wenn der Nutzer ihn explizit aktiviert hat."""
        if self.user_profile_manager.get_setting("update_check_on_start", False):
            self._check_for_updates(silent=True)

    def _show_onboarding(self):
        """Display a multi-step onboarding wizard."""
        profile = self.user_profile_manager.profile
        dialog = tk.Toplevel(self.window)
        dialog.title("Willkommen beim KI Analysetool")
        dialog.geometry("650x420")
        dialog.resizable(False, False)
        dialog.transient(self.window)
        dialog.grab_set()

        current_step = {"index": 0}
        steps = [
            {
                "title": "Willkommen!",
                "text": (
                    "Das KI Analysetool hilft dir, Texte, Webseiten, YouTube-Videos, PDFs, "
                    "Excel-Dateien und Bilder mit KI zu analysieren.\n\n"
                    "In den nächsten Seiten zeigen wir dir die Grundlagen."
                )
            },
            {
                "title": "So funktioniert es",
                "text": (
                    "1. Wähle links eine Quelle aus (Text, Webseite, PDF, …).\n"
                    "2. Gib oben rechts optional einen eigenen Prompt ein oder wähle einen Analyse-Typ.\n"
                    "3. Klicke auf 'Analyse starten' (oder drücke Strg + Enter).\n"
                    "4. Nutze rechts Folgeaktionen wie Zusammenfassen, Vertiefen oder Übersetzen."
                )
            },
            {
                "title": "Modus wählen",
                "text": (
                    "Wähle deinen Erfahrungsgrad. Du kannst ihn später jederzeit in den "
                    "Einstellungen ändern."
                ),
                "show_mode": True
            },
            {
                "title": "Bereit!",
                "text": (
                    "Starte direkt mit einem Beispiel oder schließe das Onboarding ab. "
                    "Wenn du Hilfe brauchst, findest du im Menü 'Hilfe' die Dokumentation."
                ),
                "show_example": True
            }
        ]

        content_frame = ttk.Frame(dialog, padding=20)
        content_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(content_frame, text="", font=("Segoe UI", 14, "bold"))
        title_label.pack(anchor=tk.W, pady=(0, 10))

        text_label = ttk.Label(content_frame, text="", wraplength=600, justify=tk.LEFT)
        text_label.pack(anchor=tk.W, fill=tk.BOTH, expand=True)

        mode_var = tk.StringVar(value=profile.experience_level)
        mode_frame = ttk.Frame(content_frame)
        ttk.Radiobutton(mode_frame, text="Anfänger – mehr Erklärungen und Tipps",
                        variable=mode_var, value="beginner").pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(mode_frame, text="Fortgeschritten – ausgewogener Modus",
                        variable=mode_var, value="intermediate").pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(mode_frame, text="Experte – minimale Hilfe, volle Funktionen",
                        variable=mode_var, value="expert").pack(anchor=tk.W, pady=2)

        btn_frame = ttk.Frame(dialog, padding=15)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

        back_btn = ttk.Button(btn_frame, text="Zurück", state=tk.DISABLED)
        back_btn.pack(side=tk.LEFT)

        example_btn = ttk.Button(btn_frame, text="Beispieltext einsetzen")

        skip_btn = ttk.Button(btn_frame, text="Überspringen")
        skip_btn.pack(side=tk.RIGHT, padx=(5, 0))

        next_btn = ttk.Button(btn_frame, text="Weiter")
        next_btn.pack(side=tk.RIGHT)

        def render():
            step = steps[current_step["index"]]
            title_label.config(text=step["title"])
            text_label.config(text=step["text"])

            if step.get("show_mode"):
                mode_frame.pack(after=text_label, anchor=tk.W, pady=(15, 0), fill=tk.X)
            else:
                mode_frame.pack_forget()

            if step.get("show_example"):
                example_btn.pack(side=tk.LEFT, padx=(10, 0))
            else:
                example_btn.pack_forget()

            back_btn.config(state=tk.NORMAL if current_step["index"] > 0 else tk.DISABLED)
            next_btn.config(text="Fertig" if current_step["index"] == len(steps) - 1 else "Weiter")

        def next_action():
            if current_step["index"] < len(steps) - 1:
                current_step["index"] += 1
                render()
            else:
                finish()

        def back_action():
            if current_step["index"] > 0:
                current_step["index"] -= 1
                render()

        def finish():
            self.user_profile_manager.set_experience_level(mode_var.get())
            if mode_var.get() != "expert":
                self.user_profile_manager.set_learning_panel_visibility(True)
            self.user_profile_manager.complete_onboarding()
            self._apply_experience_level()
            self._update_learning_path_panel()
            dialog.destroy()

        def skip():
            self.user_profile_manager.set_experience_level(mode_var.get())
            if mode_var.get() != "expert":
                self.user_profile_manager.set_learning_panel_visibility(True)
            self.user_profile_manager.skip_onboarding()
            self._apply_experience_level()
            dialog.destroy()

        def load_example():
            text_tab = self.enhanced_input_tabs.tab_frames.get("text")
            if text_tab:
                self.input_tabs.select(text_tab)
                self.enhanced_input_tabs.text_input.delete(1.0, tk.END)
                self.enhanced_input_tabs.text_input.insert(
                    1.0,
                    "Die Digitalisierung verändert die Arbeitswelt. KI und Automatisierung "
                    "schaffen Effizienzgewinne, erfordern aber neue Kompetenzen."
                )
                self.combobox.set("Zusammenfassung")
            finish()
            self.status_var.set("Beispiel vorbereitet – klicken Sie auf 'Analyse starten'.")

        next_btn.config(command=next_action)
        back_btn.config(command=back_action)
        example_btn.config(command=load_example)
        skip_btn.config(command=skip)

        dialog.protocol("WM_DELETE_WINDOW", skip)
        render()

    def _apply_experience_level(self):
        """Adjust UI elements based on the user's experience level."""
        level = self.user_profile_manager.profile.experience_level
        if level == "beginner":
            # Show learning panel and keep tooltips visible.
            self.analysis_frame.configure(padding=12)
            self.question_text.configure(height=6)
            if self.user_profile_manager.profile.show_learning_panel:
                self._show_learning_path_panel()
            else:
                self._hide_learning_path_panel()
        elif level == "intermediate":
            self.analysis_frame.configure(padding=10)
            self.question_text.configure(height=4)
            if self.user_profile_manager.profile.show_learning_panel:
                self._show_learning_path_panel()
            else:
                self._hide_learning_path_panel()
        else:  # expert
            self.analysis_frame.configure(padding=5)
            self.question_text.configure(height=3)
            self._hide_learning_path_panel()

    def _setup_learning_path_panel(self):
        """Create the collapsible learning path panel on the left side."""
        self.learning_path_frame = ttk.LabelFrame(self.main_frame, text="Lernpfad", padding=10)

        self.learning_path_header = ttk.Frame(self.learning_path_frame)
        self.learning_path_header.pack(fill=tk.X)

        self.learning_progress_var = tk.StringVar(value="")
        ttk.Label(self.learning_path_header, textvariable=self.learning_progress_var,
                  font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)

        self.learning_toggle_btn = ttk.Button(
            self.learning_path_header, text="Später erinnern",
            command=self._hide_learning_path_panel
        )
        self.learning_toggle_btn.pack(side=tk.RIGHT)
        ttk.Button(
            self.learning_path_header,
            text="Zurücksetzen",
            command=self._reset_learning_path
        ).pack(side=tk.RIGHT, padx=(0, 5))

        self.learning_steps_container = ttk.Frame(self.learning_path_frame)
        self.learning_steps_container.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.learning_step_widgets = []
        self._update_learning_path_panel()

        # Place the panel above the main content frame (which is currently packed).
        profile = self.user_profile_manager.profile
        if profile.show_learning_panel and profile.experience_level != "expert":
            self.learning_path_frame.pack(fill=tk.X, pady=(0, 10), before=self.content_frame)

        # Hide for expert users initially, but keep widget available.
        if profile.experience_level == "expert":
            self.learning_path_frame.pack_forget()

    def _show_learning_path_panel(self):
        """Show the learning path panel if not already visible."""
        try:
            self.learning_path_frame.pack(fill=tk.X, pady=(0, 10), before=self.content_frame)
        except tk.TclError:
            pass
        self.user_profile_manager.set_learning_panel_visibility(True)
        self._update_learning_path_panel()

    def _hide_learning_path_panel(self):
        """Hide the learning path panel and remember the preference."""
        try:
            self.learning_path_frame.pack_forget()
        except tk.TclError:
            pass
        self.user_profile_manager.set_learning_panel_visibility(False)

    def _toggle_learning_path_panel(self):
        """Toggle the visibility of the learning path panel."""
        if self.learning_path_frame.winfo_ismapped():
            self._hide_learning_path_panel()
        else:
            self._show_learning_path_panel()

    def _reset_learning_path(self):
        if messagebox.askyesno(
            "Lernpfad zurücksetzen",
            "Möchten Sie den gesamten Lernfortschritt zurücksetzen?"
        ):
            self.learning_path.reset()
            self._update_learning_path_panel()
            self.status_var.set("Lernpfad zurückgesetzt")

    def _update_learning_path_panel(self):
        """Refresh the learning path checklist."""
        # Clear existing widgets
        for widget in self.learning_steps_container.winfo_children():
            widget.destroy()
        self.learning_step_widgets.clear()

        progress = self.learning_path.progress()
        self.learning_progress_var.set(
            f"Fortschritt: {progress['completed']}/{progress['total']} ({progress['percent']}%)"
        )

        if progress["all_done"]:
            ttk.Label(self.learning_steps_container,
                      text="Alle Lernpfad-Schritte abgeschlossen!").pack(anchor=tk.W, pady=5)
            return

        current_step = progress["current_step"]
        step_frame = ttk.Frame(self.learning_steps_container)
        step_frame.pack(fill=tk.X, pady=2)
        text_frame = ttk.Frame(step_frame)
        text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(
            text_frame,
            text=f"Nächster Schritt: {current_step.title}",
            font=("Segoe UI", 9, "bold")
        ).pack(anchor=tk.W)
        ttk.Label(
            text_frame,
            text=current_step.description,
            wraplength=700
        ).pack(anchor=tk.W)
        ttk.Button(
            step_frame,
            text="Anleitung anzeigen",
            command=lambda: self._run_tutorial_for_step(current_step.id)
        ).pack(side=tk.RIGHT)
        # Only show the next open step in compact mode

    def _run_tutorial_for_step(self, step_id: str):
        """Launch a tutorial overlay for the given learning step."""
        step = self.learning_path.get_step(step_id)
        if not step:
            return

        steps = []
        # Determine relevant target widgets based on step id.
        targets = {
            "first_analysis": getattr(self, "question_text", None),
            "try_follow_up": getattr(self, "action_buttons", None),
            "analyze_file": getattr(self, "enhanced_input_tabs", None),
            "extract_data": getattr(self, "action_buttons", None),
            "visualize": getattr(self, "viz_frame", None),
            "export_excel": getattr(self, "export_frame", None),
            "save_result": getattr(self, "results_browser", None),
            "compare_results": getattr(self, "results_browser", None),
            "custom_prompt": getattr(self, "question_text", None),
        }
        target = targets.get(step_id)
        if target is not None:
            steps.append({
                "target": target,
                "title": step.title,
                "text": step.help_text
            })

        def on_finish():
            self.status_var.set(f"Anleitung beendet: {step.title}. Führe die Aktion jetzt selbst aus.")

        if steps:
            overlay = TutorialOverlay(self.window, steps=steps, on_finish=on_finish)
            overlay.start()
        else:
            messagebox.showinfo(step.title, step.help_text)

    def _show_experience_selector(self):
        """Open a dialog to switch between experience levels."""
        dialog = tk.Toplevel(self.window)
        dialog.title("Erfahrungsgrad")
        dialog.geometry("400x250")
        dialog.transient(self.window)
        dialog.grab_set()

        ttk.Label(dialog, text="Erfahrungsgrad wählen",
                  font=("Segoe UI", 12, "bold")).pack(pady=15)

        mode_var = tk.StringVar(value=self.user_profile_manager.profile.experience_level)
        ttk.Radiobutton(dialog, text="Anfänger – mehr Erklärungen und Tipps",
                        variable=mode_var, value="beginner").pack(anchor=tk.W, padx=30, pady=3)
        ttk.Radiobutton(dialog, text="Fortgeschritten – ausgewogener Modus",
                        variable=mode_var, value="intermediate").pack(anchor=tk.W, padx=30, pady=3)
        ttk.Radiobutton(dialog, text="Experte – minimale Hilfe, volle Funktionen",
                        variable=mode_var, value="expert").pack(anchor=tk.W, padx=30, pady=3)

        def apply():
            self.user_profile_manager.set_experience_level(mode_var.get())
            if mode_var.get() != "expert":
                self.user_profile_manager.set_learning_panel_visibility(True)
            self._apply_experience_level()
            self.status_var.set(f"Erfahrungsgrad geändert: {mode_var.get()}")
            dialog.destroy()

        ttk.Button(dialog, text="Übernehmen", command=apply).pack(pady=20)

    def _show_prompt_library(self):
        """Open a dialog with reusable prompt templates."""
        dialog = tk.Toplevel(self.window)
        dialog.title("Prompt-Vorlagen")
        dialog.geometry("600x500")
        dialog.transient(self.window)
        dialog.grab_set()

        ttk.Label(dialog, text="Wähle eine Prompt-Vorlage",
                  font=("Segoe UI", 12, "bold")).pack(pady=10)

        level = self.user_profile_manager.profile.experience_level
        templates = self.prompt_library.for_difficulty(level)

        search_frame = ttk.Frame(dialog, padding=(10, 0))
        search_frame.pack(fill=tk.X)
        ttk.Label(search_frame, text="Suchen:").pack(side=tk.LEFT)
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        # Group by category
        container = ttk.Frame(dialog, padding=10)
        container.pack(fill=tk.BOTH, expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        tree = ttk.Treeview(container, columns=("title", "description"), show="headings", height=15)
        tree.heading("title", text="Titel")
        tree.heading("description", text="Beschreibung")
        tree.column("title", width=180)
        tree.column("description", width=350)
        tree.grid(row=0, column=0, sticky=tk.NSEW)

        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=tree.yview)
        scrollbar.grid(row=0, column=1, sticky=tk.NS)
        tree.config(yscrollcommand=scrollbar.set)

        # Populate with categories as parents and templates as children
        def populate_templates(*_args):
            tree.delete(*tree.get_children())
            query = search_var.get().strip().lower()
            categories = {}
            for template in templates:
                searchable = " ".join([
                    template.category,
                    template.title,
                    template.description,
                    *template.tags
                ]).lower()
                if query and query not in searchable:
                    continue
                categories.setdefault(template.category, []).append(template)
            for category, items in categories.items():
                parent = tree.insert("", tk.END, text=category, values=(category, ""), open=True)
                for template in items:
                    tree.insert(parent, tk.END, values=(template.title, template.description), tags=(template.id,))

        search_var.trace_add("write", populate_templates)
        populate_templates()
        search_entry.focus_set()

        def use_template():
            selected = tree.selection()
            if not selected:
                return
            item = tree.item(selected[0])
            template_id = item.get("tags", [None])[0]
            if not template_id:
                return
            try:
                template = self.prompt_library.by_id(template_id)
                self.question_text.delete(1.0, tk.END)
                self.question_text.insert(1.0, template.prompt)
                self.combobox.set("Prompt senden")
                dialog.destroy()
                self.status_var.set(f"Prompt-Vorlage geladen: {template.title}")
            except KeyError:
                pass

        ttk.Button(dialog, text="Verwenden", command=use_template).pack(pady=10)


def create_enhanced_gui(window):
    """Factory function to create enhanced GUI."""
    return EnhancedGui(window)


# Backward compatibility: allow importing as Gui
Gui = EnhancedGui