"""
Excel Export UI Integration for KI Analysetool

This module provides UI components for Excel export functionality,
including export dialogs, preview functionality, and integration
with the results display and action buttons.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime

from excel_exporter import (
    ExcelExporter, ExportTemplate, create_excel_export_filename,
    validate_export_data
)
from data_models import ProcessedResult, StructuredData
from help_tooltip import add_help_indicator


@dataclass
class ExportOptions:
    """Configuration options for Excel export"""
    template_name: str = 'complete'
    file_path: str = ''
    include_preview: bool = True
    auto_open: bool = False
    custom_filename: bool = False


class ExcelExportUI:
    """UI component for Excel export functionality"""
    
    def __init__(self, parent=None, on_export_completed: Optional[Callable] = None):
        self.parent = parent
        self.exporter = ExcelExporter()
        self.export_options = ExportOptions()
        self.on_export_completed = on_export_completed
        
    def show_export_dialog(self, result: ProcessedResult) -> bool:
        """Show export dialog and handle export process"""
        try:
            # Simple file dialog for now
            filename = filedialog.asksaveasfilename(
                title="Excel-Export speichern",
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            
            if filename:
                success = self.exporter.export_result(result, filename)
                if success:
                    messagebox.showinfo("Export erfolgreich", f"Datei gespeichert: {filename}")
                    if self.on_export_completed:
                        self.on_export_completed(filename)
                    return True
                else:
                    messagebox.showerror("Export fehlgeschlagen", "Fehler beim Speichern der Datei")
            return False
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Export-Fehler: {str(e)}")
            return False
    
    def export_to_excel(self, result: ProcessedResult, filename: str = None) -> bool:
        """Export result to Excel file"""
        try:
            if not filename:
                filename = create_excel_export_filename(result.source_info.file_path if result.source_info else "analysis")
            
            success = self.exporter.export_result(result, filename)
            if success and self.on_export_completed:
                self.on_export_completed(filename)
            return success
        except Exception as e:
            print(f"Excel export error: {e}")
            return False


class ExcelExportDialog(tk.Toplevel):
    """
    Dialog for configuring Excel export options.
    
    Features:
    - Template selection
    - File path selection
    - Export preview
    - Validation feedback
    """
    
    def __init__(self, parent, result: ProcessedResult, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.result = result
        self.exporter = ExcelExporter()
        self.export_options = ExportOptions()
        self.export_successful = False
        
        # Dialog configuration
        self.title("Excel Export")
        self.geometry("600x500")
        self.transient(parent)
        self.grab_set()
        self.resizable(True, True)
        
        # Center the dialog
        self._center_dialog()
        
        # Setup UI
        self._setup_ui()
        self._validate_data()
        self._update_preview()
    
    def _center_dialog(self):
        """Center the dialog on the parent window"""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.winfo_screenheight() // 2) - (500 // 2)
        self.geometry(f"600x500+{x}+{y}")
    
    def _setup_ui(self):
        """Setup the dialog UI components"""
        # Main container
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Excel Export Konfiguration",
                               font=("Segoe UI", 12, "bold"))
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Data validation section
        self._create_validation_section(main_frame)
        
        # Template selection section
        self._create_template_section(main_frame)
        
        # File selection section
        self._create_file_section(main_frame)
        
        # Preview section
        self._create_preview_section(main_frame)
        
        # Options section
        self._create_options_section(main_frame)
        
        # Buttons
        self._create_buttons(main_frame)
    
    def _create_validation_section(self, parent):
        """Create data validation feedback section"""
        validation_frame = ttk.LabelFrame(parent, text="Datenvalidierung", padding="5")
        validation_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.validation_text = tk.Text(validation_frame, height=3, wrap=tk.WORD,
                                      state=tk.DISABLED, bg="#f8f9fa")
        self.validation_text.pack(fill=tk.X)
    
    def _create_template_section(self, parent):
        """Create template selection section"""
        template_frame = ttk.LabelFrame(parent, text="Export-Vorlage", padding="5")
        template_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Template selection
        ttk.Label(template_frame, text="Vorlage auswählen:").pack(anchor=tk.W)
        
        self.template_var = tk.StringVar(value='complete')
        template_combo = ttk.Combobox(template_frame, textvariable=self.template_var,
                                     state="readonly", width=50)
        
        # Populate templates
        templates = self.exporter.get_available_templates()
        template_combo['values'] = list(templates.keys())
        template_combo.pack(fill=tk.X, pady=(5, 0))
        
        # Template description
        self.template_desc_label = ttk.Label(template_frame, text="",
                                           foreground="#666666", wraplength=500)
        self.template_desc_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Bind template selection
        template_combo.bind('<<ComboboxSelected>>', self._on_template_changed)
        
        # Update initial description
        self._update_template_description()
    
    def _create_file_section(self, parent):
        """Create file selection section"""
        file_frame = ttk.LabelFrame(parent, text="Datei-Optionen", padding="5")
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        # File path selection
        path_frame = ttk.Frame(file_frame)
        path_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(path_frame, text="Speicherort:").pack(anchor=tk.W)
        
        path_entry_frame = ttk.Frame(path_frame)
        path_entry_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.file_path_var = tk.StringVar()
        self.file_path_entry = ttk.Entry(path_entry_frame, textvariable=self.file_path_var)
        self.file_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        browse_frame = ttk.Frame(path_entry_frame)
        browse_frame.pack(side=tk.RIGHT, padx=(5, 0))
        browse_btn = ttk.Button(browse_frame, text="Durchsuchen...",
                               command=self._browse_file)
        browse_btn.pack(side=tk.LEFT)
        add_help_indicator(browse_frame,
                          "Öffnet einen Datei-Dialog zur Auswahl des Speicherorts für die Excel-Datei.")
        
        # Auto-generate filename option
        self.auto_filename_var = tk.BooleanVar(value=True)
        auto_filename_cb = ttk.Checkbutton(file_frame, 
                                          text="Dateiname automatisch generieren",
                                          variable=self.auto_filename_var,
                                          command=self._on_auto_filename_changed)
        auto_filename_cb.pack(anchor=tk.W, pady=(5, 0))
        
        # Generate initial filename
        self._generate_filename()
    
    def _create_preview_section(self, parent):
        """Create export preview section"""
        preview_frame = ttk.LabelFrame(parent, text="Export-Vorschau", padding="5")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Preview text widget
        self.preview_text = tk.Text(preview_frame, height=8, wrap=tk.WORD,
                                   state=tk.DISABLED, bg="#f8f9fa")
        
        preview_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL,
                                         command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=preview_scrollbar.set)
        
        self.preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        preview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _create_options_section(self, parent):
        """Create additional options section"""
        options_frame = ttk.LabelFrame(parent, text="Zusätzliche Optionen", padding="5")
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Auto-open file option
        self.auto_open_var = tk.BooleanVar(value=False)
        auto_open_cb = ttk.Checkbutton(options_frame,
                                      text="Datei nach Export automatisch öffnen",
                                      variable=self.auto_open_var)
        auto_open_cb.pack(anchor=tk.W)
    
    def _create_buttons(self, parent):
        """Create dialog buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Export button
        export_frame = ttk.Frame(button_frame)
        export_frame.pack(side=tk.RIGHT, padx=(5, 0))
        self.export_btn = ttk.Button(export_frame, text="Exportieren",
                                    command=self._export_data)
        self.export_btn.pack(side=tk.LEFT)
        add_help_indicator(export_frame,
                          "Startet den Excel-Export mit den ausgewählten Optionen und speichert die Datei am angegebenen Speicherort.")
        
        # Cancel button
        cancel_frame = ttk.Frame(button_frame)
        cancel_frame.pack(side=tk.RIGHT)
        cancel_btn = ttk.Button(cancel_frame, text="Abbrechen",
                               command=self.destroy)
        cancel_btn.pack(side=tk.LEFT)
        add_help_indicator(cancel_frame,
                          "Bricht den Export-Dialog ab, ohne eine Datei zu erstellen.")
        
        # Preview refresh button
        refresh_btn = ttk.Button(button_frame, text="Vorschau aktualisieren",
                                command=self._update_preview)
        refresh_btn.pack(side=tk.LEFT)
    
    def _validate_data(self):
        """Validate the data for export and show feedback"""
        validation = validate_export_data(self.result)
        
        self.validation_text.config(state=tk.NORMAL)
        self.validation_text.delete(1.0, tk.END)
        
        if validation['has_exportable_data']:
            self.validation_text.insert(tk.END, "✓ Exportierbare Daten gefunden:\n")
            for data_type in validation['data_types']:
                type_names = {
                    'tables': 'Tabellen',
                    'entities': 'Entitäten',
                    'numeric_values': 'Numerische Werte',
                    'temporal_data': 'Zeitdaten'
                }
                self.validation_text.insert(tk.END, f"  • {type_names.get(data_type, data_type)}\n")
        else:
            self.validation_text.insert(tk.END, "⚠ Keine strukturierten Daten zum Exportieren gefunden.\n")
            self.validation_text.insert(tk.END, "Der Export wird nur eine Zusammenfassung enthalten.\n")
        
        if validation['warnings']:
            self.validation_text.insert(tk.END, "\nWarnungen:\n")
            for warning in validation['warnings']:
                self.validation_text.insert(tk.END, f"  • {warning}\n")
        
        self.validation_text.config(state=tk.DISABLED)
        
        # Enable/disable export button based on validation
        self.export_btn.config(state=tk.NORMAL if validation['has_exportable_data'] else tk.DISABLED)
    
    def _update_template_description(self):
        """Update the template description label"""
        templates = self.exporter.get_available_templates()
        template_name = self.template_var.get()
        description = templates.get(template_name, "Keine Beschreibung verfügbar")
        self.template_desc_label.config(text=description)
    
    def _generate_filename(self):
        """Generate automatic filename"""
        if self.auto_filename_var.get():
            filename = create_excel_export_filename(self.result)
            # Get user's documents directory or current directory
            documents_dir = os.path.expanduser("~/Documents")
            if not os.path.exists(documents_dir):
                documents_dir = os.getcwd()
            
            full_path = os.path.join(documents_dir, filename)
            self.file_path_var.set(full_path)
    
    def _update_preview(self):
        """Update the export preview"""
        try:
            template_name = self.template_var.get()
            preview = self.exporter.preview_export_structure(self.result, template_name)
            
            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete(1.0, tk.END)
            
            # Format preview information
            self.preview_text.insert(tk.END, f"Vorlage: {preview['template']}\n\n")
            self.preview_text.insert(tk.END, f"Arbeitsblätter ({len(preview['sheets'])}):\n")
            for sheet in preview['sheets']:
                self.preview_text.insert(tk.END, f"  • {sheet}\n")
            
            self.preview_text.insert(tk.END, f"\nGeschätzte Zeilen: {preview['total_rows']}\n\n")
            
            if preview['data_summary']:
                self.preview_text.insert(tk.END, "Datenübersicht:\n")
                for data_type, count in preview['data_summary'].items():
                    type_names = {
                        'tables': 'Tabellen',
                        'entities': 'Entitäten', 
                        'numeric_values': 'Numerische Werte',
                        'temporal_data': 'Zeitdaten'
                    }
                    name = type_names.get(data_type, data_type)
                    self.preview_text.insert(tk.END, f"  • {name}: {count}\n")
            
            self.preview_text.config(state=tk.DISABLED)
            
        except Exception as e:
            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, f"Fehler bei Vorschau-Generierung: {str(e)}")
            self.preview_text.config(state=tk.DISABLED)
    
    def _on_template_changed(self, event=None):
        """Handle template selection change"""
        self._update_template_description()
        self._update_preview()
    
    def _on_auto_filename_changed(self):
        """Handle auto filename checkbox change"""
        if self.auto_filename_var.get():
            self._generate_filename()
            self.file_path_entry.config(state=tk.DISABLED)
        else:
            self.file_path_entry.config(state=tk.NORMAL)
    
    def _browse_file(self):
        """Open file browser for selecting export location"""
        initial_dir = os.path.dirname(self.file_path_var.get()) or os.path.expanduser("~/Documents")
        initial_name = os.path.basename(self.file_path_var.get()) or create_excel_export_filename(self.result)
        
        file_path = filedialog.asksaveasfilename(
            title="Excel-Datei speichern",
            initialdir=initial_dir,
            initialfile=initial_name,
            defaultextension=".xlsx",
            filetypes=[
                ("Excel-Dateien", "*.xlsx"),
                ("Alle Dateien", "*.*")
            ]
        )
        
        if file_path:
            self.file_path_var.set(file_path)
            self.auto_filename_var.set(False)
            self.file_path_entry.config(state=tk.NORMAL)
    
    def _export_data(self):
        """Perform the actual export"""
        try:
            file_path = self.file_path_var.get().strip()
            if not file_path:
                messagebox.showerror("Fehler", "Bitte wählen Sie einen Speicherort aus.")
                return
            
            # Ensure .xlsx extension
            if not file_path.lower().endswith('.xlsx'):
                file_path += '.xlsx'
            
            # Check if file exists and ask for confirmation
            if os.path.exists(file_path):
                if not messagebox.askyesno("Datei überschreiben", 
                                         f"Die Datei '{os.path.basename(file_path)}' existiert bereits.\n"
                                         "Möchten Sie sie überschreiben?"):
                    return
            
            # Perform export
            template_name = self.template_var.get()
            success = self.exporter.export_to_excel(self.result, file_path, template_name)
            
            if success:
                self.export_successful = True
                
                # Show success message
                message = f"Export erfolgreich!\n\nDatei gespeichert unter:\n{file_path}"
                
                if self.auto_open_var.get():
                    try:
                        os.startfile(file_path)  # Windows
                    except AttributeError:
                        import subprocess
                        import platform
                        if platform.system() == "Darwin":
                            subprocess.run(["open", file_path], check=False)
                        else:
                            subprocess.run(["xdg-open", file_path], check=False)
                    
                    message += "\n\nDie Datei wird geöffnet..."
                
                messagebox.showinfo("Export erfolgreich", message)
                self.destroy()
                
            else:
                messagebox.showerror("Export fehlgeschlagen", 
                                   "Der Export konnte nicht durchgeführt werden.\n"
                                   "Bitte überprüfen Sie den Speicherort und versuchen Sie es erneut.")
        
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Export: {str(e)}")


class ExcelExportButton(ttk.Button):
    """
    Specialized button for Excel export functionality.
    
    Features:
    - Automatic enable/disable based on data availability
    - Integrated export dialog
    - Progress indication
    """
    
    def __init__(self, parent, result_provider: Callable[[], Optional[ProcessedResult]], **kwargs):
        # Set default button properties
        kwargs.setdefault('text', '📊 Excel Export')
        kwargs.setdefault('command', self._on_export_click)
        
        super().__init__(parent, **kwargs)
        
        self.result_provider = result_provider
        self.exporter = ExcelExporter()
        
        # Initial state
        self._update_state()
    
    def _on_export_click(self):
        """Handle export button click"""
        result = self.result_provider()
        
        if not result:
            messagebox.showwarning("Kein Ergebnis", 
                                 "Keine Analyseergebnisse zum Exportieren verfügbar.")
            return
        
        # Validate data
        validation = validate_export_data(result)
        
        if not validation['has_exportable_data']:
            response = messagebox.askyesno(
                "Keine strukturierten Daten",
                "Es wurden keine strukturierten Daten zum Exportieren gefunden.\n"
                "Möchten Sie trotzdem eine Zusammenfassung exportieren?"
            )
            if not response:
                return
        
        # Show export dialog
        try:
            dialog = ExcelExportDialog(self.winfo_toplevel(), result)
            self.wait_window(dialog)
            
            # Update state after dialog closes
            self._update_state()
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Öffnen des Export-Dialogs: {str(e)}")
    
    def _update_state(self):
        """Update button state based on available data"""
        result = self.result_provider()
        
        if result:
            validation = validate_export_data(result)
            if validation['has_exportable_data']:
                self.config(state=tk.NORMAL, text='📊 Excel Export')
            else:
                self.config(state=tk.NORMAL, text='📄 Zusammenfassung exportieren')
        else:
            self.config(state=tk.DISABLED, text='📊 Excel Export')
    
    def update_result(self):
        """Update button state when result changes"""
        self._update_state()


def integrate_excel_export_with_action_buttons(action_buttons_frame, result_provider: Callable[[], Optional[ProcessedResult]]):
    """
    Integrate Excel export functionality with existing ActionButtonsFrame.
    
    Args:
        action_buttons_frame: The ActionButtonsFrame instance
        result_provider: Function that returns the current ProcessedResult
    """
    from action_buttons import ActionButton, ActionType
    
    def handle_excel_export():
        """Handle Excel export action"""
        result = result_provider()
        
        if not result:
            messagebox.showwarning("Kein Ergebnis", 
                                 "Keine Analyseergebnisse zum Exportieren verfügbar.")
            return
        
        # Show export dialog
        try:
            dialog = ExcelExportDialog(action_buttons_frame.winfo_toplevel(), result)
            action_buttons_frame.wait_window(dialog)
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Excel-Export: {str(e)}")
    
    # Add Excel export action
    excel_export_action = ActionButton(
        action_type=ActionType.EXPORTIEREN,
        label="Excel Export",
        description="Exportiere strukturierte Daten als Excel-Datei",
        callback=handle_excel_export
    )
    
    action_buttons_frame.add_custom_action(excel_export_action)
    
    # Update context menu
    if hasattr(action_buttons_frame, 'context_menu'):
        action_buttons_frame.context_menu.add_separator()
        action_buttons_frame.context_menu.add_command(
            label="📊 Excel Export",
            command=handle_excel_export
        )


def create_quick_export_function(result: ProcessedResult, parent_window=None) -> bool:
    """
    Quick export function for immediate Excel export without dialog.
    
    Args:
        result: The ProcessedResult to export
        parent_window: Parent window for file dialog
        
    Returns:
        bool: True if export was successful
    """
    try:
        # Generate filename
        filename = create_excel_export_filename(result)
        
        # Get save location
        documents_dir = os.path.expanduser("~/Documents")
        if not os.path.exists(documents_dir):
            documents_dir = os.getcwd()
        
        file_path = filedialog.asksaveasfilename(
            parent=parent_window,
            title="Excel-Datei speichern",
            initialdir=documents_dir,
            initialfile=filename,
            defaultextension=".xlsx",
            filetypes=[
                ("Excel-Dateien", "*.xlsx"),
                ("Alle Dateien", "*.*")
            ]
        )
        
        if not file_path:
            return False
        
        # Perform export
        exporter = ExcelExporter()
        success = exporter.export_to_excel(result, file_path)
        
        if success:
            messagebox.showinfo("Export erfolgreich", 
                              f"Daten erfolgreich exportiert nach:\n{file_path}")
            return True
        else:
            messagebox.showerror("Export fehlgeschlagen", 
                               "Der Export konnte nicht durchgeführt werden.")
            return False
            
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Export: {str(e)}")
        return False