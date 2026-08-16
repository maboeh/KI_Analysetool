import tkinter as tk
import sys
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def check_dependencies():
    """Check if all required dependencies are available."""
    missing_deps = []
    
    try:
        import pandas
    except ImportError:
        missing_deps.append("pandas")
        
    try:
        import matplotlib
    except ImportError:
        missing_deps.append("matplotlib")
        
    try:
        import openpyxl
    except ImportError:
        missing_deps.append("openpyxl")
        
    # Optional dependencies
    optional_missing = []
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        optional_missing.append("pytesseract/PIL (für OCR-Funktionen)")
        
    if missing_deps:
        print(f"Fehlende erforderliche Abhängigkeiten: {', '.join(missing_deps)}")
        print("Bitte installieren Sie diese mit: pip install " + " ".join(missing_deps))
        return False
        
    if optional_missing:
        print(f"Optionale Abhängigkeiten nicht verfügbar: {', '.join(optional_missing)}")
        print("Einige erweiterte Funktionen sind möglicherweise nicht verfügbar.")
        
    return True

def setup_directories():
    """Set up required directories for the application."""
    # Create analysis_history directory if it doesn't exist
    history_dir = Path("analysis_history")
    history_dir.mkdir(exist_ok=True)
    
    # Create results directory for saved results
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    # Create exports directory
    exports_dir = Path("exports")
    exports_dir.mkdir(exist_ok=True)

def main():
    """Main application entry point."""
    try:
        # Check dependencies
        if not check_dependencies():
            input("Drücken Sie Enter zum Beenden...")
            sys.exit(1)
            
        # Set up directories
        setup_directories()
        
        # Configure matplotlib for tkinter backend
        try:
            import matplotlib
            matplotlib.use('TkAgg')
        except ImportError:
            pass  # matplotlib not available
            
        # Import GUI after dependency checks
        try:
            # Try to import enhanced GUI first
            from enhanced_gui_integration_final import EnhancedGui as Gui
            print("Erweiterte GUI-Funktionen aktiviert")
        except ImportError as e:
            # Fallback to original GUI
            from Gui import Gui
            print("Verwende Standard-GUI (erweiterte Funktionen nicht verfügbar)")
            print(f"Grund: {e}")
        
        # Create and run application
        window = tk.Tk()
        
        # Set window icon if available
        try:
            # You can add an icon file here if you have one
            # window.iconbitmap('icon.ico')
            pass
        except:
            pass
            
        app = Gui(window)
        
        # Handle window closing
        def on_closing():
            try:
                # Save any pending data
                if hasattr(app, 'results_manager'):
                    # Could add cleanup here
                    pass
            except:
                pass
            window.destroy()
            
        window.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Start the application
        window.mainloop()
        
    except Exception as e:
        logging.error(f"Fehler beim Starten der Anwendung: {e}")
        print(f"Fehler beim Starten der Anwendung: {e}")
        input("Drücken Sie Enter zum Beenden...")
        sys.exit(1)

if __name__ == "__main__":
    main()
