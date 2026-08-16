"""
Integration examples showing how to use progress indicators with file processing modules.

This module demonstrates how to integrate the progress indication system
with existing file handlers and processing operations.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
from typing import List, Optional, Callable
import os
from pathlib import Path

from progress_indicator import (
    ProgressIndicator, StatusFeedback, ProgressManager, ProgressStep,
    OperationType, global_progress_manager, with_progress
)
from excel_handler import ExcelHandler
from image_handler import ImageHandler
from csv_handler import CSVHandler
from chart_generator import ChartGenerator
from data_models import StructuredData, ChartType


class ProgressIntegratedFileProcessor:
    """
    Example class showing how to integrate progress indication with file processing.
    
    This demonstrates the recommended patterns for adding progress feedback
    to long-running operations.
    """
    
    def __init__(self, parent_widget: tk.Widget):
        """Initialize with progress components."""
        self.parent = parent_widget
        
        # Create progress components
        self.progress_indicator = ProgressIndicator(parent_widget, show_details=True)
        self.status_feedback = StatusFeedback(parent_widget)
        
        # Register with global manager
        global_progress_manager.register_indicator("file_processor", self.progress_indicator)
        global_progress_manager.register_status_feedback("file_processor", self.status_feedback)
        
        # File handlers
        self.excel_handler = ExcelHandler()
        self.image_handler = None  # Will initialize if dependencies available
        self.csv_handler = CSVHandler()
        self.chart_generator = ChartGenerator()
        
        # Try to initialize image handler
        try:
            self.image_handler = ImageHandler()
        except ImportError:
            self.status_feedback.show_warning("OCR-Funktionalität nicht verfügbar")
    
    def process_excel_file_with_progress(self, file_path: str, 
                                       progress_callback: Optional[Callable] = None) -> dict:
        """
        Process Excel file with progress indication.
        
        Args:
            file_path: Path to Excel file
            progress_callback: Optional callback for progress updates
            
        Returns:
            Processing results
        """
        steps = [
            ProgressStep("Datei validieren", "Überprüfung der Datei", weight=0.5),
            ProgressStep("Datei-Info laden", "Laden der Dateiinformationen", weight=1.0),
            ProgressStep("Daten extrahieren", "Extraktion der Tabelleninhalte", weight=2.0),
            ProgressStep("Daten strukturieren", "Aufbereitung für Analyse", weight=1.5),
            ProgressStep("Ergebnisse finalisieren", "Abschluss der Verarbeitung", weight=0.5)
        ]
        
        # Start progress indication
        operation_id = global_progress_manager.start_operation(
            "file_processor",
            OperationType.FILE_PROCESSING,
            f"Excel-Datei verarbeiten: {Path(file_path).name}",
            steps
        )
        
        try:
            results = {}
            
            # Step 1: Validate file
            if progress_callback:
                progress_callback(0, "Validiere Datei...")
            global_progress_manager.update_operation(operation_id, 0, "Validiere Datei...")
            
            if not self.excel_handler.can_handle(file_path):
                raise ValueError("Dateiformat wird nicht unterstützt")
            
            time.sleep(0.5)  # Simulate processing time
            
            # Step 2: Load file info
            if progress_callback:
                progress_callback(1, "Lade Datei-Informationen...")
            global_progress_manager.update_operation(operation_id, 1, "Lade Datei-Informationen...")
            
            file_info = self.excel_handler.get_file_info(file_path)
            results['file_info'] = file_info
            
            time.sleep(1.0)  # Simulate processing time
            
            # Step 3: Extract data from each sheet
            if progress_callback:
                progress_callback(2, "Extrahiere Daten...")
            global_progress_manager.update_operation(operation_id, 2, "Extrahiere Daten...")
            
            sheet_data = {}
            for i, sheet in enumerate(file_info.sheets):
                sheet_progress_msg = f"Verarbeite Arbeitsblatt: {sheet.name}"
                global_progress_manager.update_operation(operation_id, 2, sheet_progress_msg)
                
                df = self.excel_handler.read_sheet(file_path, sheet.name)
                sheet_data[sheet.name] = df
                
                time.sleep(0.5)  # Simulate processing time per sheet
            
            results['sheet_data'] = sheet_data
            
            # Step 4: Structure data
            if progress_callback:
                progress_callback(3, "Strukturiere Daten...")
            global_progress_manager.update_operation(operation_id, 3, "Strukturiere Daten...")
            
            structured_data = self.excel_handler.convert_to_structured_data(file_path)
            results['structured_data'] = structured_data
            
            time.sleep(0.8)  # Simulate processing time
            
            # Step 5: Finalize
            if progress_callback:
                progress_callback(4, "Finalisiere Ergebnisse...")
            global_progress_manager.update_operation(operation_id, 4, "Finalisiere Ergebnisse...")
            
            results['summary'] = {
                'total_sheets': len(file_info.sheets),
                'total_rows': sum(sheet.rows for sheet in file_info.sheets),
                'total_columns': sum(sheet.columns for sheet in file_info.sheets),
                'file_size_mb': file_info.file_size / (1024 * 1024)
            }
            
            time.sleep(0.3)  # Simulate processing time
            
            # Complete operation
            global_progress_manager.complete_operation(
                operation_id, 
                f"Excel-Datei erfolgreich verarbeitet: {len(file_info.sheets)} Arbeitsblätter"
            )
            
            return results
            
        except Exception as e:
            # Handle error
            global_progress_manager.show_status(
                "file_processor", 
                f"Fehler bei Excel-Verarbeitung: {str(e)}", 
                "error"
            )
            raise
    
    def process_image_with_ocr_progress(self, file_path: str) -> dict:
        """
        Process image with OCR and progress indication.
        
        Args:
            file_path: Path to image file
            
        Returns:
            OCR results
        """
        if not self.image_handler:
            raise RuntimeError("OCR-Funktionalität nicht verfügbar")
        
        steps = [
            ProgressStep("Bild laden", "Laden und Validierung der Bilddatei", weight=1.0),
            ProgressStep("Bild vorverarbeiten", "Optimierung für OCR", weight=1.5),
            ProgressStep("Text erkennen", "OCR-Texterkennung", weight=3.0),
            ProgressStep("Text nachbearbeiten", "Bereinigung und Strukturierung", weight=1.0)
        ]
        
        operation_id = global_progress_manager.start_operation(
            "file_processor",
            OperationType.OCR_PROCESSING,
            f"OCR-Verarbeitung: {Path(file_path).name}",
            steps
        )
        
        try:
            results = {}
            
            # Step 1: Load and validate image
            global_progress_manager.update_operation(operation_id, 0, "Lade Bilddatei...")
            
            if not self.image_handler.can_handle(file_path):
                raise ValueError("Bildformat wird nicht unterstützt")
            
            image_info = self.image_handler.get_file_info(file_path)
            results['image_info'] = image_info
            
            time.sleep(0.5)
            
            # Step 2: Preprocess image
            global_progress_manager.update_operation(operation_id, 1, "Verarbeite Bild für OCR...")
            
            # Simulate preprocessing time based on image size
            processing_time = min(2.0, image_info.file_size / (1024 * 1024))  # Max 2 seconds
            time.sleep(processing_time)
            
            # Step 3: Perform OCR
            global_progress_manager.update_operation(operation_id, 2, "Erkenne Text im Bild...")
            
            ocr_result = self.image_handler.extract_text(file_path)
            results['ocr_result'] = ocr_result
            
            # Step 4: Post-process text
            global_progress_manager.update_operation(operation_id, 3, "Bereinige erkannten Text...")
            
            # Simulate text processing
            time.sleep(0.5)
            
            results['processed_text'] = ocr_result.text.strip()
            results['confidence'] = ocr_result.confidence
            results['word_count'] = len(ocr_result.text.split())
            
            # Complete operation
            success_msg = f"OCR abgeschlossen: {results['word_count']} Wörter erkannt"
            if ocr_result.confidence < 70:
                success_msg += f" (Niedrige Qualität: {ocr_result.confidence:.1f}%)"
            
            global_progress_manager.complete_operation(operation_id, success_msg)
            
            return results
            
        except Exception as e:
            global_progress_manager.show_status(
                "file_processor", 
                f"Fehler bei OCR-Verarbeitung: {str(e)}", 
                "error"
            )
            raise
    
    def process_multiple_csv_files_with_progress(self, file_paths: List[str]) -> dict:
        """
        Process multiple CSV files with progress indication.
        
        Args:
            file_paths: List of CSV file paths
            
        Returns:
            Combined processing results
        """
        steps = [
            ProgressStep("Dateien validieren", "Überprüfung aller Dateien", weight=0.5),
            ProgressStep("Einzelne Dateien verarbeiten", "Verarbeitung jeder CSV-Datei", weight=3.0),
            ProgressStep("Daten kombinieren", "Zusammenführung der Ergebnisse", weight=1.0),
            ProgressStep("Ergebnisse strukturieren", "Finale Datenaufbereitung", weight=0.5)
        ]
        
        operation_id = global_progress_manager.start_operation(
            "file_processor",
            OperationType.MULTI_FILE,
            f"Verarbeite {len(file_paths)} CSV-Dateien",
            steps
        )
        
        try:
            results = {}
            
            # Step 1: Validate all files
            global_progress_manager.update_operation(operation_id, 0, "Validiere Dateien...")
            
            valid_files = []
            for file_path in file_paths:
                if self.csv_handler.can_handle(file_path):
                    valid_files.append(file_path)
                else:
                    self.status_feedback.show_warning(
                        f"Überspringe nicht unterstützte Datei: {Path(file_path).name}"
                    )
            
            if not valid_files:
                raise ValueError("Keine gültigen CSV-Dateien gefunden")
            
            time.sleep(0.3)
            
            # Step 2: Process individual files
            global_progress_manager.update_operation(operation_id, 1, "Verarbeite Dateien...")
            
            individual_results = {}
            for i, file_path in enumerate(valid_files):
                file_name = Path(file_path).name
                progress_msg = f"Verarbeite {file_name} ({i+1}/{len(valid_files)})"
                global_progress_manager.update_operation(operation_id, 1, progress_msg)
                
                try:
                    csv_info = self.csv_handler.get_file_info(file_path)
                    structured_data = self.csv_handler.convert_to_structured_data(file_path)
                    
                    individual_results[file_path] = {
                        'info': csv_info,
                        'structured_data': structured_data
                    }
                    
                    # Show progress for individual file
                    self.status_feedback.show_info(f"✓ {file_name} verarbeitet", duration=1000)
                    
                except Exception as e:
                    self.status_feedback.show_error(f"Fehler in {file_name}: {str(e)}")
                    individual_results[file_path] = {'error': str(e)}
                
                time.sleep(0.5)  # Simulate processing time
            
            results['individual_results'] = individual_results
            
            # Step 3: Combine data
            global_progress_manager.update_operation(operation_id, 2, "Kombiniere Daten...")
            
            multi_file_result = self.csv_handler.process_multiple_files(valid_files, 'concat')
            results['combined_result'] = multi_file_result
            
            time.sleep(0.8)
            
            # Step 4: Structure final results
            global_progress_manager.update_operation(operation_id, 3, "Strukturiere Ergebnisse...")
            
            results['summary'] = {
                'total_files_processed': len([r for r in individual_results.values() if 'error' not in r]),
                'total_files_with_errors': len([r for r in individual_results.values() if 'error' in r]),
                'combined_rows': len(multi_file_result.combined_data) if multi_file_result.combined_data is not None else 0,
                'combined_columns': len(multi_file_result.combined_data.columns) if multi_file_result.combined_data is not None else 0
            }
            
            time.sleep(0.2)
            
            # Complete operation
            success_msg = f"CSV-Verarbeitung abgeschlossen: {results['summary']['total_files_processed']} Dateien"
            if results['summary']['total_files_with_errors'] > 0:
                success_msg += f" ({results['summary']['total_files_with_errors']} Fehler)"
            
            global_progress_manager.complete_operation(operation_id, success_msg)
            
            return results
            
        except Exception as e:
            global_progress_manager.show_status(
                "file_processor", 
                f"Fehler bei CSV-Verarbeitung: {str(e)}", 
                "error"
            )
            raise
    
    def generate_chart_with_progress(self, structured_data: StructuredData, 
                                   chart_type: ChartType, output_path: str) -> dict:
        """
        Generate chart with progress indication.
        
        Args:
            structured_data: Data to visualize
            chart_type: Type of chart to create
            output_path: Path to save chart
            
        Returns:
            Chart generation results
        """
        steps = [
            ProgressStep("Daten analysieren", "Analyse der Datenstruktur", weight=0.5),
            ProgressStep("Diagramm erstellen", "Generierung der Visualisierung", weight=2.0),
            ProgressStep("Formatierung anwenden", "Styling und Layout", weight=1.0),
            ProgressStep("Datei exportieren", "Speichern der Grafik", weight=0.5)
        ]
        
        operation_id = global_progress_manager.start_operation(
            "file_processor",
            OperationType.CHART_GENERATION,
            f"Erstelle {chart_type.value}-Diagramm",
            steps
        )
        
        try:
            results = {}
            
            # Step 1: Analyze data
            global_progress_manager.update_operation(operation_id, 0, "Analysiere Datenstruktur...")
            
            suggestions = self.chart_generator.suggest_chart_types(structured_data)
            results['suggestions'] = suggestions
            
            time.sleep(0.3)
            
            # Step 2: Create chart
            global_progress_manager.update_operation(operation_id, 1, "Erstelle Diagramm...")
            
            visualization = self.chart_generator.create_chart(
                structured_data, 
                chart_type,
                data_source="user_data"
            )
            results['visualization'] = visualization
            
            time.sleep(1.5)  # Simulate chart generation time
            
            # Step 3: Apply formatting
            global_progress_manager.update_operation(operation_id, 2, "Wende Formatierung an...")
            
            # Simulate formatting time
            time.sleep(0.8)
            
            # Step 4: Export chart
            global_progress_manager.update_operation(operation_id, 3, "Exportiere Diagramm...")
            
            export_success = self.chart_generator.export_chart(
                visualization, 
                output_path,
                format='png',
                dpi=300
            )
            
            if not export_success:
                raise RuntimeError("Diagramm-Export fehlgeschlagen")
            
            results['export_path'] = output_path
            results['export_success'] = export_success
            
            time.sleep(0.4)
            
            # Complete operation
            global_progress_manager.complete_operation(
                operation_id, 
                f"Diagramm erfolgreich erstellt: {Path(output_path).name}"
            )
            
            return results
            
        except Exception as e:
            global_progress_manager.show_status(
                "file_processor", 
                f"Fehler bei Diagramm-Erstellung: {str(e)}", 
                "error"
            )
            raise
    
    def pack_progress_components(self):
        """Pack the progress components into the parent widget."""
        self.status_feedback.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)
        # Progress indicator will be shown automatically when operations start


class ProgressDemoApplication:
    """
    Demo application showing progress indication in action.
    
    This provides a complete example of how to integrate progress indication
    into a Tkinter application with file processing capabilities.
    """
    
    def __init__(self):
        """Initialize the demo application."""
        self.root = tk.Tk()
        self.root.title("Progress Indication Demo")
        self.root.geometry("800x600")
        
        self.setup_ui()
        
        # Initialize file processor with progress
        self.file_processor = ProgressIntegratedFileProcessor(self.main_frame)
        self.file_processor.pack_progress_components()
    
    def setup_ui(self):
        """Set up the user interface."""
        # Main frame
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(
            self.main_frame, 
            text="Progress Indication Demo", 
            font=('Arial', 16, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # Button frame
        button_frame = tk.Frame(self.main_frame)
        button_frame.pack(pady=10)
        
        # Demo buttons
        tk.Button(
            button_frame,
            text="Excel-Datei verarbeiten",
            command=self.demo_excel_processing,
            width=20
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="Bild mit OCR verarbeiten",
            command=self.demo_image_processing,
            width=20
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="Mehrere CSV-Dateien",
            command=self.demo_multi_csv_processing,
            width=20
        ).pack(side=tk.LEFT, padx=5)
        
        # Second button row
        button_frame2 = tk.Frame(self.main_frame)
        button_frame2.pack(pady=5)
        
        tk.Button(
            button_frame2,
            text="Diagramm erstellen",
            command=self.demo_chart_generation,
            width=20
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame2,
            text="Simuliere langen Prozess",
            command=self.demo_long_process,
            width=20
        ).pack(side=tk.LEFT, padx=5)
        
        # Results area
        results_frame = tk.LabelFrame(self.main_frame, text="Ergebnisse")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        self.results_text = tk.Text(results_frame, wrap=tk.WORD)
        scrollbar = tk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        self.results_text.config(yscrollcommand=scrollbar.set)
        
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def demo_excel_processing(self):
        """Demo Excel file processing with progress."""
        file_path = filedialog.askopenfilename(
            title="Excel-Datei auswählen",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        
        if file_path:
            def process_in_thread():
                try:
                    results = self.file_processor.process_excel_file_with_progress(file_path)
                    self.display_results("Excel-Verarbeitung", results)
                except Exception as e:
                    messagebox.showerror("Fehler", f"Excel-Verarbeitung fehlgeschlagen: {str(e)}")
            
            threading.Thread(target=process_in_thread, daemon=True).start()
    
    def demo_image_processing(self):
        """Demo image processing with OCR and progress."""
        file_path = filedialog.askopenfilename(
            title="Bilddatei auswählen",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.pdf"), ("All files", "*.*")]
        )
        
        if file_path:
            def process_in_thread():
                try:
                    results = self.file_processor.process_image_with_ocr_progress(file_path)
                    self.display_results("OCR-Verarbeitung", results)
                except Exception as e:
                    messagebox.showerror("Fehler", f"OCR-Verarbeitung fehlgeschlagen: {str(e)}")
            
            threading.Thread(target=process_in_thread, daemon=True).start()
    
    def demo_multi_csv_processing(self):
        """Demo multiple CSV file processing with progress."""
        file_paths = filedialog.askopenfilenames(
            title="CSV-Dateien auswählen",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_paths:
            def process_in_thread():
                try:
                    results = self.file_processor.process_multiple_csv_files_with_progress(list(file_paths))
                    self.display_results("Multi-CSV-Verarbeitung", results)
                except Exception as e:
                    messagebox.showerror("Fehler", f"CSV-Verarbeitung fehlgeschlagen: {str(e)}")
            
            threading.Thread(target=process_in_thread, daemon=True).start()
    
    def demo_chart_generation(self):
        """Demo chart generation with progress."""
        # Create sample structured data
        from data_models import StructuredData, DataTable
        
        sample_table = DataTable(
            title="Beispieldaten",
            headers=["Kategorie", "Wert"],
            rows=[
                ["A", "10"],
                ["B", "25"],
                ["C", "15"],
                ["D", "30"]
            ]
        )
        
        structured_data = StructuredData(
            tables=[sample_table],
            entities=[],
            numeric_values=[],
            temporal_data=[],
            relationships=[]
        )
        
        output_path = filedialog.asksaveasfilename(
            title="Diagramm speichern als",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if output_path:
            def process_in_thread():
                try:
                    results = self.file_processor.generate_chart_with_progress(
                        structured_data, ChartType.BAR, output_path
                    )
                    self.display_results("Diagramm-Erstellung", results)
                except Exception as e:
                    messagebox.showerror("Fehler", f"Diagramm-Erstellung fehlgeschlagen: {str(e)}")
            
            threading.Thread(target=process_in_thread, daemon=True).start()
    
    def demo_long_process(self):
        """Demo a long-running process with detailed progress."""
        steps = [
            ProgressStep("Initialisierung", "Vorbereitung der Verarbeitung", weight=0.5),
            ProgressStep("Datensammlung", "Sammeln von Informationen", weight=2.0),
            ProgressStep("Verarbeitung Phase 1", "Erste Verarbeitungsphase", weight=3.0),
            ProgressStep("Verarbeitung Phase 2", "Zweite Verarbeitungsphase", weight=2.5),
            ProgressStep("Optimierung", "Optimierung der Ergebnisse", weight=1.5),
            ProgressStep("Finalisierung", "Abschluss der Verarbeitung", weight=0.5)
        ]
        
        def long_process():
            operation_id = global_progress_manager.start_operation(
                "file_processor",
                OperationType.ANALYSIS,
                "Langer Demonstrationsprozess",
                steps
            )
            
            try:
                for i, step in enumerate(steps):
                    global_progress_manager.update_operation(
                        operation_id, i, f"Führe aus: {step.name}"
                    )
                    
                    # Simulate variable processing time based on step weight
                    processing_time = step.weight * 0.8
                    time.sleep(processing_time)
                
                global_progress_manager.complete_operation(
                    operation_id, "Langer Prozess erfolgreich abgeschlossen"
                )
                
                self.display_results("Langer Prozess", {
                    "duration": sum(step.weight * 0.8 for step in steps),
                    "steps_completed": len(steps),
                    "status": "Erfolgreich abgeschlossen"
                })
                
            except Exception as e:
                global_progress_manager.show_status(
                    "file_processor", f"Fehler im langen Prozess: {str(e)}", "error"
                )
        
        threading.Thread(target=long_process, daemon=True).start()
    
    def display_results(self, operation_name: str, results: dict):
        """Display operation results in the text area."""
        self.results_text.insert(tk.END, f"\n=== {operation_name} ===\n")
        
        for key, value in results.items():
            if isinstance(value, dict):
                self.results_text.insert(tk.END, f"{key}:\n")
                for sub_key, sub_value in value.items():
                    self.results_text.insert(tk.END, f"  {sub_key}: {sub_value}\n")
            else:
                self.results_text.insert(tk.END, f"{key}: {value}\n")
        
        self.results_text.insert(tk.END, "\n")
        self.results_text.see(tk.END)
    
    def run(self):
        """Run the demo application."""
        self.root.mainloop()


if __name__ == "__main__":
    # Run the demo application
    app = ProgressDemoApplication()
    app.run()