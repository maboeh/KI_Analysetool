"""
Comprehensive error handling system for enhanced results processing features.
Provides centralized error management, user-friendly messages, and graceful degradation.
"""

import logging
import traceback
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass
from enum import Enum
import os
import sys
from pathlib import Path


class ErrorSeverity(Enum):
    """Error severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better classification."""
    FILE_PROCESSING = "file_processing"
    DATA_EXTRACTION = "data_extraction"
    VISUALIZATION = "visualization"
    EXPORT = "export"
    NETWORK = "network"
    DEPENDENCY = "dependency"
    VALIDATION = "validation"
    SYSTEM = "system"


@dataclass
class ErrorInfo:
    """Comprehensive error information."""
    code: str
    message: str
    user_message: str
    severity: ErrorSeverity
    category: ErrorCategory
    suggestions: List[str]
    technical_details: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    recoverable: bool = True


@dataclass
class ErrorResult:
    """Result of error handling with recovery options."""
    success: bool
    error_info: Optional[ErrorInfo] = None
    fallback_result: Optional[Any] = None
    recovery_actions: List[str] = None


class ErrorHandler:
    """Centralized error handling system."""
    
    def __init__(self, log_level: int = logging.WARNING):
        """Initialize error handler with logging configuration."""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        
        # Create console handler if none exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Error code registry
        self.error_registry = self._initialize_error_registry()
    
    def _initialize_error_registry(self) -> Dict[str, ErrorInfo]:
        """Initialize the error code registry with predefined errors."""
        return {
            # File Processing Errors
            "FILE_NOT_FOUND": ErrorInfo(
                code="FILE_NOT_FOUND",
                message="File not found",
                user_message="Die ausgewählte Datei konnte nicht gefunden werden.",
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.FILE_PROCESSING,
                suggestions=[
                    "Überprüfen Sie, ob die Datei noch existiert",
                    "Stellen Sie sicher, dass der Dateipfad korrekt ist",
                    "Versuchen Sie, die Datei erneut auszuwählen"
                ]
            ),
            
            "FILE_TOO_LARGE": ErrorInfo(
                code="FILE_TOO_LARGE",
                message="File exceeds maximum size limit",
                user_message="Die Datei ist zu groß für die Verarbeitung.",
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.FILE_PROCESSING,
                suggestions=[
                    "Verwenden Sie eine kleinere Datei (unter {max_size}MB)",
                    "Teilen Sie große Dateien in kleinere Abschnitte auf",
                    "Komprimieren Sie die Datei vor dem Upload"
                ]
            ),
            
            "UNSUPPORTED_FORMAT": ErrorInfo(
                code="UNSUPPORTED_FORMAT",
                message="File format not supported",
                user_message="Das Dateiformat wird nicht unterstützt.",
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.FILE_PROCESSING,
                suggestions=[
                    "Unterstützte Formate: {supported_formats}",
                    "Konvertieren Sie die Datei in ein unterstütztes Format",
                    "Verwenden Sie die Texteingabe für andere Inhalte"
                ]
            ),
            
            "FILE_CORRUPTED": ErrorInfo(
                code="FILE_CORRUPTED",
                message="File appears to be corrupted",
                user_message="Die Datei scheint beschädigt zu sein.",
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.FILE_PROCESSING,
                suggestions=[
                    "Versuchen Sie, die Datei erneut zu speichern",
                    "Öffnen Sie die Datei in der ursprünglichen Anwendung",
                    "Verwenden Sie eine andere Version der Datei"
                ]
            ),
            
            # Data Extraction Errors
            "NO_DATA_FOUND": ErrorInfo(
                code="NO_DATA_FOUND",
                message="No extractable data found",
                user_message="Keine strukturierten Daten in der Datei gefunden.",
                severity=ErrorSeverity.WARNING,
                category=ErrorCategory.DATA_EXTRACTION,
                suggestions=[
                    "Die Datei enthält möglicherweise nur Text",
                    "Verwenden Sie die normale Textanalyse",
                    "Überprüfen Sie, ob die Datei Tabellen oder Listen enthält"
                ]
            ),
            
            "OCR_FAILED": ErrorInfo(
                code="OCR_FAILED",
                message="OCR text extraction failed",
                user_message="Texterkennung aus dem Bild fehlgeschlagen.",
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.DATA_EXTRACTION,
                suggestions=[
                    "Stellen Sie sicher, dass Tesseract OCR installiert ist",
                    "Verwenden Sie ein Bild mit besserer Qualität",
                    "Geben Sie den Text manuell ein"
                ]
            ),
            
            "ENCODING_ERROR": ErrorInfo(
                code="ENCODING_ERROR",
                message="Text encoding detection failed",
                user_message="Zeichenkodierung der Datei konnte nicht erkannt werden.",
                severity=ErrorSeverity.WARNING,
                category=ErrorCategory.DATA_EXTRACTION,
                suggestions=[
                    "Speichern Sie die Datei mit UTF-8 Kodierung",
                    "Verwenden Sie einen anderen Texteditor",
                    "Konvertieren Sie die Datei in ein anderes Format"
                ]
            ),
            
            # Visualization Errors
            "CHART_GENERATION_FAILED": ErrorInfo(
                code="CHART_GENERATION_FAILED",
                message="Chart generation failed",
                user_message="Diagrammerstellung fehlgeschlagen.",
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.VISUALIZATION,
                suggestions=[
                    "Überprüfen Sie, ob numerische Daten vorhanden sind",
                    "Versuchen Sie einen anderen Diagrammtyp",
                    "Exportieren Sie die Daten als Excel-Datei"
                ]
            ),
            
            "INSUFFICIENT_DATA": ErrorInfo(
                code="INSUFFICIENT_DATA",
                message="Insufficient data for visualization",
                user_message="Nicht genügend Daten für eine Visualisierung.",
                severity=ErrorSeverity.WARNING,
                category=ErrorCategory.VISUALIZATION,
                suggestions=[
                    "Mindestens 2 Datenpunkte erforderlich",
                    "Fügen Sie mehr Daten hinzu",
                    "Verwenden Sie eine andere Analysemethode"
                ]
            ),
            
            # Export Errors
            "EXPORT_FAILED": ErrorInfo(
                code="EXPORT_FAILED",
                message="Export operation failed",
                user_message="Export fehlgeschlagen.",
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.EXPORT,
                suggestions=[
                    "Überprüfen Sie die Schreibberechtigung im Zielordner",
                    "Stellen Sie sicher, dass genügend Speicherplatz vorhanden ist",
                    "Versuchen Sie einen anderen Speicherort"
                ]
            ),
            
            "PERMISSION_DENIED": ErrorInfo(
                code="PERMISSION_DENIED",
                message="Permission denied for file operation",
                user_message="Keine Berechtigung für diese Dateioperation.",
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.EXPORT,
                suggestions=[
                    "Überprüfen Sie die Dateiberechtigungen",
                    "Führen Sie die Anwendung als Administrator aus",
                    "Wählen Sie einen anderen Speicherort"
                ]
            ),
            
            # Dependency Errors
            "MISSING_DEPENDENCY": ErrorInfo(
                code="MISSING_DEPENDENCY",
                message="Required dependency not found",
                user_message="Erforderliche Komponente nicht gefunden.",
                severity=ErrorSeverity.CRITICAL,
                category=ErrorCategory.DEPENDENCY,
                suggestions=[
                    "Installieren Sie die fehlende Komponente: {dependency}",
                    "Überprüfen Sie die Installationsanleitung",
                    "Verwenden Sie alternative Funktionen"
                ]
            ),
            
            "VERSION_INCOMPATIBLE": ErrorInfo(
                code="VERSION_INCOMPATIBLE",
                message="Incompatible dependency version",
                user_message="Inkompatible Version einer Komponente.",
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.DEPENDENCY,
                suggestions=[
                    "Aktualisieren Sie die Komponente auf Version {required_version}",
                    "Überprüfen Sie die Systemanforderungen",
                    "Installieren Sie die Anwendung neu"
                ]
            ),
            
            # Network Errors
            "API_ERROR": ErrorInfo(
                code="API_ERROR",
                message="API request failed",
                user_message="Verbindung zum KI-Service fehlgeschlagen.",
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.NETWORK,
                suggestions=[
                    "Überprüfen Sie Ihre Internetverbindung",
                    "Kontrollieren Sie Ihren API-Schlüssel",
                    "Versuchen Sie es später erneut"
                ]
            ),
            
            "RATE_LIMIT_EXCEEDED": ErrorInfo(
                code="RATE_LIMIT_EXCEEDED",
                message="API rate limit exceeded",
                user_message="API-Limit erreicht. Bitte warten Sie.",
                severity=ErrorSeverity.WARNING,
                category=ErrorCategory.NETWORK,
                suggestions=[
                    "Warten Sie einige Minuten vor dem nächsten Versuch",
                    "Reduzieren Sie die Anzahl der Anfragen",
                    "Überprüfen Sie Ihr API-Kontingent"
                ]
            ),
            
            # System Errors
            "MEMORY_ERROR": ErrorInfo(
                code="MEMORY_ERROR",
                message="Insufficient memory",
                user_message="Nicht genügend Arbeitsspeicher verfügbar.",
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.SYSTEM,
                suggestions=[
                    "Schließen Sie andere Anwendungen",
                    "Verwenden Sie kleinere Dateien",
                    "Starten Sie die Anwendung neu"
                ]
            ),
            
            "DISK_SPACE_ERROR": ErrorInfo(
                code="DISK_SPACE_ERROR",
                message="Insufficient disk space",
                user_message="Nicht genügend Speicherplatz verfügbar.",
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.SYSTEM,
                suggestions=[
                    "Löschen Sie unnötige Dateien",
                    "Wählen Sie ein anderes Laufwerk",
                    "Bereinigen Sie den temporären Ordner"
                ]
            )
        }
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None,
                    fallback_function: Optional[Callable] = None) -> ErrorResult:
        """
        Handle an error with comprehensive error processing.
        
        Args:
            error: The exception that occurred
            context: Additional context information
            fallback_function: Optional fallback function to execute
            
        Returns:
            ErrorResult with error information and recovery options
        """
        # Determine error code and info
        error_info = self._classify_error(error, context)
        
        # Log the error
        self._log_error(error_info, error, context)
        
        # Try fallback function if provided
        fallback_result = None
        if fallback_function and error_info.recoverable:
            try:
                fallback_result = fallback_function()
            except Exception as fallback_error:
                self.logger.warning(f"Fallback function failed: {fallback_error}")
        
        # Generate recovery actions
        recovery_actions = self._generate_recovery_actions(error_info, context)
        
        return ErrorResult(
            success=False,
            error_info=error_info,
            fallback_result=fallback_result,
            recovery_actions=recovery_actions
        )
    
    def _classify_error(self, error: Exception, context: Optional[Dict[str, Any]]) -> ErrorInfo:
        """Classify an error and return appropriate ErrorInfo."""
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        # File not found errors
        if isinstance(error, FileNotFoundError) or "no such file" in error_message:
            return self._get_error_info("FILE_NOT_FOUND", context)
        
        # Permission errors
        if isinstance(error, PermissionError) or "permission denied" in error_message:
            return self._get_error_info("PERMISSION_DENIED", context)
        
        # Memory errors
        if isinstance(error, MemoryError) or "memory" in error_message:
            return self._get_error_info("MEMORY_ERROR", context)
        
        # Import/dependency errors
        if isinstance(error, ImportError) or isinstance(error, ModuleNotFoundError):
            return self._get_error_info("MISSING_DEPENDENCY", context, 
                                      {"dependency": str(error).split("'")[1] if "'" in str(error) else "unknown"})
        
        # Encoding errors
        if isinstance(error, UnicodeDecodeError) or "encoding" in error_message:
            return self._get_error_info("ENCODING_ERROR", context)
        
        # Network/API errors
        if "api" in error_message or "request" in error_message or "connection" in error_message:
            if "rate limit" in error_message or "429" in error_message:
                return self._get_error_info("RATE_LIMIT_EXCEEDED", context)
            else:
                return self._get_error_info("API_ERROR", context)
        
        # File format errors
        if "format" in error_message or "unsupported" in error_message:
            return self._get_error_info("UNSUPPORTED_FORMAT", context)

        # File too large errors
        if "too large" in error_message or "file size" in error_message or (
            context and "file_size" in context
        ):
            return self._get_error_info("FILE_TOO_LARGE", context)
        
        # OCR errors
        if "tesseract" in error_message or "ocr" in error_message:
            return self._get_error_info("OCR_FAILED", context)
        
        # Chart/visualization errors
        if context and context.get("operation") == "visualization":
            if "data" in error_message:
                return self._get_error_info("INSUFFICIENT_DATA", context)
            else:
                return self._get_error_info("CHART_GENERATION_FAILED", context)
        
        # Export errors
        if context and context.get("operation") == "export":
            return self._get_error_info("EXPORT_FAILED", context)
        
        # Generic error
        return ErrorInfo(
            code="UNKNOWN_ERROR",
            message=f"{error_type}: {str(error)}",
            user_message=f"Ein unerwarteter Fehler ist aufgetreten: {error_type}",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.SYSTEM,
            suggestions=[
                "Versuchen Sie die Operation erneut",
                "Starten Sie die Anwendung neu",
                "Kontaktieren Sie den Support mit den technischen Details"
            ],
            technical_details=traceback.format_exc(),
            context=context,
            recoverable=True
        )
    
    def _get_error_info(self, error_code: str, context: Optional[Dict[str, Any]] = None,
                       format_params: Optional[Dict[str, Any]] = None) -> ErrorInfo:
        """Get error info from registry with context formatting."""
        if error_code not in self.error_registry:
            return self.error_registry["UNKNOWN_ERROR"]
        
        error_info = self.error_registry[error_code]
        
        # Format suggestions with context parameters
        formatted_suggestions = []
        for suggestion in error_info.suggestions:
            try:
                if format_params:
                    formatted_suggestion = suggestion.format(**format_params)
                else:
                    formatted_suggestion = suggestion
                formatted_suggestions.append(formatted_suggestion)
            except KeyError:
                formatted_suggestions.append(suggestion)
        
        # Create new ErrorInfo with formatted suggestions and context
        return ErrorInfo(
            code=error_info.code,
            message=error_info.message,
            user_message=error_info.user_message,
            severity=error_info.severity,
            category=error_info.category,
            suggestions=formatted_suggestions,
            technical_details=error_info.technical_details,
            context=context,
            recoverable=error_info.recoverable
        )
    
    def _log_error(self, error_info: ErrorInfo, original_error: Exception,
                  context: Optional[Dict[str, Any]]) -> None:
        """Log error with appropriate level and details."""
        log_message = f"[{error_info.code}] {error_info.message}"
        
        if context:
            log_message += f" | Context: {context}"
        
        if error_info.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message, exc_info=original_error)
        elif error_info.severity == ErrorSeverity.ERROR:
            self.logger.error(log_message, exc_info=original_error)
        elif error_info.severity == ErrorSeverity.WARNING:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    def _generate_recovery_actions(self, error_info: ErrorInfo,
                                 context: Optional[Dict[str, Any]]) -> List[str]:
        """Generate specific recovery actions based on error and context."""
        recovery_actions = []
        
        # Add context-specific recovery actions
        if context:
            operation = context.get("operation")
            file_path = context.get("file_path")
            
            if operation == "file_processing" and file_path:
                recovery_actions.extend([
                    f"Datei erneut auswählen: {Path(file_path).name}",
                    "Alternative Eingabemethode verwenden",
                    "Datei in anderem Format speichern"
                ])
            
            elif operation == "export":
                recovery_actions.extend([
                    "Anderen Speicherort wählen",
                    "Dateiname ändern",
                    "Als anderes Format exportieren"
                ])
            
            elif operation == "visualization":
                recovery_actions.extend([
                    "Daten als Excel exportieren",
                    "Anderen Diagrammtyp wählen",
                    "Daten manuell überprüfen"
                ])
        
        # Add general recovery actions based on category
        if error_info.category == ErrorCategory.DEPENDENCY:
            recovery_actions.extend([
                "Abhängigkeiten installieren",
                "Anwendung neu installieren",
                "Systemanforderungen überprüfen"
            ])
        
        elif error_info.category == ErrorCategory.NETWORK:
            recovery_actions.extend([
                "Internetverbindung prüfen",
                "Später erneut versuchen",
                "Offline-Modus verwenden"
            ])
        
        return recovery_actions
    
    def create_user_friendly_message(self, error_result: ErrorResult) -> str:
        """Create a comprehensive user-friendly error message."""
        if not error_result.error_info:
            return "Ein unbekannter Fehler ist aufgetreten."
        
        error_info = error_result.error_info
        
        message_parts = [
            f"❌ {error_info.user_message}",
            ""
        ]
        
        if error_info.suggestions:
            message_parts.append("💡 Lösungsvorschläge:")
            for i, suggestion in enumerate(error_info.suggestions, 1):
                message_parts.append(f"   {i}. {suggestion}")
            message_parts.append("")
        
        if error_result.recovery_actions:
            message_parts.append("🔧 Mögliche Aktionen:")
            for i, action in enumerate(error_result.recovery_actions, 1):
                message_parts.append(f"   {i}. {action}")
            message_parts.append("")
        
        if error_result.fallback_result:
            message_parts.append("ℹ️ Alternative Ergebnisse verfügbar.")
            message_parts.append("")
        
        if error_info.severity == ErrorSeverity.CRITICAL:
            message_parts.append("⚠️ Kritischer Fehler - Anwendung muss möglicherweise neu gestartet werden.")
        
        return "\n".join(message_parts)


# Decorator for automatic error handling
def handle_errors(error_handler: ErrorHandler, context: Optional[Dict[str, Any]] = None,
                 fallback_function: Optional[Callable] = None):
    """Decorator for automatic error handling in functions."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_result = error_handler.handle_error(e, context, fallback_function)
                # You can customize what to return here
                return error_result
        return wrapper
    return decorator


# Global error handler instance
global_error_handler = ErrorHandler()