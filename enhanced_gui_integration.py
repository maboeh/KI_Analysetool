"""
Enhanced GUI integration that combines ExtendedInputTabs and DataVisualizationPanel
into the main interface with tabbed results display.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import Optional, Dict, Any, Callable
import logging

from extended_input_tabs import ExtendedInputTabs
from visualization_panel import DataVisualizationPanel
from results_display import ResultsDisplayWidget
from action_buttons import ActionButtonsFrame
from data_models import ProcessedResult, StructuredData
from markdown_formatter import configure_markdown_tags, markdown_to_tkinter_text


class EnhancedResultsInterface:
    """
    Enhanced results interface with tabbed display for text results and visualizations.
    
    This class provides a comprehensive interface that combines text results,
    interactive visualizations, and follow-up actions in a tabbed layout.
    """
    
    def __init__(self, parent_widget, on_action_triggered: Optional[Callable] = None):
        """
        Initialize the enhanced results interface.
        
        Args:
            parent_widget: Parent Tkinter widget
            on_action_triggered: Optional callback for action button clicks
        """
        self.parent = parent_widget
        self.on_action_triggered = on_action_triggered
        
        # Current state
        self.current_result: Optional[ProcessedResult] = None
        self.current_structured_data: Optional[StructuredData] = None
        
        # Create the UI
        self._create_ui()
    
    def _create_ui(self):
        """Create the enhanced results interface."""
        # Main container
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for tabbed results
        self.results_notebook = ttk.Notebook(self.main_frame)
        self.results_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Text results tab
        self.text_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(self.text_frame, text="Textergebnisse")
        
        # Visualization tab
        self.viz_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(self.viz_frame, text="Visualisierungen")
        
        # Data overview tab
        self.data_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(self.data_frame, text="Datenübersicht")
        
        # Create text results interface
        self._create_text_results_interface()
        
        # Create visualization interface
        self._create_visualization_interface()
        
        # Create data overview interface
        self._create_data_overview_interface()
    
    def _create_text_results_interface(self):
        """Create the text results display interface."""
        # Results display widget
        try:
            self.results_display = ResultsDisplayWidget(
                self.text_frame,
                on_action_triggered=self.on_action_triggered
            )
        except Exception as e:
            logging.warning(f"Could not create ResultsDisplayWidget: {e}")
            # Fallback to basic text widget
            self._create_fallback_text_interface()
    
    def _create_fallback_text_interface(self):
        """Create fallback text interface if ResultsDisplayWidget is not available."""
        # Control frame
        control_frame = ttk.Frame(self.text_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Action buttons frame
        try:
            self.action_buttons = ActionButtonsFrame(
                control_frame,
                on_action_triggered=self.on_action_triggered
            )
        except Exception as e:
            logging.warning(f"Could not create ActionButtonsFrame: {e}")
            # Create basic action buttons
            self._create_basic_action_buttons(control_frame)
        
        # Text display
        text_container = ttk.Frame(self.text_frame)
        text_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.text_widget = scrolledtext.ScrolledText(
            text_container,
            wrap=tk.WORD,
            height=15,
            state=tk.DISABLED
        )
        self.text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Configure markdown tags
        configure_markdown_tags(self.text_widget)
        
        # Status label
        self.status_label = ttk.Label(text_container, text="Bereit für Analyse")
        self.status_label.pack(anchor=tk.W, pady=(5, 0))
    
    def _create_basic_action_buttons(self, parent):
        """Create basic action buttons as fallback."""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=5)
        
        # Basic action buttons
        actions = [
            ("Zusammenfassen", "summarize"),
            ("Vertiefen", "elaborate"),
            ("Übersetzen", "translate"),
            ("Exportieren", "export")
        ]
        
        for text, action in actions:
            btn = ttk.Button(
                button_frame,
                text=text,
                command=lambda a=action: self._trigger_action(a)
            )
            btn.pack(side=tk.LEFT, padx=2)
    
    def _create_visualization_interface(self):
        """Create the visualization interface."""
        try:
            self.visualization_panel = DataVisualizationPanel(
                self.viz_frame,
                on_chart_created=self._on_chart_created
            )
        except Exception as e:
            logging.error(f"Could not create DataVisualizationPanel: {e}")
            # Create placeholder
            placeholder = ttk.Label(
                self.viz_frame,
                text="Visualisierungskomponente nicht verfügbar.\nBitte überprüfen Sie die Installation der erforderlichen Abhängigkeiten.",
                font=("Arial", 12),
                foreground="red"
            )
            placeholder.pack(expand=True)
            self.visualization_panel = None
    
    def _create_data_overview_interface(self):
        """Create the data overview interface."""
        # Data summary frame
        summary_frame = ttk.LabelFrame(self.data_frame, text="Datenübersicht")
        summary_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.data_summary_text = scrolledtext.ScrolledText(
            summary_frame,
            height=8,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.data_summary_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Extracted data frame
        extracted_frame = ttk.LabelFrame(self.data_frame, text="Extrahierte Daten")
        extracted_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview for structured data display
        columns = ("Typ", "Wert", "Kontext")
        self.data_tree = ttk.Treeview(extracted_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            self.data_tree.heading(col, text=col)
            self.data_tree.column(col, width=150)
        
        # Scrollbars for treeview
        tree_scrollbar_y = ttk.Scrollbar(extracted_frame, orient=tk.VERTICAL, command=self.data_tree.yview)
        tree_scrollbar_x = ttk.Scrollbar(extracted_frame, orient=tk.HORIZONTAL, command=self.data_tree.xview)
        self.data_tree.configure(yscrollcommand=tree_scrollbar_y.set, xscrollcommand=tree_scrollbar_x.set)
        
        self.data_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        tree_scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Export buttons for data
        data_buttons_frame = ttk.Frame(self.data_frame)
        data_buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            data_buttons_frame,
            text="Daten als Excel exportieren",
            command=self._export_data_excel
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            data_buttons_frame,
            text="Daten als CSV exportieren",
            command=self._export_data_csv
        ).pack(side=tk.LEFT, padx=2)
    
    def display_result(self, result: ProcessedResult):
        """
        Display a processed result in the interface.
        
        Args:
            result: ProcessedResult object to display
        """
        self.current_result = result
        
        # Display text results
        self._display_text_result(result)
        
        # Display structured data if available
        if hasattr(result, 'structured_data') and result.structured_data:
            self.current_structured_data = result.structured_data
            self._display_structured_data(result.structured_data)
            
            # Load data into visualization panel
            if self.visualization_panel:
                try:
                    self.visualization_panel.load_data(result.structured_data)
                except Exception as e:
                    logging.error(f"Error loading data into visualization panel: {e}")
        
        # Update action buttons if available
        self._update_action_buttons(result)
    
    def _display_text_result(self, result: ProcessedResult):
        """Display text result in the text tab."""
        if hasattr(self, 'results_display'):
            # Use enhanced results display
            try:
                self.results_display.display_result(result)
                return
            except Exception as e:
                logging.warning(f"Error using ResultsDisplayWidget: {e}")
        
        # Fallback to basic text display
        if hasattr(self, 'text_widget'):
            self.text_widget.config(state=tk.NORMAL)
            self.text_widget.delete(1.0, tk.END)
            
            # Use markdown formatting if available
            try:
                markdown_to_tkinter_text(result.content, self.text_widget)
            except Exception:
                # Plain text fallback
                self.text_widget.insert(1.0, result.content)
            
            self.text_widget.config(state=tk.DISABLED)
            
            # Update status
            if hasattr(self, 'status_label'):
                timestamp = result.created_at.strftime("%H:%M:%S") if hasattr(result, 'created_at') else "Unbekannt"
                self.status_label.config(text=f"Ergebnis angezeigt - {timestamp}")
    
    def _display_structured_data(self, structured_data: StructuredData):
        """Display structured data in the data overview tab."""
        # Update data summary
        self.data_summary_text.config(state=tk.NORMAL)
        self.data_summary_text.delete(1.0, tk.END)
        
        summary_lines = []
        summary_lines.append("=== Datenübersicht ===")
        
        if hasattr(structured_data, 'tables') and structured_data.tables:
            summary_lines.append(f"Tabellen: {len(structured_data.tables)}")
        
        if hasattr(structured_data, 'entities') and structured_data.entities:
            summary_lines.append(f"Entitäten: {len(structured_data.entities)}")
        
        if hasattr(structured_data, 'numeric_values') and structured_data.numeric_values:
            summary_lines.append(f"Numerische Werte: {len(structured_data.numeric_values)}")
        
        if hasattr(structured_data, 'temporal_data') and structured_data.temporal_data:
            summary_lines.append(f"Zeitdaten: {len(structured_data.temporal_data)}")
        
        summary_lines.append("")
        summary_lines.append("Diese Daten können für Visualisierungen und Exporte verwendet werden.")
        
        self.data_summary_text.insert(1.0, "\n".join(summary_lines))
        self.data_summary_text.config(state=tk.DISABLED)
        
        # Update data tree
        self._populate_data_tree(structured_data)
    
    def _populate_data_tree(self, structured_data: StructuredData):
        """Populate the data tree with structured data."""
        # Clear existing items
        for item in self.data_tree.get_children():
            self.data_tree.delete(item)
        
        # Add tables
        if hasattr(structured_data, 'tables') and structured_data.tables:
            for i, table in enumerate(structured_data.tables):
                table_name = getattr(table, 'name', f"Tabelle {i+1}")
                rows = getattr(table, 'rows', 0)
                cols = getattr(table, 'columns', 0)
                self.data_tree.insert("", tk.END, values=("Tabelle", table_name, f"{rows}x{cols}"))
        
        # Add entities
        if hasattr(structured_data, 'entities') and structured_data.entities:
            for entity in structured_data.entities[:20]:  # Limit to first 20
                entity_type = getattr(entity, 'type', 'Unbekannt')
                entity_text = getattr(entity, 'text', str(entity))
                confidence = getattr(entity, 'confidence', 0)
                self.data_tree.insert("", tk.END, values=("Entität", f"{entity_type}: {entity_text}", f"Vertrauen: {confidence:.2f}"))
        
        # Add numeric values
        if hasattr(structured_data, 'numeric_values') and structured_data.numeric_values:
            for num_val in structured_data.numeric_values[:20]:  # Limit to first 20
                value = getattr(num_val, 'value', str(num_val))
                unit = getattr(num_val, 'unit', '')
                context = getattr(num_val, 'context', '')
                display_value = f"{value} {unit}".strip()
                self.data_tree.insert("", tk.END, values=("Numerisch", display_value, context))
        
        # Add temporal data
        if hasattr(structured_data, 'temporal_data') and structured_data.temporal_data:
            for temp_val in structured_data.temporal_data[:20]:  # Limit to first 20
                date_str = getattr(temp_val, 'formatted_date', str(temp_val))
                date_type = getattr(temp_val, 'type', 'Datum')
                context = getattr(temp_val, 'context', '')
                self.data_tree.insert("", tk.END, values=("Zeitdaten", f"{date_type}: {date_str}", context))
    
    def _update_action_buttons(self, result: ProcessedResult):
        """Update action buttons based on the result."""
        if hasattr(self, 'action_buttons'):
            try:
                self.action_buttons.update_for_result(result)
            except Exception as e:
                logging.warning(f"Error updating action buttons: {e}")
    
    def _trigger_action(self, action_type: str):
        """Trigger an action callback."""
        if self.on_action_triggered and self.current_result:
            try:
                self.on_action_triggered(action_type, self.current_result)
            except Exception as e:
                logging.error(f"Error triggering action {action_type}: {e}")
                messagebox.showerror("Fehler", f"Fehler beim Ausführen der Aktion: {e}")
    
    def _on_chart_created(self, visualization):
        """Handle chart creation callback."""
        # Switch to visualization tab when a chart is created
        self.results_notebook.select(self.viz_frame)
    
    def _export_data_excel(self):
        """Export structured data as Excel file."""
        if not self.current_structured_data:
            messagebox.showwarning("Warnung", "Keine strukturierten Daten zum Exportieren verfügbar.")
            return
        
        try:
            from excel_exporter import ExcelExporter
            exporter = ExcelExporter()
            
            # This would typically open a file dialog and export
            messagebox.showinfo("Info", "Excel-Export-Funktionalität wird implementiert...")
            
        except ImportError:
            messagebox.showerror("Fehler", "Excel-Export-Komponente nicht verfügbar.")
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Excel-Export: {e}")
    
    def _export_data_csv(self):
        """Export structured data as CSV file."""
        if not self.current_structured_data:
            messagebox.showwarning("Warnung", "Keine strukturierten Daten zum Exportieren verfügbar.")
            return
        
        try:
            # This would typically open a file dialog and export
            messagebox.showinfo("Info", "CSV-Export-Funktionalität wird implementiert...")
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim CSV-Export: {e}")
    
    def clear(self):
        """Clear all displayed results and data."""
        self.current_result = None
        self.current_structured_data = None
        
        # Clear text results
        if hasattr(self, 'results_display'):
            try:
                self.results_display.clear()
            except Exception:
                pass
        
        if hasattr(self, 'text_widget'):
            self.text_widget.config(state=tk.NORMAL)
            self.text_widget.delete(1.0, tk.END)
            self.text_widget.insert(1.0, "Das Ergebnis wird hier angezeigt...")
            self.text_widget.config(state=tk.DISABLED)
        
        # Clear visualization
        if self.visualization_panel:
            try:
                self.visualization_panel.clear()
            except Exception:
                pass
        
        # Clear data overview
        self.data_summary_text.config(state=tk.NORMAL)
        self.data_summary_text.delete(1.0, tk.END)
        self.data_summary_text.config(state=tk.DISABLED)
        
        for item in self.data_tree.get_children():
            self.data_tree.delete(item)
        
        # Reset to first tab
        self.results_notebook.select(self.text_frame)


class EnhancedGuiIntegration:
    """
    Main class for integrating enhanced input tabs and results interface
    into the existing GUI structure.
    """
    
    def __init__(self, main_gui_instance):
        """
        Initialize enhanced GUI integration.
        
        Args:
            main_gui_instance: Instance of the main Gui class
        """
        self.main_gui = main_gui_instance
        self.extended_input_tabs = None
        self.enhanced_results = None
        
        # Initialize components
        self._integrate_extended_input_tabs()
        self._integrate_enhanced_results()
    
    def _integrate_extended_input_tabs(self):
        """Integrate ExtendedInputTabs into the main GUI."""
        try:
            # Get the existing input tabs notebook
            input_notebook = self.main_gui.input_tabs
            
            # Create extended input tabs
            self.extended_input_tabs = ExtendedInputTabs(
                input_notebook,
                status_callback=self._update_status
            )
            
            logging.info("Extended input tabs integrated successfully")
            
        except Exception as e:
            logging.error(f"Failed to integrate extended input tabs: {e}")
            messagebox.showerror("Fehler", f"Fehler beim Integrieren der erweiterten Eingabe-Tabs: {e}")
    
    def _integrate_enhanced_results(self):
        """Integrate EnhancedResultsInterface into the main GUI."""
        try:
            # Replace the existing output area with enhanced results interface
            if hasattr(self.main_gui, 'analysis_frame'):
                # Find the output area in the analysis frame
                analysis_frame = self.main_gui.analysis_frame
                
                # Create enhanced results interface
                self.enhanced_results = EnhancedResultsInterface(
                    analysis_frame,
                    on_action_triggered=self._handle_action
                )
                
                # Hide or replace the existing output text widget
                if hasattr(self.main_gui, 'output_text'):
                    self.main_gui.output_text.pack_forget()
                
                logging.info("Enhanced results interface integrated successfully")
            
        except Exception as e:
            logging.error(f"Failed to integrate enhanced results interface: {e}")
            messagebox.showerror("Fehler", f"Fehler beim Integrieren der erweiterten Ergebnis-Anzeige: {e}")
    
    def _update_status(self, message: str):
        """Update status in the main GUI."""
        if hasattr(self.main_gui, 'status_var'):
            self.main_gui.status_var.set(message)
    
    def _handle_action(self, action_type: str, result: ProcessedResult):
        """Handle action button clicks."""
        # This would integrate with the main analysis workflow
        logging.info(f"Action triggered: {action_type}")
        
        # For now, just update status
        self._update_status(f"Aktion ausgeführt: {action_type}")
    
    def get_current_input_content(self) -> Optional[str]:
        """
        Get content from currently selected input tab.
        
        Returns:
            Content string ready for analysis, or None if no content available
        """
        # First try extended input tabs
        if self.extended_input_tabs:
            content = self.extended_input_tabs.get_current_content()
            if content:
                return content
        
        # Fallback to original input tabs
        try:
            return self.main_gui.start_analyse()
        except Exception as e:
            logging.error(f"Error getting input content: {e}")
            return None
    
    def display_analysis_result(self, result_text: str):
        """
        Display analysis result in the enhanced interface.
        
        Args:
            result_text: Analysis result text to display
        """
        if self.enhanced_results:
            try:
                # Create a basic ProcessedResult object
                # In a full implementation, this would come from the analysis pipeline
                from datetime import datetime
                
                processed_result = ProcessedResult(
                    id=f"result_{datetime.now().timestamp()}",
                    content=result_text,
                    created_at=datetime.now()
                )
                
                self.enhanced_results.display_result(processed_result)
                
            except Exception as e:
                logging.error(f"Error displaying result in enhanced interface: {e}")
                # Fallback to original display
                self._fallback_display_result(result_text)
        else:
            self._fallback_display_result(result_text)
    
    def _fallback_display_result(self, result_text: str):
        """Fallback to original result display."""
        if hasattr(self.main_gui, 'output_text'):
            self.main_gui.output_text.config(state=tk.NORMAL)
            self.main_gui.output_text.delete(1.0, tk.END)
            
            try:
                from markdown_formatter import markdown_to_tkinter_text
                markdown_to_tkinter_text(result_text, self.main_gui.output_text)
            except Exception:
                self.main_gui.output_text.insert(1.0, result_text)
            
            self.main_gui.output_text.config(state=tk.DISABLED)
    
    def is_enhanced_interface_available(self) -> bool:
        """Check if enhanced interface components are available."""
        return (self.extended_input_tabs is not None and 
                self.enhanced_results is not None)