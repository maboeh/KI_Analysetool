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
            status_callback=self._on_status_update,
            analysis_callback=self._on_enhanced_analysis_requested
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
        self.enhanced_output_frame.rowconfigure(0, weight=1)
        self.enhanced_output_frame.columnconfigure(0, weight=1)
        
        # Create tabbed interface for different result views
        self.result_notebook = ttk.Notebook(self.enhanced_output_frame)
        self.result_notebook.grid(row=0, column=0, sticky=tk.W + tk.E + tk.N + tk.S)
        
        # Text results tab (enhanced version of original)
        self.text_results_frame = ttk.Frame(self.result_notebook)
        self.result_notebook.add(self.text_results_frame, text="Textanalyse")
        
        # Enhanced results display widget
        self.results_display = ResultsDisplayWidget(self.text_results_frame)
        self.results_display.pack(fill=tk.BOTH, expand=True)
        
        # Action buttons frame
        self.action_buttons = ActionButtonsFrame(self.text_results_frame)
        self.action_buttons.pack(fill=tk.X, pady=(5, 0))
        
        # Visualization tab
        self.viz_frame = ttk.Frame(self.result_notebook)
        self.result_notebook.add(self.viz_frame, text="Visualisierung")
        
        self.visualization_panel = DataVisualizationPanel(self.viz_frame)
        
        # Data export tab
        self.export_frame = ttk.Frame(self.result_notebook)
        self.result_notebook.add(self.export_frame, text="Datenexport")
        
        self.excel_export_ui = ExcelExportUI(self.export_frame)
        
        # Results browser tab
        self.browser_frame = ttk.Frame(self.result_notebook)
        self.result_notebook.add(self.browser_frame, text="Ergebnisverlauf")
        
        self.results_browser = ResultsBrowser(self.browser_frame, self.results_manager)
        
        # Hide original output text widget but keep it for backward compatibility
        self.original_output_text.grid_remove()
        
        # Update the output_text reference to point to enhanced display
        self.output_text = self.results_display.text_widget
        
    def _add_enhanced_menu(self):
        """Add enhanced menu items and toolbar."""
        # Use existing menubar from base GUI
        if hasattr(self, 'menubar'):
            menubar = self.menubar
        else:
            self.menubar = tk.Menu(self.window)
            self.window.config(menu=self.menubar)
            menubar = self.menubar
            
        # Add enhanced features menu
        self.enhanced_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Erweiterte Funktionen", menu=self.enhanced_menu)
        
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
        custom_prompt = self.question_text.get(1.0, tk.END).strip()
        prompt_template = self.get_prompt()
        
        self.processing_thread = threading.Thread(
            target=self._process_enhanced_analysis,
            args=(content, source_path, analysis_type, custom_prompt, prompt_template)
        )
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
    def _process_enhanced_analysis(self, content: str, source_path: str, analysis_type: str, custom_prompt: str, prompt_template: str):
        """Process analysis with enhanced features in background thread."""
        try:
            self.window.after(0, lambda: self.progress_indicator.start("Analyse wird durchgeführt..."))
            
            if custom_prompt:
                combined_prompt = f"{custom_prompt}\n\nInhalt: {content}"
                ai_result = real_ai_analyse_fortext(combined_prompt)
            else:
                prompt = prompt_template.replace("{text}", content)
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
        
        # Update visualization panel
        if result.extracted_data:
            self.visualization_panel.update_data(result.extracted_data)
            
        # Update export UI
        self.excel_export_ui.update_data(result.extracted_data)
        
        # Refresh results browser
        self.results_browser.refresh_results()
        
        # Update status
        self.status_var.set("Analyse abgeschlossen - Erweiterte Funktionen verfügbar")
        
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
            if self.processing_thread and self.processing_thread.is_alive():
                messagebox.showinfo("Analyse läuft", "Eine Analyse wird bereits durchgeführt. Bitte warte einen Moment.")
                return

            if hasattr(self, 'enhanced_input_tabs'):
                tab_id = self.input_tabs.select()
                tab_index = self.input_tabs.index(tab_id)
                if tab_index >= 3:
                    self.enhanced_input_tabs.trigger_analysis()
                    return

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