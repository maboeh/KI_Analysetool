"""
Extended input tabs for new file format support.
Provides Excel upload, image upload with OCR preview, and multi-file selection with drag-and-drop.
"""

import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext, messagebox
import os
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable
import threading
import logging

# Import file handlers
from file_handler_router import FileHandlerRouter
from excel_handler import ExcelHandler
from image_handler import ImageHandler
from csv_handler import CSVHandler


class ExtendedInputTabs:
    """Extended input tabs with support for Excel, images, CSV, and multi-file processing."""
    
    def __init__(self, parent_notebook: ttk.Notebook, status_callback: Optional[Callable] = None, analysis_callback: Optional[Callable] = None):
        """
        Initialize extended input tabs.
        
        Args:
            parent_notebook: The notebook widget to add tabs to
            status_callback: Optional callback for status updates
            analysis_callback: Optional callback(content, source_path, analysis_type) for analysis requests
        """
        self.parent_notebook = parent_notebook
        self.status_callback = status_callback or (lambda msg: None)
        self.analysis_callback = analysis_callback or (lambda content, source, atype: None)
        
        # Initialize file handler router
        try:
            self.file_router = FileHandlerRouter()
        except Exception as e:
            logging.error(f"Failed to initialize file router: {e}")
            self.file_router = None
        
        # State variables
        self.selected_files: List[str] = []
        self.current_excel_file: Optional[str] = None
        self.current_excel_sheets: List[str] = []
        self.current_image_file: Optional[str] = None
        self.current_csv_files: List[str] = []
        
        # Preview data
        self.excel_preview_data: Optional[Dict] = None
        self.image_preview_text: str = ""
        self.csv_preview_data: Optional[Dict] = None
        
        # Setup tabs
        self.setup_excel_tab()
        self.setup_image_tab()
        self.setup_csv_tab()
        self.setup_multi_file_tab()
    
    def setup_excel_tab(self):
        """Setup Excel file upload tab with preview functionality."""
        excel_tab = ttk.Frame(self.parent_notebook, padding=10)
        self.parent_notebook.add(excel_tab, text="Excel")
        
        # File selection section
        file_frame = ttk.LabelFrame(excel_tab, text="Excel-Datei auswählen", padding=10)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        # File path display
        self.excel_file_var = tk.StringVar()
        self.excel_file_label = ttk.Label(file_frame, textvariable=self.excel_file_var, 
                                         wraplength=400, foreground="blue")
        self.excel_file_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Upload button
        upload_btn = ttk.Button(file_frame, text="Excel-Datei auswählen", 
                               command=self.select_excel_file)
        upload_btn.pack(anchor=tk.W)
        
        # Sheet selection section
        sheet_frame = ttk.LabelFrame(excel_tab, text="Arbeitsblatt auswählen", padding=10)
        sheet_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.excel_sheet_var = tk.StringVar()
        self.excel_sheet_combo = ttk.Combobox(sheet_frame, textvariable=self.excel_sheet_var,
                                             state="readonly", width=40)
        self.excel_sheet_combo.pack(anchor=tk.W, pady=(0, 5))
        self.excel_sheet_combo.bind('<<ComboboxSelected>>', self.on_excel_sheet_selected)
        
        # Preview section
        preview_frame = ttk.LabelFrame(excel_tab, text="Datenvorschau", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview for tabular preview
        self.excel_tree = ttk.Treeview(preview_frame, height=8)
        excel_scrollbar_y = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.excel_tree.yview)
        excel_scrollbar_x = ttk.Scrollbar(preview_frame, orient=tk.HORIZONTAL, command=self.excel_tree.xview)
        self.excel_tree.configure(yscrollcommand=excel_scrollbar_y.set, xscrollcommand=excel_scrollbar_x.set)
        
        self.excel_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        excel_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        excel_scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Info label
        self.excel_info_var = tk.StringVar()
        self.excel_info_label = ttk.Label(preview_frame, textvariable=self.excel_info_var)
        self.excel_info_label.pack(anchor=tk.W, pady=(5, 0))
    
    def setup_image_tab(self):
        """Setup image upload tab with OCR preview."""
        image_tab = ttk.Frame(self.parent_notebook, padding=10)
        self.parent_notebook.add(image_tab, text="Bild/PDF")
        
        # File selection section
        file_frame = ttk.LabelFrame(image_tab, text="Bild- oder PDF-Datei auswählen", padding=10)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        # File path display
        self.image_file_var = tk.StringVar()
        self.image_file_label = ttk.Label(file_frame, textvariable=self.image_file_var,
                                         wraplength=400, foreground="blue")
        self.image_file_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Upload button
        upload_btn = ttk.Button(file_frame, text="Datei auswählen", 
                               command=self.select_image_file)
        upload_btn.pack(anchor=tk.W)
        
        # OCR settings section
        ocr_frame = ttk.LabelFrame(image_tab, text="OCR-Einstellungen", padding=10)
        ocr_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Language selection
        ttk.Label(ocr_frame, text="Sprache:").pack(anchor=tk.W)
        self.ocr_language_var = tk.StringVar(value="deu+eng")
        language_combo = ttk.Combobox(ocr_frame, textvariable=self.ocr_language_var,
                                     values=["deu+eng", "deu", "eng", "fra", "spa", "ita"],
                                     state="readonly", width=20)
        language_combo.pack(anchor=tk.W, pady=(0, 5))
        
        # Process button
        process_btn = ttk.Button(ocr_frame, text="Text extrahieren", 
                                command=self.process_image_ocr)
        process_btn.pack(anchor=tk.W)
        
        # Preview section
        preview_frame = ttk.LabelFrame(image_tab, text="Extrahierter Text (Vorschau)", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True)
        
        self.image_preview_text_widget = scrolledtext.ScrolledText(preview_frame, height=10, 
                                                                  wrap=tk.WORD, state=tk.DISABLED)
        self.image_preview_text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Info label
        self.image_info_var = tk.StringVar()
        self.image_info_label = ttk.Label(preview_frame, textvariable=self.image_info_var)
        self.image_info_label.pack(anchor=tk.W, pady=(5, 0))
    
    def setup_csv_tab(self):
        """Setup CSV file upload tab with preview."""
        csv_tab = ttk.Frame(self.parent_notebook, padding=10)
        self.parent_notebook.add(csv_tab, text="CSV/Text")
        
        # File selection section
        file_frame = ttk.LabelFrame(csv_tab, text="CSV/Text-Dateien auswählen", padding=10)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        # File list
        self.csv_files_listbox = tk.Listbox(file_frame, height=4)
        csv_list_scrollbar = ttk.Scrollbar(file_frame, orient=tk.VERTICAL, 
                                          command=self.csv_files_listbox.yview)
        self.csv_files_listbox.configure(yscrollcommand=csv_list_scrollbar.set)
        
        self.csv_files_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        csv_list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        csv_btn_frame = ttk.Frame(file_frame)
        csv_btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        add_csv_btn = ttk.Button(csv_btn_frame, text="Dateien hinzufügen", 
                                command=self.add_csv_files)
        add_csv_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        remove_csv_btn = ttk.Button(csv_btn_frame, text="Entfernen", 
                                   command=self.remove_csv_file)
        remove_csv_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        clear_csv_btn = ttk.Button(csv_btn_frame, text="Alle entfernen", 
                                  command=self.clear_csv_files)
        clear_csv_btn.pack(side=tk.LEFT)
        
        # Processing options
        options_frame = ttk.LabelFrame(csv_tab, text="Verarbeitungsoptionen", padding=10)
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(options_frame, text="Kombinationsmethode:").pack(anchor=tk.W)
        self.csv_combine_var = tk.StringVar(value="concat")
        combine_combo = ttk.Combobox(options_frame, textvariable=self.csv_combine_var,
                                    values=["concat", "merge", "separate"],
                                    state="readonly", width=20)
        combine_combo.pack(anchor=tk.W, pady=(0, 5))
        
        # Preview section
        preview_frame = ttk.LabelFrame(csv_tab, text="Datenvorschau", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True)
        
        self.csv_preview_text = scrolledtext.ScrolledText(preview_frame, height=8, 
                                                         wrap=tk.WORD, state=tk.DISABLED)
        self.csv_preview_text.pack(fill=tk.BOTH, expand=True)
        
        # Info label
        self.csv_info_var = tk.StringVar()
        self.csv_info_label = ttk.Label(preview_frame, textvariable=self.csv_info_var)
        self.csv_info_label.pack(anchor=tk.W, pady=(5, 0))
    
    def setup_multi_file_tab(self):
        """Setup multi-file selection tab with drag-and-drop support."""
        multi_tab = ttk.Frame(self.parent_notebook, padding=10)
        self.parent_notebook.add(multi_tab, text="Multi-Datei")
        
        # Instructions
        instructions = ttk.Label(multi_tab, 
                               text="Wählen Sie mehrere Dateien verschiedener Formate für die kombinierte Analyse aus.",
                               wraplength=400)
        instructions.pack(anchor=tk.W, pady=(0, 10))
        
        # File selection section
        file_frame = ttk.LabelFrame(multi_tab, text="Ausgewählte Dateien", padding=10)
        file_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # File list with details
        columns = ("Datei", "Typ", "Größe", "Status")
        self.multi_files_tree = ttk.Treeview(file_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            self.multi_files_tree.heading(col, text=col)
            self.multi_files_tree.column(col, width=100)
        
        multi_scrollbar = ttk.Scrollbar(file_frame, orient=tk.VERTICAL, 
                                       command=self.multi_files_tree.yview)
        self.multi_files_tree.configure(yscrollcommand=multi_scrollbar.set)
        
        self.multi_files_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        multi_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        multi_btn_frame = ttk.Frame(multi_tab)
        multi_btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        add_multi_btn = ttk.Button(multi_btn_frame, text="Dateien hinzufügen", 
                                  command=self.add_multiple_files)
        add_multi_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        remove_multi_btn = ttk.Button(multi_btn_frame, text="Entfernen", 
                                     command=self.remove_selected_file)
        remove_multi_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        clear_multi_btn = ttk.Button(multi_btn_frame, text="Alle entfernen", 
                                    command=self.clear_all_files)
        clear_multi_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        analyze_btn = ttk.Button(multi_btn_frame, text="Dateien analysieren", 
                                command=self.analyze_selected_files)
        analyze_btn.pack(side=tk.RIGHT)
        
        # Summary section
        summary_frame = ttk.LabelFrame(multi_tab, text="Zusammenfassung", padding=10)
        summary_frame.pack(fill=tk.X)
        
        self.multi_summary_var = tk.StringVar()
        self.multi_summary_label = ttk.Label(summary_frame, textvariable=self.multi_summary_var)
        self.multi_summary_label.pack(anchor=tk.W)
    
    def select_excel_file(self):
        """Handle Excel file selection."""
        file_path = filedialog.askopenfilename(
            title="Excel-Datei auswählen",
            filetypes=[
                ("Excel-Dateien", "*.xlsx *.xls"),
                ("Alle Dateien", "*.*")
            ]
        )
        
        if file_path:
            self.current_excel_file = file_path
            self.excel_file_var.set(f"Datei: {Path(file_path).name}")
            self.status_callback("Excel-Datei wird geladen...")
            
            # Load Excel file info in background
            threading.Thread(target=self.load_excel_info, daemon=True).start()
    
    def load_excel_info(self):
        """Load Excel file information in background thread."""
        if not self.current_excel_file or not self.file_router:
            return
        
        try:
            # Get Excel handler
            excel_handler = self.file_router.handlers.get('excel')
            if not excel_handler:
                raise Exception("Excel-Handler nicht verfügbar")
            
            # Get file info
            file_info = excel_handler.get_file_info(self.current_excel_file)
            
            # Update UI in main thread
            self.parent_notebook.after(0, self.update_excel_ui, file_info)
            
        except Exception as e:
            error_msg = f"Fehler beim Laden der Excel-Datei: {str(e)}"
            self.parent_notebook.after(0, self.show_excel_error, error_msg)
    
    def update_excel_ui(self, file_info):
        """Update Excel UI with file information."""
        # Update sheet selection
        sheet_names = [sheet.name for sheet in file_info.sheets]
        self.excel_sheet_combo['values'] = sheet_names
        
        if sheet_names:
            self.excel_sheet_combo.current(0)
            self.excel_sheet_var.set(sheet_names[0])
            
            # Load preview for first sheet
            self.load_excel_sheet_preview(sheet_names[0], file_info)
        
        self.status_callback("Excel-Datei geladen")
    
    def show_excel_error(self, error_msg):
        """Show Excel loading error."""
        self.excel_info_var.set(error_msg)
        self.status_callback("Fehler beim Laden der Excel-Datei")
        messagebox.showerror("Fehler", error_msg)
    
    def on_excel_sheet_selected(self, event=None):
        """Handle Excel sheet selection."""
        if not self.current_excel_file:
            return
        
        selected_sheet = self.excel_sheet_var.get()
        if selected_sheet:
            self.status_callback("Arbeitsblatt wird geladen...")
            threading.Thread(target=self.load_sheet_preview, args=(selected_sheet,), daemon=True).start()
    
    def load_sheet_preview(self, sheet_name):
        """Load preview for selected Excel sheet."""
        try:
            excel_handler = self.file_router.handlers.get('excel')
            file_info = excel_handler.get_file_info(self.current_excel_file)
            
            # Update UI in main thread
            self.parent_notebook.after(0, self.load_excel_sheet_preview, sheet_name, file_info)
            
        except Exception as e:
            error_msg = f"Fehler beim Laden des Arbeitsblatts: {str(e)}"
            self.parent_notebook.after(0, self.show_excel_error, error_msg)
    
    def load_excel_sheet_preview(self, sheet_name, file_info):
        """Load preview data for Excel sheet."""
        # Find sheet info
        sheet_info = None
        for sheet in file_info.sheets:
            if sheet.name == sheet_name:
                sheet_info = sheet
                break
        
        if not sheet_info:
            return
        
        # Clear existing tree
        for item in self.excel_tree.get_children():
            self.excel_tree.delete(item)
        
        # Setup columns
        if sheet_info.column_names:
            self.excel_tree['columns'] = sheet_info.column_names
            self.excel_tree['show'] = 'headings'
            
            for col in sheet_info.column_names:
                self.excel_tree.heading(col, text=col)
                self.excel_tree.column(col, width=100)
        
        # Add preview data
        for row_data in sheet_info.preview_data:
            values = [str(row_data.get(col, "")) for col in sheet_info.column_names]
            self.excel_tree.insert("", tk.END, values=values)
        
        # Update info
        info_text = f"Zeilen: {sheet_info.rows}, Spalten: {sheet_info.columns}"
        if len(sheet_info.preview_data) < sheet_info.rows:
            info_text += f" (Vorschau: erste {len(sheet_info.preview_data)} Zeilen)"
        
        self.excel_info_var.set(info_text)
        self.status_callback("Arbeitsblatt-Vorschau geladen")
    
    def select_image_file(self):
        """Handle image file selection."""
        file_path = filedialog.askopenfilename(
            title="Bild- oder PDF-Datei auswählen",
            filetypes=[
                ("Bilddateien", "*.png *.jpg *.jpeg *.bmp *.tiff *.tif"),
                ("PDF-Dateien", "*.pdf"),
                ("Alle Dateien", "*.*")
            ]
        )
        
        if file_path:
            self.current_image_file = file_path
            self.image_file_var.set(f"Datei: {Path(file_path).name}")
            
            # Auto-process OCR for quick preview
            self.process_image_ocr(preview_only=True)
    
    def process_image_ocr(self, preview_only=False):
        """Process image OCR."""
        if not self.current_image_file or not self.file_router:
            return
        
        self.status_callback("OCR wird verarbeitet...")
        
        # Process in background
        threading.Thread(target=self.run_ocr, args=(preview_only,), daemon=True).start()
    
    def run_ocr(self, preview_only=False):
        """Run OCR processing in background thread."""
        try:
            image_handler = self.file_router.handlers.get('image')
            if not image_handler:
                raise Exception("Bild-Handler nicht verfügbar")
            
            # Get file info first
            file_info = image_handler.get_file_info(self.current_image_file)
            
            if preview_only and file_info.preview_text:
                # Use cached preview
                preview_text = file_info.preview_text
                info_text = f"Format: {file_info.format}, Größe: {file_info.dimensions[0]}x{file_info.dimensions[1]}"
            else:
                # Full OCR processing
                language = self.ocr_language_var.get()
                ocr_result = image_handler.extract_text(self.current_image_file, language)
                
                preview_text = ocr_result.text[:1000]  # Limit preview
                if len(ocr_result.text) > 1000:
                    preview_text += "\n\n... (Text gekürzt für Vorschau)"
                
                info_text = (f"Format: {file_info.format}, Größe: {file_info.dimensions[0]}x{file_info.dimensions[1]}, "
                           f"Vertrauen: {ocr_result.confidence:.1f}%, Zeichen: {len(ocr_result.text)}")
            
            # Update UI in main thread
            self.parent_notebook.after(0, self.update_image_preview, preview_text, info_text)
            
        except Exception as e:
            error_msg = f"OCR-Fehler: {str(e)}"
            self.parent_notebook.after(0, self.show_image_error, error_msg)
    
    def update_image_preview(self, preview_text, info_text):
        """Update image preview UI."""
        self.image_preview_text_widget.config(state=tk.NORMAL)
        self.image_preview_text_widget.delete(1.0, tk.END)
        self.image_preview_text_widget.insert(1.0, preview_text)
        self.image_preview_text_widget.config(state=tk.DISABLED)
        
        self.image_info_var.set(info_text)
        self.status_callback("OCR-Verarbeitung abgeschlossen")
    
    def show_image_error(self, error_msg):
        """Show image processing error."""
        self.image_info_var.set(error_msg)
        self.status_callback("OCR-Fehler")
        messagebox.showerror("OCR-Fehler", error_msg)
    
    def add_csv_files(self):
        """Add CSV files to the list."""
        file_paths = filedialog.askopenfilenames(
            title="CSV/Text-Dateien auswählen",
            filetypes=[
                ("CSV-Dateien", "*.csv"),
                ("TSV-Dateien", "*.tsv"),
                ("Text-Dateien", "*.txt"),
                ("Alle Dateien", "*.*")
            ]
        )
        
        for file_path in file_paths:
            if file_path not in self.current_csv_files:
                self.current_csv_files.append(file_path)
                self.csv_files_listbox.insert(tk.END, Path(file_path).name)
        
        self.update_csv_preview()
    
    def remove_csv_file(self):
        """Remove selected CSV file."""
        selection = self.csv_files_listbox.curselection()
        if selection:
            index = selection[0]
            self.csv_files_listbox.delete(index)
            del self.current_csv_files[index]
            self.update_csv_preview()
    
    def clear_csv_files(self):
        """Clear all CSV files."""
        self.csv_files_listbox.delete(0, tk.END)
        self.current_csv_files.clear()
        self.update_csv_preview()
    
    def update_csv_preview(self):
        """Update CSV preview."""
        if not self.current_csv_files or not self.file_router:
            self.csv_preview_text.config(state=tk.NORMAL)
            self.csv_preview_text.delete(1.0, tk.END)
            self.csv_preview_text.config(state=tk.DISABLED)
            self.csv_info_var.set("")
            return
        
        self.status_callback("CSV-Vorschau wird geladen...")
        threading.Thread(target=self.load_csv_preview, daemon=True).start()
    
    def load_csv_preview(self):
        """Load CSV preview in background."""
        try:
            csv_handler = self.file_router.handlers.get('csv')
            if not csv_handler:
                raise Exception("CSV-Handler nicht verfügbar")
            
            # Get preview content
            combine_method = self.csv_combine_var.get()
            preview_content = csv_handler.extract_combined_content_for_analysis(
                self.current_csv_files, combine_method
            )
            
            # Limit preview length
            if len(preview_content) > 2000:
                preview_content = preview_content[:2000] + "\n\n... (Vorschau gekürzt)"
            
            info_text = f"Dateien: {len(self.current_csv_files)}, Methode: {combine_method}"
            
            # Update UI
            self.parent_notebook.after(0, self.update_csv_preview_ui, preview_content, info_text)
            
        except Exception as e:
            error_msg = f"CSV-Fehler: {str(e)}"
            self.parent_notebook.after(0, self.show_csv_error, error_msg)
    
    def update_csv_preview_ui(self, preview_content, info_text):
        """Update CSV preview UI."""
        self.csv_preview_text.config(state=tk.NORMAL)
        self.csv_preview_text.delete(1.0, tk.END)
        self.csv_preview_text.insert(1.0, preview_content)
        self.csv_preview_text.config(state=tk.DISABLED)
        
        self.csv_info_var.set(info_text)
        self.status_callback("CSV-Vorschau geladen")
    
    def show_csv_error(self, error_msg):
        """Show CSV error."""
        self.csv_info_var.set(error_msg)
        self.status_callback("CSV-Fehler")
        messagebox.showerror("CSV-Fehler", error_msg)
    
    def add_multiple_files(self):
        """Add multiple files of various types."""
        file_paths = filedialog.askopenfilenames(
            title="Dateien für Multi-Analyse auswählen",
            filetypes=[
                ("Alle unterstützten", "*.xlsx *.xls *.csv *.tsv *.txt *.png *.jpg *.jpeg *.pdf *.bmp *.tiff *.tif"),
                ("Excel-Dateien", "*.xlsx *.xls"),
                ("CSV-Dateien", "*.csv *.tsv *.txt"),
                ("Bilddateien", "*.png *.jpg *.jpeg *.bmp *.tiff *.tif"),
                ("PDF-Dateien", "*.pdf"),
                ("Alle Dateien", "*.*")
            ]
        )
        
        for file_path in file_paths:
            if file_path not in self.selected_files:
                self.selected_files.append(file_path)
                self.add_file_to_tree(file_path)
        
        self.update_multi_summary()
    
    def add_file_to_tree(self, file_path):
        """Add file to multi-file tree."""
        if not self.file_router:
            return
        
        try:
            # Detect file type
            file_info = self.file_router.detect_file_type(file_path)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            size_str = self.format_file_size(file_size)
            
            # Determine status
            status = "Unterstützt" if file_info.supported else "Nicht unterstützt"
            
            # Add to tree
            self.multi_files_tree.insert("", tk.END, values=(
                Path(file_path).name,
                file_info.file_type,
                size_str,
                status
            ))
            
        except Exception as e:
            # Add with error status
            self.multi_files_tree.insert("", tk.END, values=(
                Path(file_path).name,
                "Unbekannt",
                "?",
                f"Fehler: {str(e)}"
            ))
    
    def format_file_size(self, size_bytes):
        """Format file size in human readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    def remove_selected_file(self):
        """Remove selected file from multi-file list."""
        selection = self.multi_files_tree.selection()
        if selection:
            item = selection[0]
            index = self.multi_files_tree.index(item)
            
            self.multi_files_tree.delete(item)
            if 0 <= index < len(self.selected_files):
                del self.selected_files[index]
            
            self.update_multi_summary()
    
    def clear_all_files(self):
        """Clear all files from multi-file list."""
        for item in self.multi_files_tree.get_children():
            self.multi_files_tree.delete(item)
        
        self.selected_files.clear()
        self.update_multi_summary()
    
    def update_multi_summary(self):
        """Update multi-file summary."""
        if not self.selected_files:
            self.multi_summary_var.set("Keine Dateien ausgewählt")
            return
        
        if not self.file_router:
            self.multi_summary_var.set(f"{len(self.selected_files)} Dateien ausgewählt (Handler nicht verfügbar)")
            return
        
        # Count by type
        type_counts = {}
        supported_count = 0
        
        for file_path in self.selected_files:
            try:
                file_info = self.file_router.detect_file_type(file_path)
                file_type = file_info.file_type
                
                if file_type not in type_counts:
                    type_counts[file_type] = 0
                type_counts[file_type] += 1
                
                if file_info.supported:
                    supported_count += 1
                    
            except Exception:
                if 'error' not in type_counts:
                    type_counts['error'] = 0
                type_counts['error'] += 1
        
        # Format summary
        type_summary = ", ".join([f"{count} {type_name}" for type_name, count in type_counts.items()])
        summary_text = f"{len(self.selected_files)} Dateien ({supported_count} unterstützt): {type_summary}"
        
        self.multi_summary_var.set(summary_text)
    
    def analyze_selected_files(self):
        """Analyze all selected files."""
        if not self.selected_files:
            messagebox.showwarning("Keine Dateien", "Bitte wählen Sie Dateien für die Analyse aus.")
            return
        
        if not self.file_router:
            messagebox.showerror("Fehler", "Datei-Handler nicht verfügbar.")
            return
        
        self.status_callback("Multi-Datei-Analyse wird gestartet...")
        
        # This would typically trigger the main analysis workflow
        # For now, we'll show a preview of what would be analyzed
        try:
            content = self.file_router.get_analysis_content(self.selected_files)
            
            # Show preview dialog
            self.show_analysis_preview(content)
            
        except Exception as e:
            messagebox.showerror("Analyse-Fehler", f"Fehler bei der Datei-Analyse: {str(e)}")
    
    def show_analysis_preview(self, content):
        """Show analysis content preview."""
        preview_window = tk.Toplevel(self.parent_notebook)
        preview_window.title("Analyse-Vorschau")
        preview_window.geometry("600x400")
        
        # Content preview
        preview_text = scrolledtext.ScrolledText(preview_window, wrap=tk.WORD)
        preview_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Limit content for preview
        preview_content = content[:5000]
        if len(content) > 5000:
            preview_content += "\n\n... (Inhalt für Vorschau gekürzt)"
        
        preview_text.insert(1.0, preview_content)
        preview_text.config(state=tk.DISABLED)
        
        # Buttons
        btn_frame = ttk.Frame(preview_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(btn_frame, text="Schließen", 
                  command=preview_window.destroy).pack(side=tk.RIGHT)
    
    def get_current_content(self) -> Optional[str]:
        """
        Get content from currently selected tab for analysis.
        
        Returns:
            Content string ready for analysis, or None if no content available
        """
        if not self.file_router:
            return None
        
        # Get currently selected tab
        current_tab = self.parent_notebook.select()
        tab_index = self.parent_notebook.index(current_tab)
        
        # Map tab indices to our extended tabs (assuming they're added after existing tabs)
        # This would need to be adjusted based on the actual tab order in the main GUI
        extended_tab_offset = 3  # Assuming 3 existing tabs (Website, YouTube, PDF)
        
        try:
            if tab_index == extended_tab_offset:  # Excel tab
                if self.current_excel_file:
                    sheet_name = self.excel_sheet_var.get() or None
                    excel_handler = self.file_router.handlers.get('excel')
                    return excel_handler.extract_content_for_analysis(self.current_excel_file, sheet_name)
            
            elif tab_index == extended_tab_offset + 1:  # Image tab
                if self.current_image_file:
                    language = self.ocr_language_var.get()
                    image_handler = self.file_router.handlers.get('image')
                    return image_handler.extract_content_for_analysis(self.current_image_file, language)
            
            elif tab_index == extended_tab_offset + 2:  # CSV tab
                if self.current_csv_files:
                    combine_method = self.csv_combine_var.get()
                    csv_handler = self.file_router.handlers.get('csv')
                    return csv_handler.extract_combined_content_for_analysis(self.current_csv_files, combine_method)
            
            elif tab_index == extended_tab_offset + 3:  # Multi-file tab
                if self.selected_files:
                    return self.file_router.get_analysis_content(self.selected_files)
        
        except Exception as e:
            logging.error(f"Error getting content from extended tabs: {e}")
            return f"Fehler beim Extrahieren des Inhalts: {str(e)}"
        
        return None
    
    def trigger_analysis(self):
        """Trigger analysis for the currently selected extended tab."""
        if not self.analysis_callback:
            return
        
        current_tab = self.parent_notebook.select()
        tab_index = self.parent_notebook.index(current_tab)
        extended_tab_offset = 3
        
        if tab_index >= extended_tab_offset:
            content = self.get_current_content()
            if content:
                source_path = "extended_input"
                if tab_index == extended_tab_offset and self.current_excel_file:
                    source_path = self.current_excel_file
                elif tab_index == extended_tab_offset + 1 and self.current_image_file:
                    source_path = self.current_image_file
                elif tab_index == extended_tab_offset + 2 and self.current_csv_files:
                    source_path = ", ".join(self.current_csv_files)
                elif tab_index == extended_tab_offset + 3 and self.selected_files:
                    source_path = ", ".join(self.selected_files)
                
                self.analysis_callback(content, source_path, "enhanced_analysis")
    
    def get_handler_info(self) -> Dict[str, Any]:
        """Get information about available file handlers."""
        if self.file_router:
            return self.file_router.get_handler_info()
        else:
            return {"error": "File router not available"}