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
from analysis import (AnalysisFailure, analyze_text, extract_transkript,
                     extract_text_from_website, text_extraction_youtube_website,
                     real_ai_analyse_fortext, real_ai_analyse_forpdf,
                     get_usage_stats, reset_usage_stats)
from config import check_api_key_exists, save_api_key, get_api_key
from markdown_formatter import configure_markdown_tags, markdown_to_tkinter_text
from user_profile import UserProfileManager
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
        
        # Current result tracking
        self.current_result: Optional[ProcessedResult] = None
        self.processing_thread: Optional[threading.Thread] = None

        # Thread-safe queue for scheduling UI updates from worker threads
        self._ui_queue: queue.Queue = queue.Queue()

        # User profile, learning path, and prompt library
        self.user_profile_manager = UserProfileManager()
        self.learning_path = LearningPath(profile_manager=self.user_profile_manager)
        self.prompt_library = PromptLibrary()

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
        """Registriert globale Tastatur-Shortcuts."""
        self.window.bind_all("<Control-Return>", lambda e: self.send_question())
        self.window.bind_all("<Control-s>", lambda e: self.save_note())
        self.window.bind_all("<Control-e>", lambda e: self._export_content_as_pdf(
            self.current_result.content if self.current_result
            else self.output_text.get(1.0, tk.END).strip()
        ))
        self.window.bind_all("<Control-f>", lambda e: self._show_favorites())

    def _setup_enhanced_components(self):
        """Set up the enhanced components in the existing GUI structure."""
        # Replace the existing input tabs with enhanced version
        self._enhance_input_tabs()

        # Enhance the output area with new display components
        self._enhance_output_area()

        # Add learning path panel for beginners/intermediate users
        self._setup_learning_path_panel()

        # Add new menu items and toolbar
        self._add_enhanced_menu()

        # Show onboarding for first-time users
        self.window.after(100, self._maybe_show_onboarding)
        
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
        # Create menu bar if it doesn't exist
        if not hasattr(self.window, 'menubar'):
            self.window.menubar = tk.Menu(self.window)
            self.window.config(menu=self.window.menubar)
            
        # Add enhanced features menu
        self.enhanced_menu = tk.Menu(self.window.menubar, tearoff=0)
        self.window.menubar.add_cascade(label="Erweiterte Funktionen", menu=self.enhanced_menu)
        
        self.enhanced_menu.add_command(
            label="Ergebnisse verwalten",
            command=self._show_results_manager
        )
        self.enhanced_menu.add_separator()
        self.enhanced_menu.add_command(
            label="Daten exportieren",
            command=self._show_export_dialog
        )
        self.enhanced_menu.add_command(
            label="Visualisierung erstellen",
            command=self._show_visualization_dialog
        )
        self.enhanced_menu.add_separator()
        self.enhanced_menu.add_command(
            label="Analyse-Historie anzeigen",
            command=self._show_analysis_history
        )
        self.enhanced_menu.add_command(
            label="Token- & Kosten-Übersicht",
            command=self._show_usage_stats
        )
        self.enhanced_menu.add_separator()
        self.enhanced_menu.add_command(
            label="Backup erstellen",
            command=self._create_backup
        )
        self.enhanced_menu.add_command(
            label="Backup wiederherstellen",
            command=self._restore_backup
        )
        self.enhanced_menu.add_separator()
        self.enhanced_menu.add_command(
            label="PDF-Report erstellen",
            command=self._generate_pdf_report
        )
        self.enhanced_menu.add_command(
            label="Batch-Export (ZIP)",
            command=self._batch_export
        )
        self.enhanced_menu.add_command(
            label="Ergebnisse vergleichen",
            command=self._compare_results
        )
        self.enhanced_menu.add_command(
            label="Tags verwalten",
            command=self._manage_tags
        )
        self.enhanced_menu.add_command(
            label="Favoriten anzeigen",
            command=self._show_favorites
        )
        self.enhanced_menu.add_command(
            label="Einstellungen",
            command=self._show_settings_dialog
        )
        
        # Add help menu
        self.help_menu = tk.Menu(self.window.menubar, tearoff=0)
        self.window.menubar.add_cascade(label="Hilfe", menu=self.help_menu)
        
        self.help_menu.add_command(
            label="Dokumentation anzeigen",
            command=lambda: show_help_window(self.window)
        )
        self.help_menu.add_command(
            label="Hilfe: Erste Schritte",
            command=lambda: show_help_window(self.window, anchor="Schnellstart für Anfänger")
        )

        # Add experience level selector
        if not hasattr(self.window, 'menubar'):
            self.window.menubar = tk.Menu(self.window)
            self.window.config(menu=self.window.menubar)
        self.view_menu = tk.Menu(self.window.menubar, tearoff=0)
        self.window.menubar.add_cascade(label="Ansicht", menu=self.view_menu)
        self.view_menu.add_command(
            label="Erfahrungsgrad ändern",
            command=self._show_experience_selector
        )
        self.view_menu.add_command(
            label="Lernpfad anzeigen/ausblenden",
            command=self._toggle_learning_path_panel
        )

        # Add prompt library button near the prompt field (reuses existing prompt frame)
        prompt_btn_frame = ttk.Frame(self.analysis_frame)
        prompt_btn_frame.grid(row=0, column=1, sticky=tk.E, pady=(0, 5))
        ttk.Button(prompt_btn_frame, text="Vorlagen",
                   command=self._show_prompt_library).pack()

        # Add progress indicator to status bar
        self.progress_indicator = ProgressIndicator(self.main_frame)
        
    def _on_status_update(self, message: str):
        """Handle status updates from enhanced components."""
        self.status_var.set(message)
        
    def _on_file_selected(self, file_paths: List[str], file_type: str):
        """Handle file selection from enhanced input tabs."""
        self.status_var.set(f"{len(file_paths)} Datei(en) ausgewählt: {file_type}")
        
    def _on_enhanced_analysis_requested(self, content: str, source_path: str, analysis_type: str):
        """Handle analysis request from enhanced input tabs."""
        # Read prompt values on the main thread before handing off to worker
        custom_prompt = self.question_text.get(1.0, tk.END).strip()
        predefined_prompt = None
        if not custom_prompt:
            predefined_prompt = self.get_prompt(content)

        # Start analysis in background thread
        self.processing_thread = threading.Thread(
            target=self._process_enhanced_analysis,
            args=(content, source_path, analysis_type, custom_prompt, predefined_prompt)
        )
        self.processing_thread.daemon = True
        self.processing_thread.start()

    def _process_enhanced_analysis(self, content: str, source_path: str, analysis_type: str,
                                   custom_prompt: str, predefined_prompt: Optional[str]):
        """Process analysis with enhanced features in background thread."""
        try:
            # Show progress
            self._safe_after(0, self._safe_progress_start, "Analyse wird durchgeführt...")

            if custom_prompt:
                # Use custom prompt
                combined_prompt = f"{custom_prompt}\n\nInhalt: {content}"
                outcome = analyze_text(combined_prompt)
            else:
                # Use predefined analysis type
                outcome = analyze_text(predefined_prompt)

            # Process result through enhanced processor
            processed_result = self.results_processor.process_analysis_outcome(
                outcome,
                source_path,
                analysis_type
            )

            # Update learning path for file-based analyses
            if custom_prompt:
                self.learning_path.record_event("custom_prompt_succeeded")
            if analysis_type in ("file_analysis", "pdf", "excel", "csv", "image", "multi_file", "enhanced_analysis"):
                try:
                    self.learning_path.record_event("file_analyzed")
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
            self.learning_path.record_event("analysis_succeeded")
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
                content = self.output_text.get(1.0, tk.END).strip()

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
            event_name = "data_extracted" if action_name == "extract_data" else "follow_up_succeeded"
            self.learning_path.record_event(event_name)
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
        self.learning_path.record_event("chart_created")
        self._update_learning_path_panel()
        chart_name = visualization.file_path or visualization.chart_type.value
        self.status_var.set(f"Diagramm erstellt: {os.path.basename(chart_name)}")
        
    def _on_export_completed(self, export_path: str):
        """Handle export completion."""
        self.learning_path.record_event("excel_exported")
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

        rows = [
            ("Aktuelles Modell", stats.get("model", "—")),
            ("Verbrauchte Tokens", f"{stats.get('total_tokens', 0):,}"),
            ("Geschätzte Kosten", f"${stats.get('total_cost', 0.0):.4f}"),
        ]
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
            self.backup_manager.restore_backup(backup_file, overwrite=True)
            self.results_browser.refresh_results()
            messagebox.showinfo("Restore erfolgreich",
                                f"Backup wurde wiederhergestellt aus:\n{backup_file}")
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
        dialog.geometry("420x360")
        dialog.transient(self.window)
        dialog.grab_set()

        ttk.Label(dialog, text="Erweiterte Einstellungen",
                  font=("Segoe UI", 12, "bold")).pack(pady=10)

        auto_save_var = tk.BooleanVar(value=self.auto_save_enabled)
        auto_viz_var = tk.BooleanVar(value=self.auto_viz_enabled)

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

        def apply_and_close():
            self.auto_save_enabled = auto_save_var.get()
            self.auto_viz_enabled = auto_viz_var.get()
            self.status_var.set(
                f"Einstellungen gespeichert (Auto-Save: {'an' if self.auto_save_enabled else 'aus'})"
            )
            dialog.destroy()

        ttk.Button(dialog, text="Übernehmen", command=apply_and_close).pack(pady=10)
        ttk.Button(dialog, text="Abbrechen", command=dialog.destroy).pack()
        
    # Override send_question to use enhanced processing
    def send_question(self):
        """Enhanced version of send_question that uses new processing pipeline."""
        try:
            # Try to get content from enhanced input tabs first
            if hasattr(self, 'enhanced_input_tabs') and hasattr(self.enhanced_input_tabs, 'get_current_content'):
                content = self.enhanced_input_tabs.get_current_content()
                if content:
                    # Enhanced tabs return just content, we need to determine source and type
                    source_path = "enhanced_input"
                    analysis_type = "enhanced_analysis"
                    self._on_enhanced_analysis_requested(content, source_path, analysis_type)
                    return
            
            # Fallback to original method for backward compatibility
            if not super().send_question():
                return

            # Track the basic analysis step after a successful run.
            try:
                self.learning_path.record_event("analysis_succeeded")
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
        # Call original save_note
        super().save_note()
        
        # Also save current result if available
        if self.current_result:
            try:
                result_id = self.results_manager.save_result(
                    self.current_result,
                    f"Analyse vom {self.current_result.created_at.strftime('%d.%m.%Y %H:%M')}"
                )
                self.learning_path.record_event("result_saved")
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
        if profile.onboarding_completed:
            return
        self._show_onboarding()

    def _show_onboarding(self):
        """Display a multi-step onboarding wizard."""
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
                    "3. Klicke auf 'Frage senden' (oder drücke Strg + Enter).\n"
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
                    "Wenn du Hilfe brauchst, findest du im Menü 'Hilfe' die Dokumentation.\n\n"
                    "Viel Erfolg beim Analysieren!"
                )
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
            self.user_profile_manager.complete_onboarding()
            self._apply_experience_level()
            self._update_learning_path_panel()
            dialog.destroy()

        next_btn.config(command=next_action)
        back_btn.config(command=back_action)
        skip_btn.config(command=finish)

        dialog.protocol("WM_DELETE_WINDOW", finish)
        render()

    def _apply_experience_level(self):
        """Adjust UI elements based on the user's experience level."""
        level = self.user_profile_manager.profile.experience_level
        if level == "beginner":
            # Show learning panel and keep tooltips visible.
            self._show_learning_path_panel()
        elif level == "intermediate":
            self._show_learning_path_panel()
        else:  # expert
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
            self.learning_path_header, text="Ausblenden",
            command=self._hide_learning_path_panel
        )
        self.learning_toggle_btn.pack(side=tk.RIGHT)

        self.learning_steps_container = ttk.Frame(self.learning_path_frame)
        self.learning_steps_container.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.learning_step_widgets = []
        self._update_learning_path_panel()

        # Place the panel above the main content frame (which is currently packed).
        self.learning_path_frame.pack(fill=tk.X, pady=(0, 10), before=self.content_frame)

        # Hide for expert users initially, but keep widget available.
        if self.user_profile_manager.profile.experience_level == "expert":
            self.learning_path_frame.pack_forget()

    def _show_learning_path_panel(self):
        """Show the learning path panel if not already visible."""
        try:
            self.learning_path_frame.pack(fill=tk.X, pady=(0, 10), before=self.content_frame)
        except tk.TclError:
            pass
        self._update_learning_path_panel()

    def _hide_learning_path_panel(self):
        """Hide the learning path panel and remember the preference."""
        try:
            self.learning_path_frame.pack_forget()
        except tk.TclError:
            pass

    def _toggle_learning_path_panel(self):
        """Toggle the visibility of the learning path panel."""
        if self.learning_path_frame.winfo_ismapped():
            self._hide_learning_path_panel()
        else:
            self._show_learning_path_panel()

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

        for item in self.learning_path.to_ui_items():
            step_frame = ttk.Frame(self.learning_steps_container)
            step_frame.pack(fill=tk.X, pady=2)

            state_text = "✓" if item["completed"] else "○"
            label = ttk.Label(step_frame, text=f"{state_text} {item['title']}")
            label.pack(side=tk.LEFT)

            if not item["completed"]:
                btn = ttk.Button(
                    step_frame, text="Zeige mir wie",
                    command=lambda i=item: self._run_tutorial_for_step(i["id"])
                )
                btn.pack(side=tk.RIGHT)
                break  # Only show the next open step in compact mode

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

        # Group by category
        categories = {}
        for template in templates:
            categories.setdefault(template.category, []).append(template)

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
        for category, items in categories.items():
            parent = tree.insert("", tk.END, text=category, values=(category, ""), open=True)
            for template in items:
                tree.insert(parent, tk.END, values=(template.title, template.description), tags=(template.id,))

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