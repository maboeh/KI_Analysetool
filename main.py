import tkinter as tk
import sys
import os
import logging
from pathlib import Path

__version__ = "2.1.0"

# Im Frozen-Build (PyInstaller) in das schreibbare Benutzer-Datenverzeichnis
# wechseln, damit results.db, results/, logs/ und config.ini dort liegen.
from app_paths import get_data_dir, is_frozen
if is_frozen():
    os.chdir(get_data_dir())

# Configure logging with file handler
_log_dir = Path("logs")
_log_dir.mkdir(exist_ok=True)

# Formatter and handlers
_log_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
_stream_handler = logging.StreamHandler()
_stream_handler.setFormatter(_log_formatter)
_file_handler = logging.FileHandler(_log_dir / "application.log", encoding="utf-8")
_file_handler.setFormatter(_log_formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[_stream_handler, _file_handler]
)

# Mask sensitive values in all log records.
# Imported here so the formatter is set up before any module logs.
from config import SecretFilter
_secret_filter = SecretFilter()
logging.getLogger().addFilter(_secret_filter)


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
        window.title(f"KI Analysetool v{__version__}")

        # Set window icon if available
        try:
            # You can add an icon file here if you have one
            # window.iconbitmap('icon.ico')
            pass
        except tk.TclError:
            pass

        app = Gui(window)

        # Set the window title after GUI init so it includes the version number
        window.title(f"KI Analysetool v{__version__}")

        # Handle window closing
        def on_closing():
            try:
                # Save any pending data
                if hasattr(app, 'results_manager'):
                    # Could add cleanup here
                    pass
            except Exception:
                logging.exception("Fehler beim Aufräumen vor dem Beenden")
            finally:
                # Clear any cached secrets from memory
                try:
                    from config import clear_api_key_cache
                    clear_api_key_cache()
                except Exception:
                    pass
                window.destroy()

        window.protocol("WM_DELETE_WINDOW", on_closing)

        # Start the application
        window.mainloop()

    except Exception:
        logging.exception("Fehler beim Starten der Anwendung")
        print("Fehler beim Starten der Anwendung. Details wurden in logs/application.log geschrieben.")
        input("Drücken Sie Enter zum Beenden...")
        sys.exit(1)


if __name__ == "__main__":
    main()
