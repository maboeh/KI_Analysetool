"""
Results Browser and Management Interface.

This module provides a Tkinter-based GUI for browsing, searching, filtering,
and managing stored analysis results.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
import threading

from results_manager import ResultsManager
from data_models import ResultSummary, ProcessedResult
from help_tooltip import add_help_indicator


class ResultsBrowser:
    """GUI component for browsing and managing stored results."""
    
    def __init__(self, parent, results_manager: ResultsManager, 
                 on_result_selected: Optional[Callable[[ProcessedResult], None]] = None):
        """
        Initialize the results browser.
        
        Args:
            parent: Parent Tkinter widget
            results_manager: ResultsManager instance for data operations
            on_result_selected: Callback function when a result is selected
        """
        self.parent = parent
        self.results_manager = results_manager
        self.on_result_selected = on_result_selected
        
        # Current filter state
        self.current_filters = {}
        self.current_results = []
        self.selected_results = []
        
        self._create_widgets()
        self._load_results()
    
    def _create_widgets(self):
        """Create and layout all GUI widgets."""
        # Main container
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create top toolbar
        self._create_toolbar()
        
        # Create filter panel
        self._create_filter_panel()
        
        # Create results list
        self._create_results_list()
        
        # Create bottom action panel
        self._create_action_panel()
        
        # Create statistics panel
        self._create_statistics_panel()
    
    def _create_toolbar(self):
        """Create the top toolbar with main actions."""
        toolbar_frame = ttk.Frame(self.main_frame)
        toolbar_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Refresh button
        refresh_frame = ttk.Frame(toolbar_frame)
        refresh_frame.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(
            refresh_frame,
            text="🔄 Aktualisieren",
            command=self._refresh_results
        ).pack(side=tk.LEFT)
        add_help_indicator(refresh_frame,
                          "Aktualisiert die Liste der gespeicherten Analyseergebnisse aus der Datenbank.")
        
        # Search entry
        search_label_frame = ttk.Frame(toolbar_frame)
        search_label_frame.pack(side=tk.LEFT, padx=(10, 5))
        ttk.Label(search_label_frame, text="Suchen:").pack(side=tk.LEFT)
        add_help_indicator(search_label_frame,
                          "Durchsucht alle gespeicherten Ergebnisse nach dem eingegebenen Begriff. "
                          "Die Suche erfolgt in Echtzeit während der Eingabe.")
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self._on_search_changed)
        search_entry = ttk.Entry(toolbar_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # Clear search button
        ttk.Button(
            toolbar_frame,
            text="✕",
            command=self._clear_search,
            width=3
        ).pack(side=tk.LEFT)
        
        # Statistics button
        stats_frame = ttk.Frame(toolbar_frame)
        stats_frame.pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(
            stats_frame,
            text="📊 Statistiken",
            command=self._show_statistics
        ).pack(side=tk.LEFT)
        add_help_indicator(stats_frame,
                          "Zeigt statistische Übersichten der gespeicherten Analyseergebnisse an.")
    
    def _create_filter_panel(self):
        """Create the filter panel with various filter options."""
        # Collapsible filter frame
        self.filter_frame = ttk.LabelFrame(self.main_frame, text="Filter")
        self.filter_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Filter controls container
        filter_controls = ttk.Frame(self.filter_frame)
        filter_controls.pack(fill=tk.X, padx=5, pady=5)
        
        # Row 1: Analysis type and source type
        row1 = ttk.Frame(filter_controls)
        row1.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(row1, text="Analyse-Typ:").pack(side=tk.LEFT)
        self.analysis_type_var = tk.StringVar(value="Alle")
        self.analysis_type_combo = ttk.Combobox(
            row1, textvariable=self.analysis_type_var, width=15, state="readonly"
        )
        self.analysis_type_combo.pack(side=tk.LEFT, padx=(5, 15))
        self.analysis_type_combo.bind('<<ComboboxSelected>>', self._on_filter_changed)
        
        ttk.Label(row1, text="Quelle:").pack(side=tk.LEFT)
        self.source_type_var = tk.StringVar(value="Alle")
        self.source_type_combo = ttk.Combobox(
            row1, textvariable=self.source_type_var, width=15, state="readonly"
        )
        self.source_type_combo.pack(side=tk.LEFT, padx=(5, 15))
        self.source_type_combo.bind('<<ComboboxSelected>>', self._on_filter_changed)
        
        # Row 2: Date range and data filters
        row2 = ttk.Frame(filter_controls)
        row2.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(row2, text="Zeitraum:").pack(side=tk.LEFT)
        self.date_range_var = tk.StringVar(value="Alle")
        date_range_combo = ttk.Combobox(
            row2, textvariable=self.date_range_var, width=15, state="readonly",
            values=["Alle", "Heute", "Diese Woche", "Dieser Monat", "Letzten 3 Monate"]
        )
        date_range_combo.pack(side=tk.LEFT, padx=(5, 15))
        date_range_combo.bind('<<ComboboxSelected>>', self._on_filter_changed)
        
        # Checkboxes for data presence
        self.has_viz_var = tk.BooleanVar()
        ttk.Checkbutton(
            row2, text="Mit Visualisierungen", variable=self.has_viz_var,
            command=self._on_filter_changed
        ).pack(side=tk.LEFT, padx=(15, 10))
        
        self.has_export_var = tk.BooleanVar()
        ttk.Checkbutton(
            row2, text="Mit exportierbaren Daten", variable=self.has_export_var,
            command=self._on_filter_changed
        ).pack(side=tk.LEFT, padx=(10, 0))
        
        # Clear filters button
        ttk.Button(
            filter_controls,
            text="Filter zurücksetzen",
            command=self._clear_filters
        ).pack(side=tk.RIGHT, padx=(10, 0))
    
    def _create_results_list(self):
        """Create the main results list with treeview."""
        # Results list frame
        list_frame = ttk.Frame(self.main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Treeview with scrollbars
        tree_frame = ttk.Frame(list_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Define columns
        columns = ("title", "type", "source", "date", "viz", "export")
        self.results_tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", selectmode="extended"
        )
        
        # Configure column headings and widths
        self.results_tree.heading("title", text="Titel")
        self.results_tree.heading("type", text="Typ")
        self.results_tree.heading("source", text="Quelle")
        self.results_tree.heading("date", text="Datum")
        self.results_tree.heading("viz", text="Viz")
        self.results_tree.heading("export", text="Export")
        
        self.results_tree.column("title", width=300, minwidth=200)
        self.results_tree.column("type", width=120, minwidth=80)
        self.results_tree.column("source", width=100, minwidth=80)
        self.results_tree.column("date", width=120, minwidth=100)
        self.results_tree.column("viz", width=50, minwidth=40)
        self.results_tree.column("export", width=60, minwidth=50)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind events
        self.results_tree.bind('<Double-1>', self._on_result_double_click)
        self.results_tree.bind('<<TreeviewSelect>>', self._on_selection_changed)
        
        # Context menu
        self._create_context_menu()
    
    def _create_context_menu(self):
        """Create context menu for results list."""
        self.context_menu = tk.Menu(self.results_tree, tearoff=0)
        self.context_menu.add_command(label="Öffnen", command=self._open_selected_result)
        self.context_menu.add_command(label="Exportieren...", command=self._export_selected_results)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Vergleichen", command=self._compare_selected_results)
        self.context_menu.add_command(label="Kombinieren", command=self._combine_selected_results)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Löschen", command=self._delete_selected_results)
        
        # Bind right-click
        self.results_tree.bind('<Button-2>', self._show_context_menu)  # macOS
        self.results_tree.bind('<Button-3>', self._show_context_menu)  # Windows/Linux
    
    def _create_action_panel(self):
        """Create the bottom action panel with buttons."""
        action_frame = ttk.Frame(self.main_frame)
        action_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Left side - selection info
        self.selection_label = ttk.Label(action_frame, text="Keine Auswahl")
        self.selection_label.pack(side=tk.LEFT)
        
        # Right side - action buttons
        button_frame = ttk.Frame(action_frame)
        button_frame.pack(side=tk.RIGHT)
        
        open_frame = ttk.Frame(button_frame)
        open_frame.pack(side=tk.LEFT, padx=(0, 5))
        self.open_button = ttk.Button(
            open_frame, text="Öffnen", command=self._open_selected_result, state=tk.DISABLED
        )
        self.open_button.pack(side=tk.LEFT)
        add_help_indicator(open_frame,
                          "Öffnet das ausgewählte Analyseergebnis zur Detailansicht.")
        
        export_frame = ttk.Frame(button_frame)
        export_frame.pack(side=tk.LEFT, padx=(0, 5))
        self.export_button = ttk.Button(
            export_frame, text="Exportieren", command=self._export_selected_results, state=tk.DISABLED
        )
        self.export_button.pack(side=tk.LEFT)
        add_help_indicator(export_frame,
                          "Exportiert die ausgewählten Ergebnisse in das gewünschte Format.")
        
        compare_frame = ttk.Frame(button_frame)
        compare_frame.pack(side=tk.LEFT, padx=(0, 5))
        self.compare_button = ttk.Button(
            compare_frame, text="Vergleichen", command=self._compare_selected_results, state=tk.DISABLED
        )
        self.compare_button.pack(side=tk.LEFT)
        add_help_indicator(compare_frame,
                          "Vergleicht zwei oder mehr ausgewählte Ergebnisse miteinander.")
        
        delete_frame = ttk.Frame(button_frame)
        delete_frame.pack(side=tk.LEFT)
        self.delete_button = ttk.Button(
            delete_frame, text="Löschen", command=self._delete_selected_results, state=tk.DISABLED
        )
        self.delete_button.pack(side=tk.LEFT)
        add_help_indicator(delete_frame,
                          "Löscht die ausgewählten Analyseergebnisse endgültig aus der Datenbank.")
    
    def _create_statistics_panel(self):
        """Create statistics display panel (initially hidden)."""
        self.stats_window = None
    
    def _load_results(self):
        """Load and display results based on current filters."""
        try:
            # Build filter criteria
            filter_criteria = self._build_filter_criteria()
            
            # Load results from manager
            self.current_results = self.results_manager.list_results(filter_criteria)
            
            # Update UI
            self._update_results_display()
            self._update_filter_options()
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Laden der Ergebnisse: {str(e)}")
    
    def _build_filter_criteria(self) -> Dict[str, Any]:
        """Build filter criteria dictionary from current filter settings."""
        criteria = {}
        
        # Analysis type filter
        if hasattr(self, 'analysis_type_var') and self.analysis_type_var.get() != "Alle":
            criteria['analysis_type'] = self.analysis_type_var.get()
        
        # Source type filter
        if hasattr(self, 'source_type_var') and self.source_type_var.get() != "Alle":
            criteria['source_type'] = self.source_type_var.get()
        
        # Date range filter
        if hasattr(self, 'date_range_var'):
            date_range = self.date_range_var.get()
            if date_range == "Heute":
                criteria['date_from'] = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            elif date_range == "Diese Woche":
                criteria['date_from'] = datetime.now() - timedelta(days=7)
            elif date_range == "Dieser Monat":
                criteria['date_from'] = datetime.now() - timedelta(days=30)
            elif date_range == "Letzten 3 Monate":
                criteria['date_from'] = datetime.now() - timedelta(days=90)
        
        # Data presence filters
        if hasattr(self, 'has_viz_var') and self.has_viz_var.get():
            criteria['has_visualizations'] = True
        
        if hasattr(self, 'has_export_var') and self.has_export_var.get():
            criteria['has_exportable_data'] = True
        
        # Search text filter
        if hasattr(self, 'search_var') and self.search_var.get().strip():
            criteria['search_text'] = self.search_var.get().strip()
        
        return criteria
    
    def _update_results_display(self):
        """Update the results treeview with current results."""
        # Clear existing items
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # Add current results
        for result in self.current_results:
            # Format date
            date_str = result.created_at.strftime("%d.%m.%Y %H:%M")
            
            # Format boolean indicators
            viz_indicator = "✓" if result.has_visualizations else ""
            export_indicator = "✓" if result.has_exportable_data else ""
            
            # Insert item
            self.results_tree.insert(
                "", tk.END,
                values=(
                    result.title,
                    result.analysis_type,
                    result.source_type,
                    date_str,
                    viz_indicator,
                    export_indicator
                ),
                tags=(result.id,)
            )
    
    def _update_filter_options(self):
        """Update filter combobox options based on available data."""
        # Get unique analysis types
        analysis_types = ["Alle"] + list(set(r.analysis_type for r in self.current_results))
        self.analysis_type_combo['values'] = analysis_types
        
        # Get unique source types
        source_types = ["Alle"] + list(set(r.source_type for r in self.current_results))
        self.source_type_combo['values'] = source_types
    
    def _refresh_results(self):
        """Refresh the results list."""
        self._load_results()

    def refresh_results(self):
        """Öffentliche Methode zum Aktualisieren der Ergebnisliste."""
        self._refresh_results()
    
    def _clear_search(self):
        """Clear the search field."""
        self.search_var.set("")
    
    def _clear_filters(self):
        """Clear all filters and reload results."""
        self.analysis_type_var.set("Alle")
        self.source_type_var.set("Alle")
        self.date_range_var.set("Alle")
        self.has_viz_var.set(False)
        self.has_export_var.set(False)
        self.search_var.set("")
        self._load_results()
    
    def _on_search_changed(self, *args):
        """Handle search text changes."""
        # Debounce search to avoid too many updates
        if hasattr(self, '_search_timer'):
            self.parent.after_cancel(self._search_timer)
        
        self._search_timer = self.parent.after(500, self._load_results)
    
    def _on_filter_changed(self, *args):
        """Handle filter changes."""
        self._load_results()
    
    def _on_selection_changed(self, event):
        """Handle selection changes in the results list."""
        selected_items = self.results_tree.selection()
        self.selected_results = []
        
        # Get selected result IDs
        for item in selected_items:
            tags = self.results_tree.item(item, 'tags')
            if tags:
                result_id = tags[0]
                # Find the result summary
                for result in self.current_results:
                    if result.id == result_id:
                        self.selected_results.append(result)
                        break
        
        # Update UI state
        self._update_action_buttons()
        self._update_selection_label()
    
    def _update_action_buttons(self):
        """Update the state of action buttons based on selection."""
        has_selection = len(self.selected_results) > 0
        single_selection = len(self.selected_results) == 1
        multiple_selection = len(self.selected_results) > 1
        
        # Enable/disable buttons
        self.open_button.config(state=tk.NORMAL if single_selection else tk.DISABLED)
        self.export_button.config(state=tk.NORMAL if has_selection else tk.DISABLED)
        self.compare_button.config(state=tk.NORMAL if multiple_selection else tk.DISABLED)
        self.delete_button.config(state=tk.NORMAL if has_selection else tk.DISABLED)
    
    def _update_selection_label(self):
        """Update the selection info label."""
        count = len(self.selected_results)
        if count == 0:
            text = "Keine Auswahl"
        elif count == 1:
            text = f"1 Ergebnis ausgewählt"
        else:
            text = f"{count} Ergebnisse ausgewählt"
        
        self.selection_label.config(text=text)
    
    def _on_result_double_click(self, event):
        """Handle double-click on result item."""
        if len(self.selected_results) == 1:
            self._open_selected_result()
    
    def _show_context_menu(self, event):
        """Show context menu at cursor position."""
        # Select item under cursor
        item = self.results_tree.identify_row(event.y)
        if item:
            self.results_tree.selection_set(item)
            self._on_selection_changed(None)
            
            # Show context menu
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()
    
    def _open_selected_result(self):
        """Open the selected result."""
        if len(self.selected_results) == 1 and self.on_result_selected:
            result_id = self.selected_results[0].id
            full_result = self.results_manager.load_result(result_id)
            if full_result:
                self.on_result_selected(full_result)
            else:
                messagebox.showerror("Fehler", "Ergebnis konnte nicht geladen werden.")
    
    def _export_selected_results(self):
        """Export selected results."""
        if not self.selected_results:
            return
        
        # Ask for export format
        format_dialog = ExportFormatDialog(self.parent)
        if not format_dialog.result:
            return
        
        export_format = format_dialog.result
        
        # Ask for export directory
        export_dir = filedialog.askdirectory(title="Export-Verzeichnis auswählen")
        if not export_dir:
            return
        
        # Export each selected result
        exported_files = []
        for result_summary in self.selected_results:
            try:
                export_path = self.results_manager.export_result(result_summary.id, export_format)
                if export_path:
                    # Move to selected directory
                    import shutil
                    import os
                    filename = os.path.basename(export_path)
                    new_path = os.path.join(export_dir, filename)
                    shutil.move(export_path, new_path)
                    exported_files.append(new_path)
            except Exception as e:
                messagebox.showerror("Export-Fehler", f"Fehler beim Exportieren von '{result_summary.title}': {str(e)}")
        
        if exported_files:
            messagebox.showinfo("Export erfolgreich", f"{len(exported_files)} Datei(en) exportiert.")
    
    def _compare_selected_results(self):
        """Compare selected results."""
        if len(self.selected_results) < 2:
            messagebox.showwarning("Vergleich", "Bitte wählen Sie mindestens 2 Ergebnisse zum Vergleichen aus.")
            return
        
        # Create comparison window
        ComparisonWindow(self.parent, self.selected_results, self.results_manager)
    
    def _combine_selected_results(self):
        """Combine selected results into a new result."""
        if len(self.selected_results) < 2:
            messagebox.showwarning("Kombinieren", "Bitte wählen Sie mindestens 2 Ergebnisse zum Kombinieren aus.")
            return
        
        # Ask for combination name
        name = tk.simpledialog.askstring("Kombinieren", "Name für das kombinierte Ergebnis:")
        if not name:
            return
        
        try:
            # Load full results
            full_results = []
            for summary in self.selected_results:
                result = self.results_manager.load_result(summary.id)
                if result:
                    full_results.append(result)
            
            # Create combined result
            combined_result = self._create_combined_result(full_results, name)
            
            # Save combined result
            self.results_manager.save_result(combined_result, name)
            
            # Refresh list
            self._refresh_results()
            
            messagebox.showinfo("Kombinieren", "Ergebnisse erfolgreich kombiniert.")
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Kombinieren der Ergebnisse: {str(e)}")
    
    def _create_combined_result(self, results: List[ProcessedResult], name: str) -> ProcessedResult:
        """Create a combined result from multiple results."""
        from data_models import ProcessedResult, ResultMetadata, StructuredData
        
        # Combine content
        combined_content = f"Kombiniertes Ergebnis: {name}\n\n"
        for i, result in enumerate(results, 1):
            combined_content += f"=== Ergebnis {i}: {result.metadata.analysis_type} ===\n"
            combined_content += result.content + "\n\n"
        
        # Combine structured data
        combined_data = StructuredData()
        for result in results:
            combined_data.tables.extend(result.extracted_data.tables)
            combined_data.entities.extend(result.extracted_data.entities)
            combined_data.numeric_values.extend(result.extracted_data.numeric_values)
            combined_data.temporal_data.extend(result.extracted_data.temporal_data)
        
        # Create metadata
        metadata = ResultMetadata(
            analysis_type="kombiniert",
            tags=["kombiniert"] + [r.metadata.analysis_type for r in results]
        )
        
        return ProcessedResult(
            content=combined_content,
            extracted_data=combined_data,
            metadata=metadata
        )
    
    def _delete_selected_results(self):
        """Delete selected results after confirmation."""
        if not self.selected_results:
            return
        
        count = len(self.selected_results)
        message = f"Möchten Sie {count} Ergebnis(se) wirklich löschen? Diese Aktion kann nicht rückgängig gemacht werden."
        
        if messagebox.askyesno("Löschen bestätigen", message):
            deleted_count = 0
            for result_summary in self.selected_results:
                if self.results_manager.delete_result(result_summary.id):
                    deleted_count += 1
            
            # Refresh list
            self._refresh_results()
            
            messagebox.showinfo("Löschen", f"{deleted_count} Ergebnis(se) gelöscht.")
    
    def _show_statistics(self):
        """Show statistics window."""
        if self.stats_window and self.stats_window.winfo_exists():
            self.stats_window.lift()
            return
        
        self.stats_window = StatisticsWindow(self.parent, self.results_manager)


class ExportFormatDialog:
    """Dialog for selecting export format."""
    
    def __init__(self, parent):
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Export-Format auswählen")
        self.dialog.geometry("300x150")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        # Format selection
        ttk.Label(self.dialog, text="Export-Format auswählen:").pack(pady=10)
        
        self.format_var = tk.StringVar(value="json")
        formats = [("JSON", "json"), ("Text", "txt"), ("CSV", "csv")]
        
        for text, value in formats:
            ttk.Radiobutton(
                self.dialog, text=text, variable=self.format_var, value=value
            ).pack(anchor=tk.W, padx=20)
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="OK", command=self._ok_clicked).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Abbrechen", command=self._cancel_clicked).pack(side=tk.LEFT, padx=5)
        
        # Wait for dialog to close
        self.dialog.wait_window()
    
    def _ok_clicked(self):
        self.result = self.format_var.get()
        self.dialog.destroy()
    
    def _cancel_clicked(self):
        self.result = None
        self.dialog.destroy()


class ComparisonWindow:
    """Window for comparing multiple results."""
    
    def __init__(self, parent, result_summaries: List[ResultSummary], results_manager: ResultsManager):
        self.results_manager = results_manager
        
        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title("Ergebnisse vergleichen")
        self.window.geometry("800x600")
        
        # Load full results
        self.results = []
        for summary in result_summaries:
            result = results_manager.load_result(summary.id)
            if result:
                self.results.append(result)
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create comparison interface."""
        # Create notebook for tabbed comparison
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Content comparison tab
        content_frame = ttk.Frame(notebook)
        notebook.add(content_frame, text="Inhalte")
        self._create_content_comparison(content_frame)
        
        # Metadata comparison tab
        metadata_frame = ttk.Frame(notebook)
        notebook.add(metadata_frame, text="Metadaten")
        self._create_metadata_comparison(metadata_frame)
        
        # Data comparison tab
        data_frame = ttk.Frame(notebook)
        notebook.add(data_frame, text="Strukturierte Daten")
        self._create_data_comparison(data_frame)
    
    def _create_content_comparison(self, parent):
        """Create content comparison view."""
        # Create paned window for side-by-side comparison
        paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        for i, result in enumerate(self.results):
            frame = ttk.LabelFrame(paned, text=f"Ergebnis {i+1}: {result.metadata.analysis_type}")
            
            # Text widget with scrollbar
            text_frame = ttk.Frame(frame)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            text_widget = tk.Text(text_frame, wrap=tk.WORD, state=tk.DISABLED)
            scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Insert content
            text_widget.config(state=tk.NORMAL)
            text_widget.insert(tk.END, result.content)
            text_widget.config(state=tk.DISABLED)
            
            paned.add(frame)
    
    def _create_metadata_comparison(self, parent):
        """Create metadata comparison table."""
        # Create treeview for metadata comparison
        columns = ["Eigenschaft"] + [f"Ergebnis {i+1}" for i in range(len(self.results))]
        tree = ttk.Treeview(parent, columns=columns, show="headings")
        
        # Configure columns
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        # Add metadata rows
        metadata_props = [
            ("Analyse-Typ", lambda r: r.metadata.analysis_type),
            ("Verarbeitungszeit", lambda r: f"{r.metadata.processing_time:.2f}s" if r.metadata.processing_time else "N/A"),
            ("Verwendetes Modell", lambda r: r.metadata.model_used or "N/A"),
            ("Token verwendet", lambda r: str(r.metadata.tokens_used) if r.metadata.tokens_used else "N/A"),
            ("Konfidenz", lambda r: f"{r.metadata.confidence_score:.2f}" if r.metadata.confidence_score else "N/A"),
            ("Erstellt am", lambda r: r.created_at.strftime("%d.%m.%Y %H:%M")),
            ("Quelle", lambda r: r.source_info.type if r.source_info else "N/A"),
        ]
        
        for prop_name, prop_getter in metadata_props:
            values = [prop_name] + [prop_getter(result) for result in self.results]
            tree.insert("", tk.END, values=values)
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def _create_data_comparison(self, parent):
        """Create structured data comparison."""
        # Create notebook for different data types
        data_notebook = ttk.Notebook(parent)
        data_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tables comparison
        tables_frame = ttk.Frame(data_notebook)
        data_notebook.add(tables_frame, text="Tabellen")
        self._create_tables_comparison(tables_frame)
        
        # Entities comparison
        entities_frame = ttk.Frame(data_notebook)
        data_notebook.add(entities_frame, text="Entitäten")
        self._create_entities_comparison(entities_frame)
    
    def _create_tables_comparison(self, parent):
        """Create tables comparison view."""
        text_widget = tk.Text(parent, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Display table information
        for i, result in enumerate(self.results):
            text_widget.insert(tk.END, f"=== Ergebnis {i+1} ===\n")
            if result.extracted_data.tables:
                for j, table in enumerate(result.extracted_data.tables):
                    text_widget.insert(tk.END, f"Tabelle {j+1}: {table.title or 'Unbenannt'}\n")
                    text_widget.insert(tk.END, f"Spalten: {', '.join(table.headers)}\n")
                    text_widget.insert(tk.END, f"Zeilen: {len(table.rows)}\n\n")
            else:
                text_widget.insert(tk.END, "Keine Tabellen gefunden.\n\n")
        
        text_widget.config(state=tk.DISABLED)
    
    def _create_entities_comparison(self, parent):
        """Create entities comparison view."""
        text_widget = tk.Text(parent, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Display entity information
        for i, result in enumerate(self.results):
            text_widget.insert(tk.END, f"=== Ergebnis {i+1} ===\n")
            if result.extracted_data.entities:
                entity_types = {}
                for entity in result.extracted_data.entities:
                    if entity.entity_type not in entity_types:
                        entity_types[entity.entity_type] = []
                    entity_types[entity.entity_type].append(entity.text)
                
                for entity_type, entities in entity_types.items():
                    text_widget.insert(tk.END, f"{entity_type.value}: {', '.join(entities)}\n")
            else:
                text_widget.insert(tk.END, "Keine Entitäten gefunden.\n")
            text_widget.insert(tk.END, "\n")
        
        text_widget.config(state=tk.DISABLED)


class StatisticsWindow:
    """Window for displaying results statistics."""
    
    def __init__(self, parent, results_manager: ResultsManager):
        self.results_manager = results_manager
        
        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title("Statistiken")
        self.window.geometry("500x400")
        
        self._create_widgets()
        self._load_statistics()
    
    def _create_widgets(self):
        """Create statistics display widgets."""
        # Main frame with scrollbar
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Statistics text widget
        self.stats_text = tk.Text(main_frame, wrap=tk.WORD, state=tk.DISABLED)
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=scrollbar.set)
        
        self.stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Refresh button
        ttk.Button(
            self.window, text="Aktualisieren", command=self._load_statistics
        ).pack(pady=5)
    
    def _load_statistics(self):
        """Load and display statistics."""
        try:
            stats = self.results_manager.get_statistics()
            
            self.stats_text.config(state=tk.NORMAL)
            self.stats_text.delete(1.0, tk.END)
            
            # General statistics
            self.stats_text.insert(tk.END, "=== Allgemeine Statistiken ===\n\n")
            self.stats_text.insert(tk.END, f"Gesamtanzahl Ergebnisse: {stats['total_results']}\n")
            self.stats_text.insert(tk.END, f"Mit Visualisierungen: {stats['with_visualizations']}\n")
            self.stats_text.insert(tk.END, f"Mit exportierbaren Daten: {stats['with_exportable_data']}\n")
            self.stats_text.insert(tk.END, f"Letzte 7 Tage: {stats['recent_activity']}\n\n")
            
            # By analysis type
            self.stats_text.insert(tk.END, "=== Nach Analyse-Typ ===\n\n")
            for analysis_type, count in stats['by_analysis_type'].items():
                self.stats_text.insert(tk.END, f"{analysis_type}: {count}\n")
            
            self.stats_text.insert(tk.END, "\n")
            
            # By source type
            self.stats_text.insert(tk.END, "=== Nach Quell-Typ ===\n\n")
            for source_type, count in stats['by_source_type'].items():
                self.stats_text.insert(tk.END, f"{source_type}: {count}\n")
            
            self.stats_text.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Laden der Statistiken: {str(e)}")