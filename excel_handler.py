"""
Excel file handler for processing Excel files (.xlsx, .xls) with sheet selection and data preview.
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import os
from pathlib import Path
import logging

from error_handler import ErrorHandler, ErrorResult, handle_errors


@dataclass
class ExcelSheetInfo:
    """Information about an Excel sheet."""
    name: str
    rows: int
    columns: int
    column_names: List[str]
    preview_data: List[Dict[str, Any]]


@dataclass
class ExcelFileInfo:
    """Information about an Excel file."""
    file_path: str
    file_size: int
    sheets: List[ExcelSheetInfo]
    total_sheets: int


class ExcelHandler:
    """Handler for Excel file processing with sheet selection and data preview."""
    
    SUPPORTED_EXTENSIONS = ['.xlsx', '.xls']
    MAX_PREVIEW_ROWS = 10
    MAX_FILE_SIZE_MB = 100
    
    def __init__(self):
        self.current_file_path: Optional[str] = None
        self.current_file_info: Optional[ExcelFileInfo] = None
        self.error_handler = ErrorHandler()
        self.logger = logging.getLogger(__name__)
    
    def can_handle(self, file_path: str) -> bool:
        """Check if the file can be handled by this handler."""
        if not os.path.exists(file_path):
            return False
        
        file_extension = Path(file_path).suffix.lower()
        return file_extension in self.SUPPORTED_EXTENSIONS
    
    def get_file_info(self, file_path: str) -> ExcelFileInfo:
        """Get comprehensive information about the Excel file."""
        context = {"operation": "file_processing", "file_path": file_path, "file_type": "excel"}
        
        if not self.can_handle(file_path):
            error_result = self.error_handler.handle_error(
                ValueError("Unsupported file format"), 
                context=context
            )
            raise ValueError(self.error_handler.create_user_friendly_message(error_result))
        
        # Check file size
        try:
            file_size = os.path.getsize(file_path)
            if file_size > self.MAX_FILE_SIZE_MB * 1024 * 1024:
                context["file_size"] = file_size
                error_result = self.error_handler.handle_error(
                    ValueError("File too large"), 
                    context=context
                )
                raise ValueError(self.error_handler.create_user_friendly_message(error_result))
        except FileNotFoundError as e:
            error_result = self.error_handler.handle_error(e, context=context)
            raise FileNotFoundError(self.error_handler.create_user_friendly_message(error_result))
        
        try:
            # Read Excel file to get sheet names
            excel_file = pd.ExcelFile(file_path)
            sheets_info = []
            
            for sheet_name in excel_file.sheet_names:
                try:
                    sheet_info = self._get_sheet_info(excel_file, sheet_name)
                    sheets_info.append(sheet_info)
                except Exception as sheet_error:
                    self.logger.warning(f"Error processing sheet '{sheet_name}': {sheet_error}")
                    # Continue with other sheets instead of failing completely
                    continue
            
            if not sheets_info:
                context["error_details"] = "No readable sheets found"
                error_result = self.error_handler.handle_error(
                    ValueError("No readable sheets in Excel file"), 
                    context=context
                )
                raise ValueError(self.error_handler.create_user_friendly_message(error_result))
            
            file_info = ExcelFileInfo(
                file_path=file_path,
                file_size=file_size,
                sheets=sheets_info,
                total_sheets=len(sheets_info)
            )
            
            self.current_file_path = file_path
            self.current_file_info = file_info
            
            return file_info
            
        except Exception as e:
            context["error_details"] = str(e)
            error_result = self.error_handler.handle_error(e, context=context)
            raise type(e)(self.error_handler.create_user_friendly_message(error_result))
    
    def _get_sheet_info(self, excel_file: pd.ExcelFile, sheet_name: str) -> ExcelSheetInfo:
        """Get information about a specific sheet."""
        try:
            # Read only the first few rows for preview
            df = pd.read_excel(excel_file, sheet_name=sheet_name, nrows=self.MAX_PREVIEW_ROWS)
            
            # Get column names, handling unnamed columns
            column_names = []
            for col in df.columns:
                if str(col).startswith('Unnamed:'):
                    column_names.append(f"Column_{len(column_names) + 1}")
                else:
                    column_names.append(str(col))
            
            # Create preview data
            preview_data = []
            for _, row in df.iterrows():
                row_dict = {}
                for i, (col_name, value) in enumerate(zip(column_names, row.values)):
                    # Convert pandas types to Python types for JSON serialization
                    if pd.isna(value):
                        row_dict[col_name] = None
                    elif isinstance(value, (pd.Timestamp, pd.DatetimeIndex)):
                        row_dict[col_name] = str(value)
                    else:
                        row_dict[col_name] = str(value) if not isinstance(value, (int, float, bool)) else value
                preview_data.append(row_dict)
            
            # Get total row count (read without nrows limit just for counting)
            full_df = pd.read_excel(excel_file, sheet_name=sheet_name)
            total_rows = len(full_df)
            
            return ExcelSheetInfo(
                name=sheet_name,
                rows=total_rows,
                columns=len(column_names),
                column_names=column_names,
                preview_data=preview_data
            )
            
        except Exception as e:
            raise ValueError(f"Error reading sheet '{sheet_name}': {str(e)}")
    
    def read_sheet(self, file_path: str, sheet_name: Optional[str] = None, 
                   max_rows: Optional[int] = None) -> pd.DataFrame:
        """Read a specific sheet from the Excel file."""
        if not self.can_handle(file_path):
            raise ValueError(f"Unsupported file format. Supported formats: {self.SUPPORTED_EXTENSIONS}")
        
        try:
            # If no sheet specified, use the first sheet
            if sheet_name is None:
                excel_file = pd.ExcelFile(file_path)
                sheet_name = excel_file.sheet_names[0]
            
            # Read the sheet
            kwargs = {'sheet_name': sheet_name}
            if max_rows is not None:
                kwargs['nrows'] = max_rows
            
            df = pd.read_excel(file_path, **kwargs)
            
            # Clean column names
            df.columns = [
                f"Column_{i+1}" if str(col).startswith('Unnamed:') else str(col)
                for i, col in enumerate(df.columns)
            ]
            
            return df
            
        except Exception as e:
            raise ValueError(f"Error reading Excel sheet: {str(e)}")
    
    def extract_content_for_analysis(self, file_path: str, sheet_name: Optional[str] = None,
                                   include_headers: bool = True) -> str:
        """Extract content from Excel file in a format suitable for AI analysis."""
        df = self.read_sheet(file_path, sheet_name)
        
        # Convert DataFrame to text format
        content_parts = []
        
        if include_headers:
            content_parts.append("Excel-Daten:")
            content_parts.append(f"Tabelle: {sheet_name or 'Standard-Arbeitsblatt'}")
            content_parts.append(f"Zeilen: {len(df)}, Spalten: {len(df.columns)}")
            content_parts.append("")
        
        # Add column headers
        content_parts.append("Spalten: " + " | ".join(df.columns))
        content_parts.append("-" * 50)
        
        # Add data rows (limit to reasonable number for analysis)
        max_rows_for_analysis = 100
        rows_to_process = min(len(df), max_rows_for_analysis)
        
        for i in range(rows_to_process):
            row_values = []
            for col in df.columns:
                value = df.iloc[i][col]
                if pd.isna(value):
                    row_values.append("(leer)")
                else:
                    row_values.append(str(value))
            content_parts.append(" | ".join(row_values))
        
        if len(df) > max_rows_for_analysis:
            content_parts.append(f"... ({len(df) - max_rows_for_analysis} weitere Zeilen)")
        
        return "\n".join(content_parts)
    
    def get_sheet_names(self, file_path: str) -> List[str]:
        """Get list of sheet names in the Excel file."""
        if not self.can_handle(file_path):
            raise ValueError(f"Unsupported file format. Supported formats: {self.SUPPORTED_EXTENSIONS}")
        
        try:
            excel_file = pd.ExcelFile(file_path)
            return excel_file.sheet_names
        except Exception as e:
            raise ValueError(f"Error reading Excel file: {str(e)}")
    
    def convert_to_structured_data(self, file_path: str, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """Convert Excel data to structured format for further processing."""
        df = self.read_sheet(file_path, sheet_name)
        
        structured_data = {
            'source_type': 'excel',
            'source_file': file_path,
            'sheet_name': sheet_name or 'default',
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
                'null_counts': df.isnull().sum().to_dict()
            }
        }
        
        return structured_data   
    
    def extract_content(self, file_path: str, sheet_name: Optional[str] = None) -> str:
        """Extract content from Excel file - alias for extract_content_for_analysis"""
        return self.extract_content_for_analysis(file_path, sheet_name)