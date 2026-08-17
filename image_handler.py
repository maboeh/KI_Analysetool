"""
Image handler for processing images with OCR capabilities.
Supports PNG, JPG, and PDF image extraction using pytesseract.
"""

import os
import tempfile
from typing import List, Optional, Dict, Any, Tuple, Callable
from dataclasses import dataclass
from pathlib import Path
import logging

from error_handler import ErrorHandler, ErrorResult, handle_errors

try:
    import pytesseract
    from PIL import Image, ImageEnhance, ImageFilter
    from pdf2image import convert_from_path
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    IMPORT_ERROR = str(e)


@dataclass
class OCRResult:
    """Result of OCR processing."""
    text: str
    confidence: float
    language: str
    processing_info: Dict[str, Any]


@dataclass
class ImageInfo:
    """Information about an image file."""
    file_path: str
    file_size: int
    format: str
    dimensions: Tuple[int, int]
    mode: str
    has_text: bool
    preview_text: str
    total_pages: int = 1


class ImageHandler:
    """Handler for image processing with OCR capabilities."""
    
    SUPPORTED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.pdf', '.bmp', '.tiff', '.tif']
    MAX_FILE_SIZE_MB = 50
    MAX_IMAGE_DIMENSION = 4000
    PREVIEW_TEXT_LENGTH = 200
    
    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        Initialize ImageHandler.
        
        Args:
            tesseract_cmd: Path to tesseract executable (optional)
        """
        self.error_handler = ErrorHandler()
        self.logger = logging.getLogger(__name__)
        
        if not DEPENDENCIES_AVAILABLE:
            context = {"operation": "initialization", "missing_dependency": IMPORT_ERROR}
            error_result = self.error_handler.handle_error(
                ImportError(f"Required dependencies not available: {IMPORT_ERROR}"), 
                context=context
            )
            raise ImportError(self.error_handler.create_user_friendly_message(error_result))
        
        self.tesseract_cmd = tesseract_cmd
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        # Test if tesseract is available
        self.tesseract_available = True
        try:
            pytesseract.get_tesseract_version()
        except Exception as e:
            self.tesseract_available = False
            self.logger.warning(f"Tesseract not found or not working: {e}")
            self.logger.warning("OCR functionality will be limited")
    
    def can_handle(self, file_path: str) -> bool:
        """Check if the file can be handled by this handler."""
        if not os.path.exists(file_path):
            return False
        
        file_extension = Path(file_path).suffix.lower()
        return file_extension in self.SUPPORTED_EXTENSIONS
    
    def get_file_info(self, file_path: str) -> ImageInfo:
        """Get comprehensive information about the image file."""
        if not self.can_handle(file_path):
            raise ValueError(f"Unsupported file format. Supported formats: {self.SUPPORTED_EXTENSIONS}")
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > self.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise ValueError(f"File too large. Maximum size: {self.MAX_FILE_SIZE_MB}MB")
        
        try:
            file_extension = Path(file_path).suffix.lower()
            
            if file_extension == '.pdf':
                return self._get_pdf_info(file_path, file_size)
            else:
                return self._get_image_info(file_path, file_size)
                
        except Exception as e:
            raise ValueError(f"Error reading image file: {str(e)}")
    
    def _get_image_info(self, file_path: str, file_size: int) -> ImageInfo:
        """Get information about a regular image file."""
        with Image.open(file_path) as img:
            # Get basic image info
            format_name = img.format or "Unknown"
            dimensions = img.size
            mode = img.mode
            
            # Quick OCR test to see if there's text
            preview_text = ""
            has_text = False
            
            try:
                # Preprocess image for better OCR
                processed_img = self._preprocess_image(img)
                
                # Extract a small amount of text for preview
                text = pytesseract.image_to_string(processed_img, lang='deu+eng')
                preview_text = text[:self.PREVIEW_TEXT_LENGTH].strip()
                has_text = len(preview_text) > 10  # Assume text if we got reasonable content
                
            except Exception as e:
                logging.warning(f"OCR preview failed: {e}")
                preview_text = f"OCR-Vorschau nicht verfügbar: {str(e)}"
            
            return ImageInfo(
                file_path=file_path,
                file_size=file_size,
                format=format_name,
                dimensions=dimensions,
                mode=mode,
                has_text=has_text,
                preview_text=preview_text,
                total_pages=1
            )
    
    def _get_pdf_info(self, file_path: str, file_size: int) -> ImageInfo:
        """Get information about a PDF file."""
        try:
            # Convert first page to image for analysis
            images = convert_from_path(file_path, first_page=1, last_page=1, dpi=150)
            
            if not images:
                raise ValueError("No images found in PDF")
            
            first_page = images[0]
            
            # Get basic info from first page
            dimensions = first_page.size
            mode = first_page.mode
            
            # Try to get total page count
            total_pages = 1
            try:
                from pdf2image import pdfinfo_from_path
                pdf_info = pdfinfo_from_path(file_path)
                total_pages = int(pdf_info.get("Pages", 1))
            except Exception as e:
                logging.warning(f"Could not determine PDF page count: {e}")
            
            # Quick OCR test
            preview_text = ""
            has_text = False
            
            try:
                processed_img = self._preprocess_image(first_page)
                text = pytesseract.image_to_string(processed_img, lang='deu+eng')
                preview_text = text[:self.PREVIEW_TEXT_LENGTH].strip()
                has_text = len(preview_text) > 10
                
            except Exception as e:
                logging.warning(f"PDF OCR preview failed: {e}")
                preview_text = f"OCR-Vorschau nicht verfügbar: {str(e)}"
            
            return ImageInfo(
                file_path=file_path,
                file_size=file_size,
                format="PDF",
                dimensions=dimensions,
                mode=mode,
                has_text=has_text,
                preview_text=preview_text,
                total_pages=total_pages
            )
            
        except Exception as e:
            raise ValueError(f"Error processing PDF: {str(e)}")
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR accuracy."""
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize if too large
        width, height = image.size
        if width > self.MAX_IMAGE_DIMENSION or height > self.MAX_IMAGE_DIMENSION:
            ratio = min(self.MAX_IMAGE_DIMENSION / width, self.MAX_IMAGE_DIMENSION / height)
            new_size = (int(width * ratio), int(height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Enhance contrast and sharpness
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.2)
        
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.1)
        
        return image
    
    def extract_text(self, file_path: str, language: str = 'deu+eng', 
                    preprocessing: bool = True,
                    progress_callback: Optional[Callable[[str], None]] = None) -> OCRResult:
        """Extract text from image using OCR."""
        context = {"operation": "data_extraction", "file_path": file_path, "file_type": "image"}
        
        if not self.tesseract_available:
            context["error_details"] = "Tesseract OCR not available"
            error_result = self.error_handler.handle_error(
                RuntimeError("OCR functionality not available"), 
                context=context,
                fallback_function=lambda: self._create_fallback_ocr_result(file_path)
            )
            if error_result.fallback_result:
                return error_result.fallback_result
            raise RuntimeError(self.error_handler.create_user_friendly_message(error_result))
        
        if not self.can_handle(file_path):
            error_result = self.error_handler.handle_error(
                ValueError("Unsupported file format"), 
                context=context
            )
            raise ValueError(self.error_handler.create_user_friendly_message(error_result))
        
        try:
            file_extension = Path(file_path).suffix.lower()
            
            if file_extension == '.pdf':
                return self._extract_text_from_pdf(file_path, language, preprocessing, progress_callback)
            else:
                return self._extract_text_from_image(file_path, language, preprocessing)
                
        except Exception as e:
            context["error_details"] = str(e)
            context["language"] = language
            error_result = self.error_handler.handle_error(
                e, 
                context=context,
                fallback_function=lambda: self._create_fallback_ocr_result(file_path)
            )
            if error_result.fallback_result:
                return error_result.fallback_result
            raise type(e)(self.error_handler.create_user_friendly_message(error_result))
    
    def _extract_text_from_image(self, file_path: str, language: str, 
                                preprocessing: bool) -> OCRResult:
        """Extract text from a regular image file."""
        with Image.open(file_path) as img:
            if preprocessing:
                img = self._preprocess_image(img)
            
            # Extract text with confidence data
            try:
                text = pytesseract.image_to_string(img, lang=language)
                
                # Get confidence data
                data = pytesseract.image_to_data(img, lang=language, output_type=pytesseract.Output.DICT)
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                
                return OCRResult(
                    text=text.strip(),
                    confidence=avg_confidence,
                    language=language,
                    processing_info={
                        'preprocessing_applied': preprocessing,
                        'image_size': img.size,
                        'image_mode': img.mode,
                        'word_count': len(text.split()),
                        'character_count': len(text)
                    }
                )
                
            except Exception as e:
                # Fallback without confidence data
                text = pytesseract.image_to_string(img, lang=language)
                return OCRResult(
                    text=text.strip(),
                    confidence=0.0,
                    language=language,
                    processing_info={
                        'preprocessing_applied': preprocessing,
                        'image_size': img.size,
                        'image_mode': img.mode,
                        'word_count': len(text.split()),
                        'character_count': len(text),
                        'confidence_unavailable': True
                    }
                )
    
    def _extract_text_from_pdf(self, file_path: str, language: str, 
                              preprocessing: bool,
                              progress_callback: Optional[Callable[[str], None]] = None) -> OCRResult:
        """Extract text from all pages of a PDF file."""
        try:
            # Convert PDF pages to images
            if progress_callback:
                progress_callback("PDF wird in Bilder umgewandelt...")
            images = convert_from_path(file_path, dpi=200)
            
            all_text = []
            all_confidences = []
            total_words = 0
            total_chars = 0
            
            for i, image in enumerate(images):
                if progress_callback:
                    progress_callback(f"OCR Seite {i+1} von {len(images)}")
                
                if preprocessing:
                    image = self._preprocess_image(image)
                
                try:
                    # Extract text
                    page_text = pytesseract.image_to_string(image, lang=language)
                    all_text.append(f"--- Seite {i+1} ---\n{page_text}")
                    
                    # Get confidence data
                    data = pytesseract.image_to_data(image, lang=language, output_type=pytesseract.Output.DICT)
                    confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                    all_confidences.extend(confidences)
                    
                    total_words += len(page_text.split())
                    total_chars += len(page_text)
                    
                except Exception as e:
                    logging.warning(f"Error processing PDF page {i+1}: {e}")
                    all_text.append(f"--- Seite {i+1} ---\nFehler beim Verarbeiten der Seite: {str(e)}")
            
            combined_text = "\n\n".join(all_text)
            avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0
            
            return OCRResult(
                text=combined_text.strip(),
                confidence=avg_confidence,
                language=language,
                processing_info={
                    'preprocessing_applied': preprocessing,
                    'pages_processed': len(images),
                    'word_count': total_words,
                    'character_count': total_chars,
                    'source_type': 'pdf'
                }
            )
            
        except Exception as e:
            raise ValueError(f"Error processing PDF: {str(e)}")
    
    def extract_content_for_analysis(self, file_path: str, language: str = 'deu+eng',
                                   include_metadata: bool = True) -> str:
        """Extract content from image in a format suitable for AI analysis."""
        ocr_result = self.extract_text(file_path, language)
        
        content_parts = []
        
        if include_metadata:
            file_info = self.get_file_info(file_path)
            content_parts.append("Bild-/Dokument-Daten:")
            content_parts.append(f"Datei: {Path(file_path).name}")
            content_parts.append(f"Format: {file_info.format}")
            content_parts.append(f"Größe: {file_info.dimensions[0]}x{file_info.dimensions[1]} Pixel")
            content_parts.append(f"OCR-Vertrauen: {ocr_result.confidence:.1f}%")
            content_parts.append(f"Sprache: {ocr_result.language}")
            content_parts.append("")
        
        content_parts.append("Extrahierter Text:")
        content_parts.append("-" * 50)
        content_parts.append(ocr_result.text)
        
        if ocr_result.confidence < 70:
            content_parts.append("")
            content_parts.append("Hinweis: Niedrige OCR-Qualität erkannt. Der Text könnte Fehler enthalten.")
        
        return "\n".join(content_parts)
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported OCR languages."""
        try:
            return pytesseract.get_languages(config='')
        except Exception:
            # Return common languages as fallback
            return ['deu', 'eng', 'fra', 'spa', 'ita']
    
    def convert_to_structured_data(self, file_path: str, language: str = 'deu+eng') -> Dict[str, Any]:
        """Convert image OCR data to structured format for further processing."""
        ocr_result = self.extract_text(file_path, language)
        file_info = self.get_file_info(file_path)
        
        structured_data = {
            'source_type': 'image_ocr',
            'source_file': file_path,
            'file_info': {
                'format': file_info.format,
                'dimensions': file_info.dimensions,
                'file_size': file_info.file_size,
                'mode': file_info.mode
            },
            'ocr_result': {
                'text': ocr_result.text,
                'confidence': ocr_result.confidence,
                'language': ocr_result.language,
                'processing_info': ocr_result.processing_info
            },
            'text_analysis': {
                'word_count': len(ocr_result.text.split()),
                'character_count': len(ocr_result.text),
                'line_count': len(ocr_result.text.split('\n')),
                'has_meaningful_content': len(ocr_result.text.strip()) > 50,
                'confidence_level': 'high' if ocr_result.confidence > 80 else 'medium' if ocr_result.confidence > 60 else 'low'
            }
        }
        
        return structured_data
    
    def _create_fallback_ocr_result(self, file_path: str) -> OCRResult:
        """Create a fallback OCR result when OCR fails."""
        return OCRResult(
            text="[OCR-Texterkennung fehlgeschlagen - Bitte geben Sie den Text manuell ein]",
            confidence=0.0,
            language="unknown",
            processing_info={
                'fallback_mode': True,
                'original_file': file_path,
                'error_message': 'OCR processing failed, manual input required'
            }
        )
    
    def extract_content(self, file_path: str, language: str = 'deu+eng') -> str:
        """Extract content from image file - alias for extract_content_for_analysis"""
        return self.extract_content_for_analysis(file_path, language)