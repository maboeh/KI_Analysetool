"""
Results processor for integrating enhanced processing with existing analysis functions.

This module provides the ResultsProcessor class that wraps existing analysis
functions to return ProcessedResult objects with extracted data and suggested actions.
"""

import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from data_models import (
    ProcessedResult, StructuredData, SourceInfo, ResultMetadata, Action, ActionType,
    create_default_actions, create_source_info_from_path
)
from data_extractor import DataExtractor, ExtractionConfig
from chart_generator import ChartGenerator
from follow_up_actions import FollowUpActionSystem
from analysis import AnalysisFailure, AnalysisOutcome
import analysis


class ResultsProcessor:
    """
    Main processor for integrating enhanced results processing with existing analysis functions.
    
    This class wraps the existing analysis functions to return ProcessedResult objects
    that include extracted structured data, suggested visualizations, and follow-up actions.
    """
    
    def __init__(self):
        self.data_extractor = DataExtractor(ExtractionConfig())
        self.chart_generator = ChartGenerator()
        self.follow_up_system = FollowUpActionSystem()
        self.history: List[ProcessedResult] = []
        self.current_result: Optional[ProcessedResult] = None
    
    def process_analysis_result(
        self, 
        raw_result: str, 
        source_path: str, 
        analysis_type: str = "general",
        model_used: str = "gpt-4o",
        tokens_used: Optional[int] = None
    ) -> ProcessedResult:
        """
        Process a raw analysis result into a ProcessedResult with enhanced features.
        
        Args:
            raw_result: The raw text result from analysis
            source_path: Path or URL of the analyzed content
            analysis_type: Type of analysis performed
            model_used: AI model used for analysis
            
        Returns:
            ProcessedResult object with extracted data and suggested actions
        """
        start_time = time.time()
        
        # Create source info
        source_info = create_source_info_from_path(source_path)
        
        # Extract structured data from the result
        extracted_data = self.data_extractor.extract_structured_data(raw_result)
        
        # Create metadata
        processing_time = time.time() - start_time
        metadata = ResultMetadata(
            analysis_type=analysis_type,
            processing_time=processing_time,
            model_used=model_used,
            tokens_used=tokens_used,
            confidence_score=self._calculate_confidence_score(extracted_data)
        )
        
        # Create the processed result
        processed_result = ProcessedResult(
            content=raw_result,
            source_info=source_info,
            extracted_data=extracted_data,
            metadata=metadata
        )
        
        # Add suggested follow-up actions
        self._add_follow_up_actions(processed_result)
        
        # Add visualization suggestions
        self._add_visualization_suggestions(processed_result)
        
        # Store in history
        self.history.append(processed_result)
        self.current_result = processed_result
        
        return processed_result

    def process_analysis_outcome(
        self,
        outcome: AnalysisOutcome,
        source_path: str,
        analysis_type: str = "general",
        model_used: Optional[str] = None
    ) -> ProcessedResult:
        if not outcome.success:
            raise AnalysisFailure(outcome.error)
        return self.process_analysis_result(
            raw_result=outcome.content,
            source_path=source_path,
            analysis_type=analysis_type,
            model_used=model_used or analysis.get_model(),
            tokens_used=outcome.prompt_tokens + outcome.completion_tokens
        )
    
    def analyze_text_enhanced(self, text: str, source_path: str = "") -> ProcessedResult:
        """
        Enhanced version of text analysis that returns ProcessedResult.
        
        Args:
            text: Text content to analyze
            source_path: Source path or URL
            
        Returns:
            ProcessedResult with enhanced processing
        """
        # Use existing analysis function
        raw_result = analysis.real_ai_analyse_fortext(text)
        
        # Process the result
        return self.process_analysis_result(
            raw_result=raw_result,
            source_path=source_path,
            analysis_type="text_analysis"
        )
    
    def analyze_pdf_enhanced(self, pdf_path: str, prompt: str) -> ProcessedResult:
        """
        Enhanced version of PDF analysis that returns ProcessedResult.
        
        Args:
            pdf_path: Path to PDF file
            prompt: Analysis prompt
            
        Returns:
            ProcessedResult with enhanced processing
        """
        # Use existing analysis function
        raw_result = analysis.real_ai_analyse_forpdf(pdf_path, prompt)
        
        # Process the result
        return self.process_analysis_result(
            raw_result=raw_result,
            source_path=pdf_path,
            analysis_type="pdf_analysis"
        )
    
    def analyze_content_enhanced(self, file_path: str, custom_prompt: str = "") -> ProcessedResult:
        """
        Enhanced version of content analysis that handles multiple input types.
        
        Args:
            file_path: Path to file or URL
            custom_prompt: Optional custom prompt for analysis
            
        Returns:
            ProcessedResult with enhanced processing
        """
        try:
            # Extract content using existing function
            content = analysis.text_extraction_youtube_website(file_path)
            
            if content.startswith("Fehler:") or content.startswith("Ein Fehler"):
                # Handle error case
                return ProcessedResult(
                    content=content,
                    source_info=create_source_info_from_path(file_path),
                    metadata=ResultMetadata(analysis_type="error")
                )
            
            # Determine analysis type based on file path
            if analysis.is_pdf_file(file_path):
                prompt = custom_prompt or "Analysiere dieses PDF-Dokument und fasse die wichtigsten Punkte zusammen."
                return self.analyze_pdf_enhanced(file_path, prompt)
            else:
                # For text, YouTube, or website content
                analysis_prompt = custom_prompt or content
                return self.analyze_text_enhanced(analysis_prompt, file_path)
                
        except Exception as e:
            # Handle exceptions gracefully
            error_result = ProcessedResult(
                content=f"Fehler bei der Analyse: {str(e)}",
                source_info=create_source_info_from_path(file_path),
                metadata=ResultMetadata(analysis_type="error")
            )
            return error_result
    
    def execute_follow_up_action(
        self, 
        result: ProcessedResult, 
        action_type: ActionType, 
        parameters: Dict[str, Any] = None
    ) -> ProcessedResult:
        """
        Execute a follow-up action on a result using the integrated follow-up system.
        
        Args:
            result: The original result to act upon
            action_type: Type of action to execute
            parameters: Optional parameters for the action
            
        Returns:
            New ProcessedResult from the follow-up action
        """
        parameters = parameters or {}
        
        # Create action object
        action = Action(
            action_type=action_type,
            label=action_type.value.title(),
            description=f"Execute {action_type.value} action",
            parameters=parameters
        )
        
        # Execute using the follow-up system
        follow_up_result = self.follow_up_system.execute_follow_up_action(
            result, action, parent_step_id=result.id
        )
        
        # Add to our local history as well for backward compatibility
        self.history.append(follow_up_result)
        self.current_result = follow_up_result
        
        return follow_up_result
    
    def get_action_suggestions(self, result: ProcessedResult) -> List[Action]:
        """
        Get suggested actions based on result content and extracted data.
        
        Args:
            result: The result to analyze for action suggestions
            
        Returns:
            List of suggested Action objects
        """
        suggestions = []
        
        # Always include basic actions
        suggestions.extend(create_default_actions())
        
        # Add data-specific actions
        if result.extracted_data.has_visualizable_data():
            suggestions.append(Action(
                action_type=ActionType.VISUALIZE,
                label="Visualisieren",
                description="Erstelle Diagramme aus den extrahierten Daten"
            ))
        
        if result.has_exportable_data():
            suggestions.append(Action(
                action_type=ActionType.EXPORT,
                label="Exportieren",
                description="Exportiere strukturierte Daten als Excel-Datei"
            ))
        
        # Content-specific suggestions
        if len(result.content) > 1000:
            suggestions.append(Action(
                action_type=ActionType.SUMMARIZE,
                label="Kurzzusammenfassung",
                description="Erstelle eine kurze Zusammenfassung des Inhalts",
                parameters={"length": "short"}
            ))
        
        if result.extracted_data.entities:
            suggestions.append(Action(
                action_type=ActionType.ANALYZE,
                label="Entitäten analysieren",
                description="Analysiere die gefundenen Personen, Orte und Organisationen",
                parameters={"focus": "Entitätenanalyse"}
            ))
        
        if result.extracted_data.numeric_values:
            suggestions.append(Action(
                action_type=ActionType.ANALYZE,
                label="Zahlen analysieren",
                description="Analysiere die numerischen Daten und Trends",
                parameters={"focus": "numerische Analyse"}
            ))
        
        return suggestions
    
    def get_visualization_suggestions(self, result: ProcessedResult) -> List[Dict[str, Any]]:
        """
        Get visualization suggestions based on extracted data.
        
        Args:
            result: The result to analyze for visualization options
            
        Returns:
            List of visualization suggestion dictionaries
        """
        suggestions = []
        
        if not result.extracted_data.has_visualizable_data():
            return suggestions
        
        # Get suggestions from chart generator
        chart_suggestions = self.chart_generator.suggest_chart_types(result.extracted_data)
        
        for chart_suggestion in chart_suggestions:
            chart_type = chart_suggestion.chart_type
            suggestions.append({
                'type': chart_type.value,
                'title': f"{chart_type.value.title()} Chart",
                'description': f"Erstelle ein {chart_type.value}-Diagramm aus den Daten",
                'data_source': 'extracted_data',
                'confidence': chart_suggestion.confidence,
                'reasoning': chart_suggestion.reasoning
            })
        
        return suggestions
    
    def _add_follow_up_actions(self, result: ProcessedResult):
        """Add appropriate follow-up actions to a result."""
        suggested_actions = self.get_action_suggestions(result)
        result.follow_up_actions = suggested_actions
    
    def _add_visualization_suggestions(self, result: ProcessedResult):
        """Add visualization suggestions to a result."""
        if result.extracted_data.has_visualizable_data():
            viz_suggestions = self.get_visualization_suggestions(result)
            # Store suggestions in metadata for now
            result.metadata.tags.extend([f"viz_suggestion_{s['type']}" for s in viz_suggestions])
    
    def _calculate_confidence_score(self, extracted_data: StructuredData) -> float:
        """
        Calculate a confidence score based on extracted data quality.
        
        Args:
            extracted_data: The extracted structured data
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        score = 0.0
        factors = 0
        
        # Factor in entity confidence
        if extracted_data.entities:
            avg_entity_confidence = sum(e.confidence for e in extracted_data.entities) / len(extracted_data.entities)
            score += avg_entity_confidence
            factors += 1
        
        # Factor in data completeness
        data_types_found = 0
        if extracted_data.tables:
            data_types_found += 1
        if extracted_data.entities:
            data_types_found += 1
        if extracted_data.numeric_values:
            data_types_found += 1
        if extracted_data.temporal_data:
            data_types_found += 1
        
        completeness_score = min(1.0, data_types_found / 4.0)
        score += completeness_score
        factors += 1
        
        # Factor in data volume
        total_items = (len(extracted_data.tables) + len(extracted_data.entities) + 
                      len(extracted_data.numeric_values) + len(extracted_data.temporal_data))
        volume_score = min(1.0, total_items / 10.0)  # Normalize to 10 items = 1.0
        score += volume_score
        factors += 1
        
        return score / factors if factors > 0 else 0.5
    
    def get_history(self) -> List[ProcessedResult]:
        """Get the analysis history."""
        return self.history.copy()
    
    def clear_history(self):
        """Clear the analysis history."""
        self.history.clear()
        self.current_result = None
        self.follow_up_system.clear_history()
    
    def get_current_result(self) -> Optional[ProcessedResult]:
        """Get the current result."""
        return self.current_result
    
    def get_analysis_chain(self, step_id: str) -> List[ProcessedResult]:
        """
        Get the complete analysis chain for a specific step.
        
        Args:
            step_id: The step ID to get the chain for
            
        Returns:
            List of ProcessedResult objects in chronological order
        """
        steps = self.follow_up_system.get_step_chain(step_id)
        return [step.result for step in steps]
    
    def navigate_to_step(self, step_id: str) -> Optional[ProcessedResult]:
        """
        Navigate to a specific step in the analysis history.
        
        Args:
            step_id: The step ID to navigate to
            
        Returns:
            The ProcessedResult of the step, or None if not found
        """
        result = self.follow_up_system.navigate_to_step(step_id)
        if result:
            self.current_result = result
        return result
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the current analysis session."""
        return self.follow_up_system.get_session_summary()
    
    def save_analysis_session(self, session_name: str) -> str:
        """
        Save the current analysis session to disk.
        
        Args:
            session_name: Name for the saved session
            
        Returns:
            Path to the saved session file
        """
        return self.follow_up_system.save_session(session_name)
    
    def load_analysis_session(self, session_file: str):
        """
        Load an analysis session from disk.
        
        Args:
            session_file: Path to the session file to load
        """
        self.follow_up_system.load_session(session_file)
        
        # Update local history for backward compatibility
        analysis_steps = self.follow_up_system.get_analysis_history()
        self.history = [step.result for step in analysis_steps]
        if self.history:
            self.current_result = self.history[-1]


# Factory function for creating a configured ResultsProcessor
def create_results_processor() -> ResultsProcessor:
    """
    Create a configured ResultsProcessor instance.
    
    Returns:
        Configured ResultsProcessor ready for use
    """
    return ResultsProcessor()


# Integration functions for backward compatibility
def enhanced_analyze_text(text: str, source_path: str = "") -> ProcessedResult:
    """
    Enhanced text analysis function that returns ProcessedResult.
    
    This function provides a drop-in replacement for the original analysis
    functions while returning enhanced results.
    
    Args:
        text: Text to analyze
        source_path: Source path or URL
        
    Returns:
        ProcessedResult with enhanced processing
    """
    processor = create_results_processor()
    return processor.analyze_text_enhanced(text, source_path)


def enhanced_analyze_pdf(pdf_path: str, prompt: str) -> ProcessedResult:
    """
    Enhanced PDF analysis function that returns ProcessedResult.
    
    Args:
        pdf_path: Path to PDF file
        prompt: Analysis prompt
        
    Returns:
        ProcessedResult with enhanced processing
    """
    processor = create_results_processor()
    return processor.analyze_pdf_enhanced(pdf_path, prompt)


def enhanced_analyze_content(file_path: str, custom_prompt: str = "") -> ProcessedResult:
    """
    Enhanced content analysis function that handles multiple input types.
    
    Args:
        file_path: Path to file or URL
        custom_prompt: Optional custom prompt
        
    Returns:
        ProcessedResult with enhanced processing
    """
    processor = create_results_processor()
    return processor.analyze_content_enhanced(file_path, custom_prompt)