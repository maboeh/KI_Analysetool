"""
Visualization panel for displaying charts in the Tkinter interface.

This module provides the DataVisualizationPanel class that integrates
matplotlib charts into the existing Tkinter GUI and handles chart
display, customization, and export functionality.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import os
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass

from chart_generator import ChartGenerator, InteractiveChart
from data_models import (
    StructuredData, ChartType, ChartConfig, Visualization, 
    ProcessedResult
)


@dataclass
class ChartCustomization:
    """Configuration for chart customization options."""
    title: str = ""
    x_label: str = ""
    y_label: str = ""
    color_scheme: str = "default"
    chart_style: str = "seaborn-v0_8"
    width: int = 10
    height: int = 6
    show_grid: bool = True
    show_legend: bool = True


class DataVisualizationPanel:
    """
    Panel for displaying and managing chart visualizations in Tkinter.
    
    This class provides a complete interface for chart display, customization,
    and export functionality integrated into the existing GUI.
    """
    
    def __init__(self, parent_widget, on_chart_created: Optional[Callable] = None):
        """
        Initialize the visualization panel.
        
        Args:
            parent_widget: Parent Tkinter widget
            on_chart_created: Optional callback when a chart is created
        """
        self.parent = parent_widget
        self.on_chart_created = on_chart_created
        
        # Initialize chart generator
        self.chart_generator = ChartGenerator()
        
        # Current state
        self.current_data: Optional[StructuredData] = None
        self.current_visualization: Optional[Visualization] = None
        self.current_canvas: Optional[FigureCanvasTkAgg] = None
        self.current_toolbar: Optional[NavigationToolbar2Tk] = None
        
        # Chart customization
        self.customization = ChartCustomization()
        
        # Create the UI
        self._create_ui()
    
    def _create_ui(self):
        """Create the visualization panel UI."""
        # Main container
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create notebook for tabbed interface
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Chart display tab
        self.chart_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.chart_frame, text="Diagramm")
        
        # Chart customization tab
        self.custom_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.custom_frame, text="Anpassungen")
        
        # Chart suggestions tab
        self.suggestions_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.suggestions_frame, text="Vorschläge")
        
        # Create chart display area
        self._create_chart_display()
        
        # Create customization controls
        self._create_customization_controls()
        
        # Create suggestions area
        self._create_suggestions_area()
    
    def _create_chart_display(self):
        """Create the main chart display area."""
        # Control buttons frame
        control_frame = ttk.Frame(self.chart_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Export buttons
        ttk.Button(
            control_frame,
            text="PNG exportieren",
            command=lambda: self._export_chart('png')
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            control_frame,
            text="PDF exportieren", 
            command=lambda: self._export_chart('pdf')
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            control_frame,
            text="SVG exportieren",
            command=lambda: self._export_chart('svg')
        ).pack(side=tk.LEFT, padx=2)
        
        # Separator
        ttk.Separator(control_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Chart type selection
        ttk.Label(control_frame, text="Diagrammtyp:").pack(side=tk.LEFT, padx=2)
        
        self.chart_type_var = tk.StringVar(value="BAR")
        self.chart_type_combo = ttk.Combobox(
            control_frame,
            textvariable=self.chart_type_var,
            values=["BAR", "LINE", "PIE", "SCATTER", "HISTOGRAM"],
            state="readonly",
            width=12
        )
        self.chart_type_combo.pack(side=tk.LEFT, padx=2)
        self.chart_type_combo.bind('<<ComboboxSelected>>', self._on_chart_type_changed)
        
        # Refresh button
        ttk.Button(
            control_frame,
            text="Aktualisieren",
            command=self._refresh_chart
        ).pack(side=tk.LEFT, padx=2)
        
        # Chart container frame
        self.chart_container = ttk.Frame(self.chart_frame)
        self.chart_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Placeholder label
        self.placeholder_label = ttk.Label(
            self.chart_container,
            text="Keine Daten für Visualisierung verfügbar.\nLaden Sie Daten mit numerischen Werten.",
            font=("Arial", 12),
            foreground="gray"
        )
        self.placeholder_label.pack(expand=True)
    
    def _create_customization_controls(self):
        """Create chart customization controls."""
        # Scrollable frame for customization options
        canvas = tk.Canvas(self.custom_frame)
        scrollbar = ttk.Scrollbar(self.custom_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Title customization
        title_frame = ttk.LabelFrame(scrollable_frame, text="Titel und Beschriftungen")
        title_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(title_frame, text="Titel:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.title_var = tk.StringVar(value=self.customization.title)
        ttk.Entry(title_frame, textvariable=self.title_var, width=40).grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(title_frame, text="X-Achse:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.x_label_var = tk.StringVar(value=self.customization.x_label)
        ttk.Entry(title_frame, textvariable=self.x_label_var, width=40).grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(title_frame, text="Y-Achse:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.y_label_var = tk.StringVar(value=self.customization.y_label)
        ttk.Entry(title_frame, textvariable=self.y_label_var, width=40).grid(row=2, column=1, padx=5, pady=2)
        
        # Style customization
        style_frame = ttk.LabelFrame(scrollable_frame, text="Stil und Farben")
        style_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(style_frame, text="Farbschema:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.color_scheme_var = tk.StringVar(value=self.customization.color_scheme)
        color_combo = ttk.Combobox(
            style_frame,
            textvariable=self.color_scheme_var,
            values=["default", "pastel", "dark", "professional"],
            state="readonly"
        )
        color_combo.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(style_frame, text="Stil:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.style_var = tk.StringVar(value=self.customization.chart_style)
        style_combo = ttk.Combobox(
            style_frame,
            textvariable=self.style_var,
            values=["seaborn-v0_8", "classic", "ggplot", "bmh", "fivethirtyeight"],
            state="readonly"
        )
        style_combo.grid(row=1, column=1, padx=5, pady=2)
        
        # Size customization
        size_frame = ttk.LabelFrame(scrollable_frame, text="Größe")
        size_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(size_frame, text="Breite:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.width_var = tk.IntVar(value=self.customization.width)
        width_spin = ttk.Spinbox(size_frame, from_=5, to=20, textvariable=self.width_var, width=10)
        width_spin.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(size_frame, text="Höhe:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.height_var = tk.IntVar(value=self.customization.height)
        height_spin = ttk.Spinbox(size_frame, from_=3, to=15, textvariable=self.height_var, width=10)
        height_spin.grid(row=1, column=1, padx=5, pady=2)
        
        # Options
        options_frame = ttk.LabelFrame(scrollable_frame, text="Optionen")
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.grid_var = tk.BooleanVar(value=self.customization.show_grid)
        ttk.Checkbutton(options_frame, text="Gitter anzeigen", variable=self.grid_var).pack(anchor=tk.W, padx=5, pady=2)
        
        self.legend_var = tk.BooleanVar(value=self.customization.show_legend)
        ttk.Checkbutton(options_frame, text="Legende anzeigen", variable=self.legend_var).pack(anchor=tk.W, padx=5, pady=2)
        
        # Apply button
        ttk.Button(
            scrollable_frame,
            text="Änderungen anwenden",
            command=self._apply_customization
        ).pack(pady=10)
    
    def _create_suggestions_area(self):
        """Create chart suggestions area."""
        # Instructions
        instructions = ttk.Label(
            self.suggestions_frame,
            text="Automatische Diagrammvorschläge basierend auf Ihren Daten:",
            font=("Arial", 10, "bold")
        )
        instructions.pack(pady=10)
        
        # Suggestions list frame
        self.suggestions_list_frame = ttk.Frame(self.suggestions_frame)
        self.suggestions_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Placeholder for suggestions
        self.suggestions_placeholder = ttk.Label(
            self.suggestions_list_frame,
            text="Laden Sie Daten, um Diagrammvorschläge zu erhalten.",
            foreground="gray"
        )
        self.suggestions_placeholder.pack(expand=True)
    
    def load_data(self, data: StructuredData):
        """
        Load structured data for visualization.
        
        Args:
            data: StructuredData object containing the data to visualize
        """
        self.current_data = data
        
        # Update suggestions
        self._update_suggestions()
        
        # Try to create a default chart if data is available
        if data.has_visualizable_data():
            self._create_default_chart()
        else:
            self._show_no_data_message()
    
    def _update_suggestions(self):
        """Update the chart suggestions based on current data."""
        # Clear existing suggestions
        for widget in self.suggestions_list_frame.winfo_children():
            widget.destroy()
        
        if not self.current_data or not self.current_data.has_visualizable_data():
            self.suggestions_placeholder = ttk.Label(
                self.suggestions_list_frame,
                text="Keine visualisierbaren Daten verfügbar.",
                foreground="gray"
            )
            self.suggestions_placeholder.pack(expand=True)
            return
        
        # Get suggestions from chart generator
        suggestions = self.chart_generator.suggest_chart_types(self.current_data)
        
        if not suggestions:
            self.suggestions_placeholder = ttk.Label(
                self.suggestions_list_frame,
                text="Keine Diagrammvorschläge verfügbar.",
                foreground="gray"
            )
            self.suggestions_placeholder.pack(expand=True)
            return
        
        # Create suggestion buttons
        for i, suggestion in enumerate(suggestions[:5]):  # Show top 5 suggestions
            suggestion_frame = ttk.Frame(self.suggestions_list_frame)
            suggestion_frame.pack(fill=tk.X, pady=2)
            
            # Suggestion info
            info_text = f"{suggestion.chart_type.value.upper()} ({suggestion.confidence:.0%})"
            ttk.Label(suggestion_frame, text=info_text, font=("Arial", 9, "bold")).pack(side=tk.LEFT)
            
            # Create button
            ttk.Button(
                suggestion_frame,
                text="Erstellen",
                command=lambda s=suggestion: self._create_suggested_chart(s)
            ).pack(side=tk.RIGHT)
            
            # Reasoning
            ttk.Label(
                suggestion_frame,
                text=suggestion.reasoning,
                font=("Arial", 8),
                foreground="gray"
            ).pack(side=tk.LEFT, padx=10)
    
    def _create_default_chart(self):
        """Create a default chart from the current data."""
        if not self.current_data:
            return
        
        # Get the best suggestion
        suggestions = self.chart_generator.suggest_chart_types(self.current_data)
        if suggestions:
            self._create_suggested_chart(suggestions[0])
        else:
            # Fallback to bar chart
            try:
                config = ChartConfig(
                    title="Datenvisualisierung",
                    size=(self.customization.width, self.customization.height)
                )
                self._create_chart(ChartType.BAR, config)
            except Exception as e:
                self._show_error_message(f"Fehler beim Erstellen des Diagramms: {e}")
    
    def _create_suggested_chart(self, suggestion):
        """Create a chart from a suggestion."""
        try:
            self._create_chart(suggestion.chart_type, suggestion.suggested_config)
            
            # Update chart type selection
            self.chart_type_var.set(suggestion.chart_type.value.upper())
            
        except Exception as e:
            self._show_error_message(f"Fehler beim Erstellen des vorgeschlagenen Diagramms: {e}")
    
    def _create_chart(self, chart_type: ChartType, config: Optional[ChartConfig] = None):
        """Create and display a chart."""
        if not self.current_data:
            self._show_error_message("Keine Daten verfügbar")
            return
        
        if config is None:
            config = self._get_current_config()
        
        try:
            # Create visualization
            self.current_visualization = self.chart_generator.create_chart(
                self.current_data,
                chart_type,
                config
            )
            
            # Display the chart
            self._display_chart()
            
            # Notify callback
            if self.on_chart_created:
                self.on_chart_created(self.current_visualization)
                
        except Exception as e:
            self._show_error_message(f"Fehler beim Erstellen des Diagramms: {e}")
    
    def _display_chart(self):
        """Display the current visualization in the chart container."""
        # Clear existing chart
        self._clear_chart_display()
        
        if not self.current_visualization or not hasattr(self.current_visualization, '_figure'):
            return
        
        # Create canvas
        self.current_canvas = FigureCanvasTkAgg(
            self.current_visualization._figure,
            self.chart_container
        )
        self.current_canvas.draw()
        self.current_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Create toolbar
        toolbar_frame = ttk.Frame(self.chart_container)
        toolbar_frame.pack(fill=tk.X)
        
        self.current_toolbar = NavigationToolbar2Tk(self.current_canvas, toolbar_frame)
        self.current_toolbar.update()
    
    def _clear_chart_display(self):
        """Clear the current chart display."""
        # Hide placeholder
        if hasattr(self, 'placeholder_label'):
            self.placeholder_label.pack_forget()
        
        # Clear existing canvas and toolbar
        for widget in self.chart_container.winfo_children():
            widget.destroy()
        
        self.current_canvas = None
        self.current_toolbar = None
    
    def _get_current_config(self) -> ChartConfig:
        """Get current chart configuration from UI controls."""
        return ChartConfig(
            title=self.title_var.get(),
            x_label=self.x_label_var.get(),
            y_label=self.y_label_var.get(),
            colors=self.chart_generator.color_schemes.get(self.color_scheme_var.get()),
            style=self.style_var.get(),
            size=(self.width_var.get(), self.height_var.get())
        )
    
    def _apply_customization(self):
        """Apply current customization settings."""
        # Update customization object
        self.customization.title = self.title_var.get()
        self.customization.x_label = self.x_label_var.get()
        self.customization.y_label = self.y_label_var.get()
        self.customization.color_scheme = self.color_scheme_var.get()
        self.customization.chart_style = self.style_var.get()
        self.customization.width = self.width_var.get()
        self.customization.height = self.height_var.get()
        self.customization.show_grid = self.grid_var.get()
        self.customization.show_legend = self.legend_var.get()
        
        # Refresh chart with new settings
        self._refresh_chart()
    
    def _refresh_chart(self):
        """Refresh the current chart with updated settings."""
        if not self.current_data:
            return
        
        chart_type_str = self.chart_type_var.get()
        try:
            chart_type = ChartType(chart_type_str.lower())
        except ValueError:
            chart_type = ChartType.BAR
        
        config = self._get_current_config()
        self._create_chart(chart_type, config)
    
    def _on_chart_type_changed(self, event=None):
        """Handle chart type selection change."""
        self._refresh_chart()
    
    def _export_chart(self, format: str):
        """Export the current chart to file."""
        if not self.current_visualization:
            messagebox.showwarning("Warnung", "Kein Diagramm zum Exportieren verfügbar.")
            return
        
        # File dialog
        file_extensions = {
            'png': [('PNG Dateien', '*.png')],
            'pdf': [('PDF Dateien', '*.pdf')],
            'svg': [('SVG Dateien', '*.svg')]
        }
        
        filename = filedialog.asksaveasfilename(
            title=f"Diagramm als {format.upper()} speichern",
            filetypes=file_extensions.get(format, [('Alle Dateien', '*.*')]),
            defaultextension=f'.{format}'
        )
        
        if filename:
            try:
                success = self.chart_generator.export_chart(
                    self.current_visualization,
                    filename,
                    format=format,
                    dpi=300
                )
                
                if success:
                    messagebox.showinfo("Erfolg", f"Diagramm erfolgreich als {filename} gespeichert.")
                else:
                    messagebox.showerror("Fehler", "Fehler beim Speichern des Diagramms.")
                    
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Exportieren: {e}")
    
    def _show_no_data_message(self):
        """Show message when no visualizable data is available."""
        self._clear_chart_display()
        
        # Recreate placeholder label if it doesn't exist or was destroyed
        try:
            self.placeholder_label.pack(expand=True)
        except (AttributeError, tk.TclError):
            self.placeholder_label = ttk.Label(
                self.chart_container,
                text="Keine Daten für Visualisierung verfügbar.\nLaden Sie Daten mit numerischen Werten.",
                font=("Arial", 12),
                foreground="gray"
            )
            self.placeholder_label.pack(expand=True)
    
    def _show_error_message(self, message: str):
        """Show error message to user."""
        messagebox.showerror("Fehler", message)
    
    def get_current_visualization(self) -> Optional[Visualization]:
        """Get the currently displayed visualization."""
        return self.current_visualization
    
    def clear(self):
        """Clear all data and charts."""
        self.current_data = None
        self.current_visualization = None
        self._clear_chart_display()
        self._show_no_data_message()
        
        # Clear suggestions
        try:
            for widget in self.suggestions_list_frame.winfo_children():
                widget.destroy()
            
            self.suggestions_placeholder = ttk.Label(
                self.suggestions_list_frame,
                text="Laden Sie Daten, um Diagrammvorschläge zu erhalten.",
                foreground="gray"
            )
            self.suggestions_placeholder.pack(expand=True)
        except tk.TclError:
            # Widget may have been destroyed already
            pass


class ChartExportDialog:
    """Dialog for advanced chart export options."""
    
    def __init__(self, parent, visualization: Visualization):
        """Initialize the export dialog."""
        self.parent = parent
        self.visualization = visualization
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Diagramm Export Optionen")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_ui()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def _create_ui(self):
        """Create the export dialog UI."""
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Format selection
        format_frame = ttk.LabelFrame(main_frame, text="Export Format")
        format_frame.pack(fill=tk.X, pady=5)
        
        self.format_var = tk.StringVar(value="png")
        formats = [("PNG (Raster)", "png"), ("PDF (Vektor)", "pdf"), ("SVG (Vektor)", "svg")]
        
        for text, value in formats:
            ttk.Radiobutton(
                format_frame,
                text=text,
                variable=self.format_var,
                value=value
            ).pack(anchor=tk.W, padx=5, pady=2)
        
        # Quality settings
        quality_frame = ttk.LabelFrame(main_frame, text="Qualität")
        quality_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(quality_frame, text="DPI (nur für PNG):").pack(anchor=tk.W, padx=5)
        self.dpi_var = tk.IntVar(value=300)
        dpi_frame = ttk.Frame(quality_frame)
        dpi_frame.pack(fill=tk.X, padx=5, pady=2)
        
        for dpi in [150, 300, 600]:
            ttk.Radiobutton(
                dpi_frame,
                text=str(dpi),
                variable=self.dpi_var,
                value=dpi
            ).pack(side=tk.LEFT, padx=5)
        
        # Size settings
        size_frame = ttk.LabelFrame(main_frame, text="Größe")
        size_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(size_frame, text="Breite (Zoll):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.width_var = tk.DoubleVar(value=10.0)
        ttk.Spinbox(size_frame, from_=1, to=20, increment=0.5, textvariable=self.width_var, width=10).grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(size_frame, text="Höhe (Zoll):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.height_var = tk.DoubleVar(value=6.0)
        ttk.Spinbox(size_frame, from_=1, to=15, increment=0.5, textvariable=self.height_var, width=10).grid(row=1, column=1, padx=5, pady=2)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            button_frame,
            text="Exportieren",
            command=self._export
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Abbrechen",
            command=self._cancel
        ).pack(side=tk.RIGHT)
    
    def _export(self):
        """Handle export button click."""
        self.result = {
            'format': self.format_var.get(),
            'dpi': self.dpi_var.get(),
            'size': (self.width_var.get(), self.height_var.get())
        }
        self.dialog.destroy()
    
    def _cancel(self):
        """Handle cancel button click."""
        self.result = None
        self.dialog.destroy()
    
    def show(self):
        """Show the dialog and return the result."""
        self.dialog.wait_window()
        return self.result