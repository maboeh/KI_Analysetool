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
from typing import Optional, List, Dict, Any

# Import existing components
from Gui import Gui as BaseGui
from analysis import (extract_transkript, extract_text_from_website,
                     text_extraction_youtube_website, real_ai_analyse_fortext,
                     real_ai_analyse_forpdf)
from config import check_api_key_exists, save_api_key, get_api_key
from markdown_formatter import configure_markdown_tags, markdown_to_tkinter_text

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
    from data_models import ProcessedResult
    from help_tooltip import show_help_window, add_help_indicator
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
        
        # Current result tracking
        self.current_result: Optional[ProcessedResult] = None
        self.processing_thread: Optional[threading.Thread] = None
        
        # Initialize base GUI
        super().__init__(window)
        
        # Add enhanced components after base initialization
        self._setup_enhanced_components()
        
    def _setup_enhanced_components(self):
        """Set up the enhanced components in the existing GUI structure."""
        # Replace the existing input tabs with enhanced version
        self._enhance_input_tabs()
        
        # Enhance the output area with new display components
        self._enhance_output_area()
        
        # Add new menu items and toolbar
        self._add_enhanced_menu()
        
    def _enhance_input_tabs(self):
        """Replace existing input tabs with enhanced version supporting more file types."""
        # Remove existing input tabs
        self.input_tabs.destroy()
        
        # Create new notebook for enhanced tabs
        self.input_tabs = ttk.Notebook(self.sources_frame)
        self.input_tabs.grid(row=0, column=0, sticky=tk.W + tk.E)
        
        # Create enhanced input tabs
        self.enhanced_input_tabs = ExtendedInputTabs(
            self.input_tabs,
            status_callback=self._on_status_update
        )
        
        # Keep reference to the notebook for backward compatibility
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
        
        # Enhanced results display widget (left side)
        self.results_display = ResultsDisplayWidget(self.text_results_frame)
        self.results_display.grid(row=0, column=0, sticky=tk.W + tk.E + tk.N + tk.S, padx=(5, 0), pady=5)
        
        # Action buttons frame (right side)
        self.action_buttons = ActionButtonsFrame(
            self.text_results_frame,
            on_action_callback=self._handle_action_button
        )
        self.action_buttons.grid(row=0, column=1, sticky=tk.N + tk.S + tk.E + tk.W, padx=(5, 5), pady=5)
        
        # Move original note buttons (Notiz exportieren, In Zwischenablage) into the right column
        # below the action buttons
        if hasattr(self, 'note_buttons_frame'):
            self.note_buttons_frame.grid_forget()
            self.note_buttons_frame.grid(row=1, column=1, sticky=tk.EW, padx=(5, 5), pady=(0, 5))
            self.text_results_frame.rowconfigure(1, weight=0)
        
        # Visualization tab
        self.viz_frame = ttk.Frame(self.result_notebook)
        self.result_notebook.add(self.viz_frame, text="Visualisierung")
        
        self.visualization_panel = DataVisualizationPanel(self.viz_frame)
        
        # Add help indicator for visualization tab
        viz_help_frame = ttk.Frame(self.viz_frame)
        viz_help_frame.pack(fill=tk.X, padx=5, pady=2)
        add_help_indicator(viz_help_frame,
                          "Hier können Sie Diagramme und Visualisierungen aus den extrahierten Daten erstellen. "
                          "Wählen Sie den Diagrammtyp, passen Sie Titel und Achsen an und exportieren Sie als PNG/PDF/SVG.")
        
        # Data export tab
        self.export_frame = ttk.Frame(self.result_notebook)
        self.result_notebook.add(self.export_frame, text="Datenexport")
        
        self.excel_export_ui = ExcelExportUI(self.export_frame)
        
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
        
        self.results_browser = ResultsBrowser(self.browser_frame, self.results_manager)
        
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
        # Start analysis in background thread
        self.processing_thread = threading.Thread(
            target=self._process_enhanced_analysis,
            args=(content, source_path, analysis_type)
        )
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
    def _process_enhanced_analysis(self, content: str, source_path: str, analysis_type: str):
        """Process analysis with enhanced features in background thread."""
        try:
            # Show progress
            self.window.after(0, lambda: self.progress_indicator.start("Analyse wird durchgeführt..."))
            
            # Get custom prompt if provided
            custom_prompt = self.question_text.get(1.0, tk.END).strip()
            if custom_prompt:
                # Use custom prompt
                combined_prompt = f"{custom_prompt}\n\nInhalt: {content}"
                ai_result = real_ai_analyse_fortext(combined_prompt)
            else:
                # Use predefined analysis type
                prompt = self.get_prompt(content)
                ai_result = real_ai_analyse_fortext(prompt)
            
            # Process result through enhanced processor
            processed_result = self.results_processor.process_analysis_result(
                ai_result,
                source_path,
                analysis_type
            )
            
            # Update UI in main thread
            self.window.after(0, lambda: self._display_enhanced_result(processed_result))
            
        except Exception as e:
            error_msg = self.error_handler.create_user_friendly_message(
                self.error_handler.handle_error(e, {"operation": "analysis"})
            )
            self.window.after(0, lambda: self._show_error(error_msg))
        finally:
            self.window.after(0, lambda: self.progress_indicator.stop())
            
    def _display_enhanced_result(self, result: ProcessedResult):
        """Display enhanced analysis result."""
        self.current_result = result
        
        # Update text display
        self.results_display.display_result(result)
        
        # Update action buttons
        self.action_buttons.update_actions(result.follow_up_actions)
        self.action_buttons.update_content(result.content, "text")
        
        # Update visualization panel
        if result.extracted_data:
            self.visualization_panel.update_data(result.extracted_data)
            
        # Update export UI
        self.excel_export_ui.update_data(result.extracted_data)
        
        # Refresh results browser
        self.results_browser.refresh_results()
        
        # Update status
        self.status_var.set("Analyse abgeschlossen - Erweiterte Funktionen verfügbar")

    def _handle_action_button(self, action_name: str, content: str, content_type: str):
        """Handle action button click from the action buttons frame."""
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
        
        if action_name == "extract_data":
            prompt = f"Extrahiere alle strukturierten Daten (Zahlen, Datumsangaben, Namen, Orte, Organisationen) aus folgendem Text und stelle sie tabellarisch dar:\n\n{content}"
        elif action_name == "find_similar":
            prompt = f"Finde und beschreibe ähnliche Inhalte, Themen oder Konzepte wie in folgendem Text:\n\n{content}"
        elif action_name == "add_tags":
            prompt = f"Extrahiere die wichtigsten Tags/Schlüsselwörter aus folgendem Text und gib sie als kommagetrennte Liste aus:\n\n{content}"
        else:
            # Build prompt based on action
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

    def _export_content_as_pdf(self, content: str):
        """Export content as a PDF file."""
        from tkinter import filedialog as fd
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Spacer, Paragraph
        from reportlab.platypus import Paragraph as RLParagraph
        
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
            story.append(Paragraph(content.replace('\n', '<br/>'), styles["Normal"]))
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
        elif action_name == "exportieren" or action_name == "visualisieren":
            return None  # Not supported via simple text prompt
        else:
            return f"{action_name.replace('_', ' ').title()} folgenden Text:\n\n{content}"

    def _run_action_button_analysis(self, action_name: str, prompt: str):
        """Run the AI analysis for an action button in a background thread."""
        try:
            result = real_ai_analyse_fortext(prompt)
            self.window.after(0, self._display_action_button_result, action_name, result)
        except Exception as e:
            error_msg = self.error_handler.create_user_friendly_message(
                self.error_handler.handle_error(e, {"operation": "action_button"})
            )
            self.window.after(0, self._show_error, error_msg)
        finally:
            self.window.after(0, self.progress_indicator.stop)

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
            
    def _on_chart_created(self, chart_path: str):
        """Handle chart creation completion."""
        self.status_var.set(f"Diagramm erstellt: {os.path.basename(chart_path)}")
        
    def _on_export_completed(self, export_path: str):
        """Handle export completion."""
        self.status_var.set(f"Export abgeschlossen: {os.path.basename(export_path)}")
        messagebox.showinfo("Export erfolgreich", f"Daten wurden exportiert nach:\n{export_path}")
        
    def _on_historical_result_selected(self, result: ProcessedResult):
        """Handle selection of historical result."""
        self._display_enhanced_result(result)
        
    def _show_error(self, error_msg: str):
        """Show error message to user."""
        messagebox.showerror("Fehler", error_msg)
        self.status_var.set("Fehler aufgetreten")
        
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
        
    def _show_settings_dialog(self):
        """Show settings dialog."""
        # Create settings dialog
        dialog = tk.Toplevel(self.window)
        dialog.title("Einstellungen")
        dialog.geometry("400x300")
        dialog.transient(self.window)
        dialog.grab_set()
        
        # Add settings options
        ttk.Label(dialog, text="Erweiterte Einstellungen", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Auto-save results option
        auto_save_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            dialog,
            text="Ergebnisse automatisch speichern",
            variable=auto_save_var
        ).pack(anchor=tk.W, padx=20, pady=5)
        
        # Auto-generate visualizations option
        auto_viz_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            dialog,
            text="Visualisierungen automatisch erstellen",
            variable=auto_viz_var
        ).pack(anchor=tk.W, padx=20, pady=5)
        
        # Close button
        ttk.Button(dialog, text="Schließen", command=dialog.destroy).pack(pady=20)
        
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
            super().send_question()
                
        except Exception as e:
            if hasattr(self, 'error_handler'):
                error_msg = self.error_handler.create_user_friendly_message(
                    self.error_handler.handle_error(e, {"operation": "send_question"})
                )
                self._show_error(error_msg)
            else:
                # Fallback error handling
                messagebox.showerror("Fehler", f"Fehler bei der Analyse: {str(e)}")
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
                self.status_var.set(f"Ergebnis gespeichert (ID: {result_id[:8]}...)")
            except Exception as e:
                self.status_var.set("Fehler beim Speichern des Ergebnisses")


def create_enhanced_gui(window):
    """Factory function to create enhanced GUI."""
    return EnhancedGui(window)


# Backward compatibility: allow importing as Gui
Gui = EnhancedGui