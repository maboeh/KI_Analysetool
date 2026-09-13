"""
CSV file handler for processing CSV files with automatic delimiter detection.
Includes multi-file processing capabilities.
"""

import pandas as pd
import csv
import os
import chardet
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from pathlib import Path
import logging

from error_handler import ErrorHandler, ErrorResult, handle_errors


@dataclass
class CSVInfo:
    """Information about a CSV file."""
    file_path: str
    file_size: int
    encoding: str
    delimiter: str
    rows: int
    columns: int
    column_names: List[str]
    preview_data: List[Dict[str, Any]]
    has_header: bool


@dataclass
class MultiFileResult:
    """Result of multi-file processing."""
    files_processed: List[str]
    combined_data: pd.DataFrame
    individual_results: Dict[str, Any]
    processing_summary: Dict[str, Any]


class CSVHandler:
    """Handler for CSV file processing with automatic delimiter detection."""
    
    SUPPORTED_EXTENSIONS = ['.csv', '.tsv', '.txt']
    MAX_FILE_SIZE_MB = 100
    MAX_PREVIEW_ROWS = 10
    COMMON_DELIMITERS = [',', ';', '\t', '|', ' ']
    COMMON_ENCODINGS = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    def __init__(self):
        self.current_files: List[str] = []
        self.current_results: Dict[str, CSVInfo] = {}
        self.error_handler = ErrorHandler()
        self.logger = logging.getLogger(__name__)
    
    def can_handle(self, file_path: str) -> bool:
        """Check if the file can be handled by this handler."""
        if not os.path.exists(file_path):
            return False
        
        file_extension = Path(file_path).suffix.lower()
        return file_extension in self.SUPPORTED_EXTENSIONS
    
    def detect_encoding(self, file_path: str) -> str:
        """Detect the encoding of a CSV file."""
        try:
            with open(file_path, 'rb') as f:
                # Read first 10KB for encoding detection
                raw_data = f.read(10240)
                result = chardet.detect(raw_data)
                encoding = result.get('encoding', 'utf-8')
                
                # Validate encoding by trying to read a few lines
                try:
                    with open(file_path, 'r', encoding=encoding) as test_file:
                        test_file.readline()
                    return encoding
                except UnicodeDecodeError:
                    # Fall back to common encodings
                    for enc in self.COMMON_ENCODINGS:
                        try:
                            with open(file_path, 'r', encoding=enc) as test_file:
                                test_file.readline()
                            return enc
                        except UnicodeDecodeError:
                            continue
                    
                    # Last resort
                    return 'utf-8'
                    
        except Exception as e:
            logging.warning(f"Encoding detection failed for {file_path}: {e}")
            return 'utf-8'
    
    def detect_delimiter(self, file_path: str, encoding: str) -> Tuple[str, bool]:
        """Detect the delimiter and whether the file has a header."""
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                # Read first few lines for analysis
                sample_lines = []
                for i, line in enumerate(f):
                    if i >= 5:  # Analyze first 5 lines
                        break
                    sample_lines.append(line.strip())
                
                if not sample_lines:
                    return ',', False
                
                # Use csv.Sniffer to detect delimiter
                sample_text = '\n'.join(sample_lines)
                sniffer = csv.Sniffer()
                
                try:
                    dialect = sniffer.sniff(sample_text, delimiters=''.join(self.COMMON_DELIMITERS))
                    delimiter = dialect.delimiter
                    
                    # Check if first line looks like a header
                    has_header = sniffer.has_header(sample_text)
                    
                    return delimiter, has_header
                    
                except csv.Error:
                    # Fallback: count occurrences of common delimiters
                    delimiter_counts = {}
                    for delimiter in self.COMMON_DELIMITERS:
                        count = sum(line.count(delimiter) for line in sample_lines)
                        if count > 0:
                            delimiter_counts[delimiter] = count
                    
                    if delimiter_counts:
                        # Choose delimiter with most consistent count across lines
                        best_delimiter = max(delimiter_counts.keys(), 
                                           key=lambda d: min(line.count(d) for line in sample_lines))
                        
                        # Simple header detection: check if first line has different pattern
                        first_line_count = sample_lines[0].count(best_delimiter)
                        other_lines_count = [line.count(best_delimiter) for line in sample_lines[1:]]
                        has_header = len(set(other_lines_count)) == 1 and first_line_count == other_lines_count[0]
                        
                        return best_delimiter, has_header
                    else:
                        return ',', False
                        
        except Exception as e:
            logging.warning(f"Delimiter detection failed for {file_path}: {e}")
            return ',', False
    
    def get_file_info(self, file_path: str) -> CSVInfo:
        """Get comprehensive information about the CSV file."""
        if not self.can_handle(file_path):
            raise ValueError(f"Unsupported file format. Supported formats: {self.SUPPORTED_EXTENSIONS}")
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > self.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise ValueError(f"File too large. Maximum size: {self.MAX_FILE_SIZE_MB}MB")
        
        try:
            # Detect encoding and delimiter
            encoding = self.detect_encoding(file_path)
            delimiter, has_header = self.detect_delimiter(file_path, encoding)
            
            # Read file with detected parameters
            df = pd.read_csv(
                file_path,
                encoding=encoding,
                delimiter=delimiter,
                header=0 if has_header else None,
                nrows=self.MAX_PREVIEW_ROWS
            )
            
            # Get column names
            if has_header:
                column_names = list(df.columns)
            else:
                column_names = [f"Column_{i+1}" for i in range(len(df.columns))]
                df.columns = column_names
            
            # Create preview data
            preview_data = []
            for _, row in df.iterrows():
                row_dict = {}
                for col_name, value in zip(column_names, row.values):
                    if pd.isna(value):
                        row_dict[col_name] = None
                    else:
                        row_dict[col_name] = str(value) if not isinstance(value, (int, float, bool)) else value
                preview_data.append(row_dict)
            
            # Get total row count
            with open(file_path, 'r', encoding=encoding) as row_file:
                total_rows = sum(1 for _ in row_file)
            if has_header:
                total_rows -= 1  # Subtract header row
            
            csv_info = CSVInfo(
                file_path=file_path,
                file_size=file_size,
                encoding=encoding,
                delimiter=delimiter,
                rows=total_rows,
                columns=len(column_names),
                column_names=column_names,
                preview_data=preview_data,
                has_header=has_header
            )
            
            return csv_info
            
        except Exception as e:
            raise ValueError(f"Error reading CSV file: {str(e)}")
    
    def read_csv(self, file_path: str, max_rows: Optional[int] = None) -> pd.DataFrame:
        """Read CSV file with automatic parameter detection."""
        if not self.can_handle(file_path):
            raise ValueError(f"Unsupported file format. Supported formats: {self.SUPPORTED_EXTENSIONS}")
        
        try:
            # Get file info for parameters
            csv_info = self.get_file_info(file_path)
            
            # Read the full file (or limited rows)
            kwargs = {
                'encoding': csv_info.encoding,
                'delimiter': csv_info.delimiter,
                'header': 0 if csv_info.has_header else None
            }
            
            if max_rows is not None:
                kwargs['nrows'] = max_rows
            
            df = pd.read_csv(file_path, **kwargs)
            
            # Set column names if no header
            if not csv_info.has_header:
                df.columns = csv_info.column_names
            
            return df
            
        except Exception as e:
            raise ValueError(f"Error reading CSV file: {str(e)}")
    
    def extract_content_for_analysis(self, file_path: str, include_headers: bool = True,
                                   max_rows_for_analysis: int = 100) -> str:
        """Extract content from CSV file in a format suitable for AI analysis."""
        df = self.read_csv(file_path, max_rows=max_rows_for_analysis)
        csv_info = self.get_file_info(file_path)
        
        content_parts = []
        
        if include_headers:
            content_parts.append("CSV-Daten:")
            content_parts.append(f"Datei: {Path(file_path).name}")
            content_parts.append(f"Zeilen: {csv_info.rows}, Spalten: {csv_info.columns}")
            content_parts.append(f"Trennzeichen: '{csv_info.delimiter}'")
            content_parts.append(f"Kodierung: {csv_info.encoding}")
            content_parts.append("")
        
        # Add column headers
        content_parts.append("Spalten: " + " | ".join(df.columns))
        content_parts.append("-" * 50)
        
        # Add data rows
        for i in range(len(df)):
            row_values = []
            for col in df.columns:
                value = df.iloc[i][col]
                if pd.isna(value):
                    row_values.append("(leer)")
                else:
                    row_values.append(str(value))
            content_parts.append(" | ".join(row_values))
        
        if csv_info.rows > max_rows_for_analysis:
            content_parts.append(f"... ({csv_info.rows - max_rows_for_analysis} weitere Zeilen)")
        
        return "\n".join(content_parts)
    
    def convert_to_structured_data(self, file_path: str) -> Dict[str, Any]:
        """Convert CSV data to structured format for further processing."""
        df = self.read_csv(file_path)
        csv_info = self.get_file_info(file_path)
        
        structured_data = {
            'source_type': 'csv',
            'source_file': file_path,
            'file_info': {
                'encoding': csv_info.encoding,
                'delimiter': csv_info.delimiter,
                'has_header': csv_info.has_header,
                'file_size': csv_info.file_size
            },
            'dimensions': {
                'rows': len(df),
                'columns': len(df.columns)
            },
            'columns': list(df.columns),
            'data_types': {col: str(df[col].dtype) for col in df.columns},
            'data': df.to_dict('records'),
            'summary': {
                'numeric_columns': list(df.select_dtypes(include=['number']).columns),
                'text_columns': list(df.select_dtypes(include=['object']).columns),
                'date_columns': list(df.select_dtypes(include=['datetime']).columns),
                'null_counts': df.isnull().sum().to_dict(),
                'unique_counts': {col: df[col].nunique() for col in df.columns}
            }
        }
        
        return structured_data
    
    def process_multiple_files(self, file_paths: List[str], 
                             combine_method: str = 'concat') -> MultiFileResult:
        """
        Process multiple CSV files and optionally combine them.
        
        Args:
            file_paths: List of file paths to process
            combine_method: 'concat' (stack vertically), 'merge' (join on common columns), 'separate'
        """
        if not file_paths:
            raise ValueError("No file paths provided")
        
        # Validate all files
        valid_files = []
        for file_path in file_paths:
            if self.can_handle(file_path):
                valid_files.append(file_path)
            else:
                logging.warning(f"Skipping unsupported file: {file_path}")
        
        if not valid_files:
            raise ValueError("No valid CSV files found")
        
        # Process each file individually
        individual_results = {}
        dataframes = []
        
        for file_path in valid_files:
            try:
                # Get file info
                csv_info = self.get_file_info(file_path)
                individual_results[file_path] = {
                    'info': csv_info,
                    'structured_data': self.convert_to_structured_data(file_path)
                }
                
                # Read data
                df = self.read_csv(file_path)
                df['_source_file'] = Path(file_path).name  # Add source tracking
                dataframes.append(df)
                
            except Exception as e:
                logging.error(f"Error processing file {file_path}: {e}")
                individual_results[file_path] = {'error': str(e)}
        
        # Combine data based on method
        combined_data = None
        processing_summary = {
            'files_processed': len(dataframes),
            'total_files': len(file_paths),
            'combine_method': combine_method,
            'errors': [path for path, result in individual_results.items() if 'error' in result]
        }
        
        if dataframes:
            try:
                if combine_method == 'concat':
                    # Stack all dataframes vertically
                    combined_data = pd.concat(dataframes, ignore_index=True, sort=False)
                    processing_summary['combined_rows'] = len(combined_data)
                    processing_summary['combined_columns'] = len(combined_data.columns)
                    
                elif combine_method == 'merge':
                    # Find common columns and merge
                    if len(dataframes) >= 2:
                        combined_data = dataframes[0]
                        for df in dataframes[1:]:
                            # Find common columns
                            common_cols = list(set(combined_data.columns) & set(df.columns))
                            if common_cols:
                                # Remove source file column for merging
                                merge_cols = [col for col in common_cols if col != '_source_file']
                                if merge_cols:
                                    combined_data = pd.merge(combined_data, df, on=merge_cols, how='outer')
                                else:
                                    # No common columns except source, concat instead
                                    combined_data = pd.concat([combined_data, df], ignore_index=True, sort=False)
                            else:
                                # No common columns, concat instead
                                combined_data = pd.concat([combined_data, df], ignore_index=True, sort=False)
                    else:
                        combined_data = dataframes[0]
                    
                    processing_summary['combined_rows'] = len(combined_data)
                    processing_summary['combined_columns'] = len(combined_data.columns)
                    
                elif combine_method == 'separate':
                    # Keep files separate, just return summary
                    processing_summary['note'] = 'Files processed separately, no combination performed'
                    
            except Exception as e:
                logging.error(f"Error combining data: {e}")
                processing_summary['combination_error'] = str(e)
                # Fallback to simple concat
                combined_data = pd.concat(dataframes, ignore_index=True, sort=False)
        
        return MultiFileResult(
            files_processed=[path for path in valid_files if path not in processing_summary.get('errors', [])],
            combined_data=combined_data,
            individual_results=individual_results,
            processing_summary=processing_summary
        )
    
    def extract_combined_content_for_analysis(self, file_paths: List[str],
                                            combine_method: str = 'concat') -> str:
        """Extract content from multiple CSV files for AI analysis."""
        result = self.process_multiple_files(file_paths, combine_method)
        
        content_parts = []
        content_parts.append("Multi-CSV-Datenanalyse:")
        content_parts.append(f"Verarbeitete Dateien: {result.processing_summary['files_processed']}")
        content_parts.append(f"Kombinationsmethode: {combine_method}")
        content_parts.append("")
        
        # Add individual file summaries
        for file_path in result.files_processed:
            if file_path in result.individual_results and 'info' in result.individual_results[file_path]:
                info = result.individual_results[file_path]['info']
                content_parts.append(f"Datei: {Path(file_path).name}")
                content_parts.append(f"  Zeilen: {info.rows}, Spalten: {info.columns}")
                content_parts.append(f"  Trennzeichen: '{info.delimiter}', Kodierung: {info.encoding}")
        
        content_parts.append("")
        
        # Add combined data preview
        if result.combined_data is not None and not result.combined_data.empty:
            content_parts.append("Kombinierte Daten (Vorschau):")
            content_parts.append(f"Gesamt: {len(result.combined_data)} Zeilen, {len(result.combined_data.columns)} Spalten")
            content_parts.append("")
            
            # Show column headers
            content_parts.append("Spalten: " + " | ".join(result.combined_data.columns))
            content_parts.append("-" * 50)
            
            # Show first few rows
            preview_rows = min(20, len(result.combined_data))
            for i in range(preview_rows):
                row_values = []
                for col in result.combined_data.columns:
                    value = result.combined_data.iloc[i][col]
                    if pd.isna(value):
                        row_values.append("(leer)")
                    else:
                        row_values.append(str(value)[:50])  # Limit cell content length
                content_parts.append(" | ".join(row_values))
            
            if len(result.combined_data) > preview_rows:
                content_parts.append(f"... ({len(result.combined_data) - preview_rows} weitere Zeilen)")
        
        # Add any errors
        if result.processing_summary.get('errors'):
            content_parts.append("")
            content_parts.append("Fehler bei folgenden Dateien:")
            for error_file in result.processing_summary['errors']:
                error_msg = result.individual_results[error_file].get('error', 'Unbekannter Fehler')
                content_parts.append(f"  {Path(error_file).name}: {error_msg}")
        
        return "\n".join(content_parts)
    
    def extract_content(self, file_path: str) -> str:
        """Extract content from CSV file - alias for extract_content_for_analysis"""
        return self.extract_content_for_analysis(file_path)