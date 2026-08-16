"""
Demo script for the enhanced GUI integration.
Shows how ExtendedInputTabs and DataVisualizationPanel integrate into the main interface.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_gui_integration import EnhancedResultsInterface, EnhancedGuiIntegration
from extended_input_tabs import ExtendedInputTabs
from data_models import ProcessedResult, StructuredData, DataTable, NumericValue, NamedEntity


class EnhancedGuiDemo:
    """Demo application showing enhanced GUI features."""
    
    def __init__(self):
        """Initialize the demo application."""
        self.root = tk.Tk()
        self.root.title("Enhanced GUI Integration Demo")
        self.root.geometry("1200x800")
        
        # Create main layout
        self.create_main_layout()
        
        # Create demo data
        self.create_demo_data()
    
    def create_main_layout(self):
        """Create the main application layout."""
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(
            main_container,
            text="Enhanced GUI Integration Demo",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 10))
        
        # Create paned window for input and results
        paned_window = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Input section
        input_frame = ttk.LabelFrame(paned_window, text="Erweiterte Eingabe-Tabs")
        paned_window.add(input_frame, weight=1)
        
        # Results section
        results_frame = ttk.LabelFrame(paned_window, text="Erweiterte Ergebnis-Anzeige")
        paned_window.add(results_frame, weight=2)
        
        # Create input tabs
        self.create_input_section(input_frame)
        
        # Create results interface
        self.create_results_section(results_frame)
        
        # Control buttons
        self.create_control_buttons(main_container)
    
    def create_input_section(self, parent):
        """Create the input section with extended tabs."""
        try:
            # Create notebook for input tabs
            input_notebook = ttk.Notebook(parent)
            input_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Add basic tabs (simulating existing functionality)
            basic_tab = ttk.Frame(input_notebook)
            input_notebook.add(basic_tab, text="Text")
            
            text_label = ttk.Label(basic_tab, text="Basis-Texteingabe:")
            text_label.pack(anchor=tk.W, padx=5, pady=5)
            
            self.text_input = tk.Text(basic_tab, height=10, wrap=tk.WORD)
            self.text_input.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            self.text_input.insert(1.0, "Geben Sie hier Text für die Analyse ein...")
            
            # Create extended input tabs
            self.extended_tabs = ExtendedInputTabs(
                input_notebook,
                status_callback=self.update_status
            )
            
            self.input_notebook = input_notebook
            
        except Exception as e:
            error_label = ttk.Label(
                parent,
                text=f"Fehler beim Erstellen der Eingabe-Tabs:\n{str(e)}",
                foreground="red"
            )
            error_label.pack(expand=True)
            self.extended_tabs = None
    
    def create_results_section(self, parent):
        """Create the results section with enhanced interface."""
        try:
            self.results_interface = EnhancedResultsInterface(
                parent,
                on_action_triggered=self.handle_action
            )
        except Exception as e:
            error_label = ttk.Label(
                parent,
                text=f"Fehler beim Erstellen der Ergebnis-Anzeige:\n{str(e)}",
                foreground="red"
            )
            error_label.pack(expand=True)
            self.results_interface = None
    
    def create_control_buttons(self, parent):
        """Create control buttons."""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Status label
        self.status_var = tk.StringVar(value="Bereit")
        status_label = ttk.Label(button_frame, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT)
        
        # Demo buttons
        ttk.Button(
            button_frame,
            text="Demo-Ergebnis anzeigen",
            command=self.show_demo_result
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Demo-Daten laden",
            command=self.load_demo_data
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Alles löschen",
            command=self.clear_all
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Handler-Info",
            command=self.show_handler_info
        ).pack(side=tk.RIGHT, padx=5)
    
    def create_demo_data(self):
        """Create demo data for testing."""
        # Create demo structured data
        demo_table = DataTable(
            name="Verkaufsdaten",
            columns=["Monat", "Verkäufe", "Umsatz"],
            rows=[
                {"Monat": "Januar", "Verkäufe": 150, "Umsatz": 15000},
                {"Monat": "Februar", "Verkäufe": 180, "Umsatz": 18000},
                {"Monat": "März", "Verkäufe": 220, "Umsatz": 22000},
                {"Monat": "April", "Verkäufe": 190, "Umsatz": 19000},
                {"Monat": "Mai", "Verkäufe": 250, "Umsatz": 25000}
            ]
        )
        
        demo_entities = [
            NamedEntity(type="PERSON", text="Max Mustermann", confidence=0.95),
            NamedEntity(type="ORG", text="Beispiel GmbH", confidence=0.88),
            NamedEntity(type="LOC", text="Berlin", confidence=0.92)
        ]
        
        demo_numeric_values = [
            NumericValue(value=15000, unit="EUR", context="Umsatz Januar"),
            NumericValue(value=250, unit="Stück", context="Verkäufe Mai"),
            NumericValue(value=99000, unit="EUR", context="Gesamtumsatz")
        ]
        
        self.demo_structured_data = StructuredData(
            tables=[demo_table],
            entities=demo_entities,
            numeric_values=demo_numeric_values,
            temporal_data=[]
        )
        
        # Create demo result
        self.demo_result = ProcessedResult(
            id="demo_result_1",
            content="""# Verkaufsanalyse Q1 2024

## Zusammenfassung

Die Verkaufsanalyse für das erste Quartal 2024 zeigt **positive Trends** in allen Bereichen:

### Wichtige Erkenntnisse:

- **Umsatzsteigerung**: 67% Wachstum von Januar bis Mai
- **Verkaufszahlen**: Kontinuierlicher Anstieg mit Peak im Mai (250 Verkäufe)
- **Durchschnittlicher Verkaufswert**: 100 EUR pro Verkauf

### Monatliche Entwicklung:

| Monat | Verkäufe | Umsatz |
|-------|----------|--------|
| Januar | 150 | 15.000 EUR |
| Februar | 180 | 18.000 EUR |
| März | 220 | 22.000 EUR |
| April | 190 | 19.000 EUR |
| Mai | 250 | 25.000 EUR |

### Empfehlungen:

1. **Marketing intensivieren** in erfolgreichen Monaten
2. **Lagerbestände** für Mai-ähnliche Nachfrage vorbereiten
3. **Kundenbindung** durch gezielte Aktionen stärken

Die Daten zeigen eine **sehr positive Entwicklung** mit großem Potenzial für das restliche Jahr.
""",
            structured_data=self.demo_structured_data,
            created_at=datetime.now()
        )
    
    def show_demo_result(self):
        """Show the demo result in the enhanced interface."""
        if self.results_interface:
            try:
                self.results_interface.display_result(self.demo_result)
                self.update_status("Demo-Ergebnis angezeigt")
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Anzeigen des Demo-Ergebnisses: {e}")
        else:
            messagebox.showwarning("Warnung", "Ergebnis-Interface nicht verfügbar")
    
    def load_demo_data(self):
        """Load demo data into visualization panel."""
        if self.results_interface and hasattr(self.results_interface, 'visualization_panel'):
            try:
                if self.results_interface.visualization_panel:
                    self.results_interface.visualization_panel.load_data(self.demo_structured_data)
                    self.update_status("Demo-Daten in Visualisierung geladen")
                else:
                    messagebox.showwarning("Warnung", "Visualisierungs-Panel nicht verfügbar")
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Laden der Demo-Daten: {e}")
        else:
            messagebox.showwarning("Warnung", "Visualisierungs-Interface nicht verfügbar")
    
    def clear_all(self):
        """Clear all displayed content."""
        if self.results_interface:
            try:
                self.results_interface.clear()
                self.update_status("Alle Inhalte gelöscht")
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Löschen: {e}")
        
        # Clear text input
        if hasattr(self, 'text_input'):
            self.text_input.delete(1.0, tk.END)
            self.text_input.insert(1.0, "Geben Sie hier Text für die Analyse ein...")
    
    def show_handler_info(self):
        """Show information about available file handlers."""
        if self.extended_tabs:
            try:
                handler_info = self.extended_tabs.get_handler_info()
                
                info_window = tk.Toplevel(self.root)
                info_window.title("Handler-Information")
                info_window.geometry("500x400")
                
                text_widget = tk.Text(info_window, wrap=tk.WORD)
                text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                
                # Format handler info
                info_text = "=== Verfügbare Datei-Handler ===\n\n"
                
                if 'available_handlers' in handler_info:
                    info_text += f"Handler: {', '.join(handler_info['available_handlers'])}\n\n"
                
                if 'supported_extensions' in handler_info:
                    info_text += "Unterstützte Dateiformate:\n"
                    for handler_type, extensions in handler_info['supported_extensions'].items():
                        info_text += f"  {handler_type}: {', '.join(extensions)}\n"
                
                if 'handler_details' in handler_info:
                    info_text += "\nHandler-Details:\n"
                    for handler_type, details in handler_info['handler_details'].items():
                        info_text += f"  {handler_type}:\n"
                        for key, value in details.items():
                            info_text += f"    {key}: {value}\n"
                
                text_widget.insert(1.0, info_text)
                text_widget.config(state=tk.DISABLED)
                
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Abrufen der Handler-Info: {e}")
        else:
            messagebox.showwarning("Warnung", "Erweiterte Eingabe-Tabs nicht verfügbar")
    
    def handle_action(self, action_type: str, result: ProcessedResult):
        """Handle action button clicks."""
        self.update_status(f"Aktion ausgeführt: {action_type}")
        
        # Show action details
        messagebox.showinfo(
            "Aktion ausgeführt",
            f"Aktion: {action_type}\n"
            f"Ergebnis-ID: {result.id}\n"
            f"Zeitpunkt: {result.created_at.strftime('%H:%M:%S')}"
        )
    
    def update_status(self, message: str):
        """Update status message."""
        self.status_var.set(f"{datetime.now().strftime('%H:%M:%S')} - {message}")
    
    def run(self):
        """Run the demo application."""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.root.quit()


def main():
    """Main function to run the demo."""
    print("Starting Enhanced GUI Integration Demo...")
    print("This demo shows the new ExtendedInputTabs and DataVisualizationPanel features.")
    print("Note: Some features may not be available if dependencies are missing.")
    print()
    
    try:
        demo = EnhancedGuiDemo()
        demo.run()
    except Exception as e:
        print(f"Error starting demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()