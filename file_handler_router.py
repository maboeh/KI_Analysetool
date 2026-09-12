"""
File handler router for detecting file types and routing to appropriate handlers.
Provides unified interface for processing different file formats.
"""

import os
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass
import logging

# Import handlers
from excel_handler import ExcelHandler
from image_handler import ImageHandler
from csv_handler import CSVHandler


@dataclass
class FileTypeInfo:
    """Information about a detected file type."""
    file_path: str
    file_type: str
    handler_class: str
    confidence: float
    supported: bool
    error_message: Optional[str] = None


@dataclass
class ProcessingResult:
    """Result of file processing."""
    file_path: str
    file_type: str
    success: bool
    content: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processing_info: Optional[Dict[str, Any]] = None


class FileHandlerRouter:
    """Router for detecting file types and delegating to appropriate handlers."""
    
    def __init__(self):
        """Initialize the router with available handlers."""
        self.handlers = {}
        self.file_type_mapping = {}
        
        # Initialize handlers
        try:
            self.handlers['excel'] = ExcelHandler()
            self.file_type_mapping.update({
                '.xlsx': 'excel',
                '.xls': 'excel'
            })
        except Exception as e:
            logging.warning(f"Excel handler not available: {e}")
        
        try:
            self.handlers['image'] = ImageHandler()
            self.file_type_mapping.update({
                '.png': 'image',
                '.jpg': 'image',
                '.jpeg': 'image',
                '.pdf': 'image',  # PDF can be handled by image handler for OCR
                '.bmp': 'image',
                '.tiff': 'image',
                '.tif': 'image'
            })
        except Exception as e:
            logging.warning(f"Image handler not available: {e}")
        
        try:
            self.handlers['csv'] = CSVHandler()
            self.file_type_mapping.update({
                '.csv': 'csv',
                '.tsv': 'csv',
                '.txt': 'csv'  # Text files might be CSV
            })
        except Exception as e:
            logging.warning(f"CSV handler not available: {e}")
    
    def detect_file_type(self, file_path: str) -> FileTypeInfo:
        """
        Detect the file type and determine which handler should process it.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            FileTypeInfo with detection results
        """
        if not os.path.exists(file_path):
            return FileTypeInfo(
                file_path=file_path,
                file_type='unknown',
                handler_class='none',
                confidence=0.0,
                supported=False,
                error_message="File does not exist"
            )
        
        file_extension = Path(file_path).suffix.lower()
        
        # Check if extension is directly mapped
        if file_extension in self.file_type_mapping:
            file_type = self.file_type_mapping[file_extension]
            
            # Verify handler can actually handle the file
            if file_type in self.handlers:
                handler = self.handlers[file_type]
                if handler.can_handle(file_path):
                    return FileTypeInfo(
                        file_path=file_path,
                        file_type=file_type,
                        handler_class=handler.__class__.__name__,
                        confidence=1.0,
                        supported=True
                    )
                else:
                    return FileTypeInfo(
                        file_path=file_path,
                        file_type=file_type,
                        handler_class=handler.__class__.__name__,
                        confidence=0.5,
                        supported=False,
                        error_message=f"Handler cannot process this {file_type} file"
                    )
        
        # Special handling for ambiguous extensions like .txt
        if file_extension == '.txt':
            # Try to determine if it's CSV-like
            try:
                if 'csv' in self.handlers:
                    csv_handler = self.handlers['csv']
                    if csv_handler.can_handle(file_path):
                        # Try to read a few lines to see if it looks like CSV
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            first_lines = [f.readline().strip() for _ in range(3)]
                        
                        # Simple heuristic: if lines contain common delimiters, likely CSV
                        delimiters = [',', ';', '\t', '|']
                        delimiter_counts = sum(
                            1 for line in first_lines 
                            for delimiter in delimiters 
                            if delimiter in line
                        )
                        
                        if delimiter_counts > 0:
                            return FileTypeInfo(
                                file_path=file_path,
                                file_type='csv',
                                handler_class='CSVHandler',
                                confidence=0.7,
                                supported=True
                            )
            except Exception as e:
                logging.debug(f"Error analyzing .txt file as CSV: {e}")
        
        # PDF files can be handled by image handler for OCR
        if file_extension == '.pdf' and 'image' in self.handlers:
            return FileTypeInfo(
                file_path=file_path,
                file_type='image',
                handler_class='ImageHandler',
                confidence=0.9,
                supported=True
            )
        
        # Unknown or unsupported file type
        return FileTypeInfo(
            file_path=file_path,
            file_type='unknown',
            handler_class='none',
            confidence=0.0,
            supported=False,
            error_message=f"Unsupported file type: {file_extension}"
        )
    
    def get_supported_extensions(self) -> Dict[str, List[str]]:
        """Get list of supported file extensions by handler type."""
        supported = {}
        
        for handler_type, handler in self.handlers.items():
            if hasattr(handler, 'SUPPORTED_EXTENSIONS'):
                supported[handler_type] = handler.SUPPORTED_EXTENSIONS
        
        return supported
    
    def process_file(self, file_path: str, **kwargs) -> ProcessingResult:
        """
        Process a file using the appropriate handler.
        
        Args:
            file_path: Path to the file to process
            **kwargs: Additional arguments passed to the handler
            
        Returns:
            ProcessingResult with processing outcome
        """
        # Detect file type
        file_info = self.detect_file_type(file_path)
        
        if not file_info.supported:
            return ProcessingResult(
                file_path=file_path,
                file_type=file_info.file_type,
                success=False,
                error_message=file_info.error_message or "File type not supported"
            )
        
        # Get appropriate handler
        handler = self.handlers.get(file_info.file_type)
        if not handler:
            return ProcessingResult(
                file_path=file_path,
                file_type=file_info.file_type,
                success=False,
                error_message=f"No handler available for {file_info.file_type}"
            )
        
        try:
            # Extract content for analysis
            content = handler.extract_content_for_analysis(file_path, **kwargs)
            
            # Get structured data
            structured_data = handler.convert_to_structured_data(file_path)
            
            # Get additional processing info
            processing_info = {
                'handler_used': handler.__class__.__name__,
                'file_type_detected': file_info.file_type,
                'detection_confidence': file_info.confidence
            }
            
            # Add handler-specific info
            if hasattr(handler, 'get_file_info'):
                try:
                    handler_info = handler.get_file_info(file_path)
                    processing_info['handler_info'] = handler_info
                except Exception as e:
                    logging.debug(f"Could not get handler info: {e}")
            
            return ProcessingResult(
                file_path=file_path,
                file_type=file_info.file_type,
                success=True,
                content=content,
                structured_data=structured_data,
                processing_info=processing_info
            )
            
        except Exception as e:
            return ProcessingResult(
                file_path=file_path,
                file_type=file_info.file_type,
                success=False,
                error_message=f"Processing failed: {str(e)}"
            )
    
    def process_multiple_files(self, file_paths: List[str], 
                             combine_similar: bool = True) -> Dict[str, Any]:
        """
        Process multiple files, optionally combining files of the same type.
        
        Args:
            file_paths: List of file paths to process
            combine_similar: Whether to combine files of the same type
            
        Returns:
            Dictionary with processing results
        """
        if not file_paths:
            return {
                'success': False,
                'error': 'No file paths provided'
            }
        
        # Group files by type
        files_by_type = {}
        individual_results = {}
        
        for file_path in file_paths:
            file_info = self.detect_file_type(file_path)
            
            if file_info.supported:
                if file_info.file_type not in files_by_type:
                    files_by_type[file_info.file_type] = []
                files_by_type[file_info.file_type].append(file_path)
            else:
                individual_results[file_path] = ProcessingResult(
                    file_path=file_path,
                    file_type=file_info.file_type,
                    success=False,
                    error_message=file_info.error_message
                )
        
        # Process each group
        combined_results = {}
        
        for file_type, type_files in files_by_type.items():
            if len(type_files) == 1 or not combine_similar:
                # Process individually
                for file_path in type_files:
                    result = self.process_file(file_path)
                    individual_results[file_path] = result
            else:
                # Try to combine files of the same type
                handler = self.handlers.get(file_type)
                
                if file_type == 'csv' and hasattr(handler, 'process_multiple_files'):
                    # CSV handler supports multi-file processing
                    try:
                        multi_result = handler.process_multiple_files(type_files)
                        combined_results[file_type] = {
                            'type': 'combined',
                            'files': type_files,
                            'result': multi_result,
                            'content': handler.extract_combined_content_for_analysis(type_files)
                        }
                    except Exception as e:
                        # Fall back to individual processing
                        for file_path in type_files:
                            result = self.process_file(file_path)
                            individual_results[file_path] = result
                else:
                    # Process individually for other types
                    for file_path in type_files:
                        result = self.process_file(file_path)
                        individual_results[file_path] = result
        
        return {
            'success': True,
            'files_processed': len([r for r in individual_results.values() if r.success]) + 
                             sum(len(cr['files']) for cr in combined_results.values()),
            'total_files': len(file_paths),
            'individual_results': individual_results,
            'combined_results': combined_results,
            'files_by_type': {k: len(v) for k, v in files_by_type.items()},
            'supported_handlers': list(self.handlers.keys())
        }
    
    def get_analysis_content(self, file_paths: Union[str, List[str]], 
                           combine_similar: bool = True) -> str:
        """
        Get combined analysis content from one or more files.
        
        Args:
            file_paths: Single file path or list of file paths
            combine_similar: Whether to combine files of the same type
            
        Returns:
            Combined content string ready for AI analysis
        """
        if isinstance(file_paths, str):
            file_paths = [file_paths]
        
        if len(file_paths) == 1:
            # Single file processing
            result = self.process_file(file_paths[0])
            if result.success:
                return result.content
            else:
                return f"Fehler beim Verarbeiten der Datei: {result.error_message}"
        
        # Multiple files processing
        multi_result = self.process_multiple_files(file_paths, combine_similar)
        
        if not multi_result['success']:
            return f"Fehler beim Verarbeiten der Dateien: {multi_result.get('error', 'Unbekannter Fehler')}"
        
        content_parts = []
        content_parts.append("Multi-Datei-Analyse:")
        content_parts.append(f"Verarbeitete Dateien: {multi_result['files_processed']} von {multi_result['total_files']}")
        content_parts.append(f"Dateitypen: {', '.join(multi_result['files_by_type'].keys())}")
        content_parts.append("")
        
        # Add combined results
        for file_type, combined_result in multi_result['combined_results'].items():
            content_parts.append(f"=== Kombinierte {file_type.upper()}-Daten ===")
            content_parts.append(combined_result['content'])
            content_parts.append("")
        
        # Add individual results
        for file_path, result in multi_result['individual_results'].items():
            if result.success:
                content_parts.append(f"=== {Path(file_path).name} ===")
                content_parts.append(result.content)
                content_parts.append("")
            else:
                content_parts.append(f"=== Fehler: {Path(file_path).name} ===")
                content_parts.append(f"Fehler: {result.error_message}")
                content_parts.append("")
        
        return "\n".join(content_parts)
    
    def get_handler_info(self) -> Dict[str, Any]:
        """Get information about available handlers."""
        info = {
            'available_handlers': list(self.handlers.keys()),
            'supported_extensions': self.get_supported_extensions(),
            'handler_details': {}
        }
        
        for handler_type, handler in self.handlers.items():
            handler_info = {
                'class_name': handler.__class__.__name__,
                'supported_extensions': getattr(handler, 'SUPPORTED_EXTENSIONS', [])
            }
            
            # Add handler-specific info
            if hasattr(handler, 'MAX_FILE_SIZE_MB'):
                handler_info['max_file_size_mb'] = handler.MAX_FILE_SIZE_MB
            
            info['handler_details'][handler_type] = handler_info
        
        return info 
    
    def get_handler(self, file_path: str):
        """Get appropriate handler for file - alias for get_handler_for_file"""
        file_info = self.detect_file_type(file_path)
        if file_info.supported and file_info.file_type in self.handlers:
            return self.handlers[file_info.file_type]
        return None