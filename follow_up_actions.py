"""
Follow-up action system for enhanced results processing.

This module provides the framework for executing follow-up analyses,
preserving context between analysis steps, and tracking analysis history.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from pathlib import Path

from data_models import (
    ProcessedResult, Action, ActionType, SourceInfo, ResultMetadata
)
import analysis


@dataclass
class AnalysisContext:
    """Context information for analysis steps."""
    original_result_id: str
    step_number: int
    action_chain: List[ActionType] = field(default_factory=list)
    parameters_history: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'original_result_id': self.original_result_id,
            'step_number': self.step_number,
            'action_chain': [action.value for action in self.action_chain],
            'parameters_history': self.parameters_history,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisContext':
        return cls(
            original_result_id=data['original_result_id'],
            step_number=data['step_number'],
            action_chain=[ActionType(action) for action in data['action_chain']],
            parameters_history=data['parameters_history'],
            created_at=datetime.fromisoformat(data['created_at'])
        )


@dataclass
class AnalysisStep:
    """Represents a single step in an analysis workflow."""
    result: ProcessedResult
    context: AnalysisContext
    parent_step_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'result': self.result.to_dict(),
            'context': self.context.to_dict(),
            'parent_step_id': self.parent_step_id
        }


class FollowUpActionExecutor:
    """
    Executor for follow-up actions with context preservation.
    
    This class handles the execution of follow-up actions while maintaining
    context and building analysis chains.
    """
    
    def __init__(self):
        self.action_handlers: Dict[ActionType, Callable] = {
            ActionType.SUMMARIZE: self._execute_summarize,
            ActionType.DEEPEN: self._execute_deepen,
            ActionType.TRANSLATE: self._execute_translate,
            ActionType.ANALYZE: self._execute_analyze,
            ActionType.EXPLAIN: self._execute_explain,
            ActionType.EXPORT: self._execute_export,
            ActionType.VISUALIZE: self._execute_visualize
        }
    
    def execute_action(
        self, 
        result: ProcessedResult, 
        action: Action, 
        context: Optional[AnalysisContext] = None
    ) -> ProcessedResult:
        """
        Execute a follow-up action with context preservation.
        
        Args:
            result: The result to act upon
            action: The action to execute
            context: Optional existing context
            
        Returns:
            New ProcessedResult from the action
        """
        # Create or update context
        if context is None:
            context = AnalysisContext(
                original_result_id=result.id,
                step_number=1
            )
        else:
            context.step_number += 1
        
        context.action_chain.append(action.action_type)
        context.parameters_history.append(action.parameters)
        
        # Execute the action
        handler = self.action_handlers.get(action.action_type)
        if handler:
            new_result = handler(result, action, context)
        else:
            raise ValueError(f"Unsupported action type: {action.action_type}")
        
        # Add context information to the new result
        new_result.metadata.tags.append(f"follow_up_from_{result.id}")
        new_result.metadata.tags.append(f"step_{context.step_number}")
        new_result.metadata.tags.append(f"action_chain_{len(context.action_chain)}")
        
        return new_result
    
    def _execute_summarize(
        self, 
        result: ProcessedResult, 
        action: Action, 
        context: AnalysisContext
    ) -> ProcessedResult:
        """Execute summarize action."""
        length = action.parameters.get('length', 'normal')
        
        if length == 'short':
            prompt = f"Erstelle eine kurze Zusammenfassung (max. 3 Sätze) des folgenden Textes:\n\n{result.content}"
        elif length == 'detailed':
            prompt = f"Erstelle eine detaillierte Zusammenfassung mit den wichtigsten Punkten:\n\n{result.content}"
        else:
            prompt = f"Fasse den folgenden Text zusammen:\n\n{result.content}"
        
        # Add context information
        if context.step_number > 1:
            prompt += f"\n\nHinweis: Dies ist Schritt {context.step_number} einer Analyse-Kette."
        
        raw_result = analysis.real_ai_analyse_fortext(prompt)
        
        return self._create_follow_up_result(
            raw_result, result, action, context, "summarization"
        )
    
    def _execute_deepen(
        self, 
        result: ProcessedResult, 
        action: Action, 
        context: AnalysisContext
    ) -> ProcessedResult:
        """Execute deepen analysis action."""
        focus_area = action.parameters.get('focus', 'allgemeine Vertiefung')
        
        prompt = f"Führe eine tiefergehende Analyse des folgenden Textes durch"
        if focus_area != 'allgemeine Vertiefung':
            prompt += f" mit Fokus auf {focus_area}"
        prompt += f":\n\n{result.content}"
        
        # Add context from previous steps
        if context.action_chain:
            previous_actions = ", ".join([action.value for action in context.action_chain[:-1]])
            prompt += f"\n\nVorherige Analyseschritte: {previous_actions}"
        
        raw_result = analysis.real_ai_analyse_fortext(prompt)
        
        return self._create_follow_up_result(
            raw_result, result, action, context, "deep_analysis"
        )
    
    def _execute_translate(
        self, 
        result: ProcessedResult, 
        action: Action, 
        context: AnalysisContext
    ) -> ProcessedResult:
        """Execute translation action."""
        target_language = action.parameters.get('target_language', 'English')
        style = action.parameters.get('style', 'formal')
        
        prompt = f"Übersetze den folgenden Text ins {target_language}"
        if style != 'formal':
            prompt += f" im {style} Stil"
        prompt += f":\n\n{result.content}"
        
        raw_result = analysis.real_ai_analyse_fortext(prompt)
        
        return self._create_follow_up_result(
            raw_result, result, action, context, "translation"
        )
    
    def _execute_analyze(
        self, 
        result: ProcessedResult, 
        action: Action, 
        context: AnalysisContext
    ) -> ProcessedResult:
        """Execute custom analysis action."""
        analysis_type = action.parameters.get('focus', 'allgemeine Analyse')
        custom_prompt = action.parameters.get('prompt', '')
        
        if custom_prompt:
            prompt = f"{custom_prompt}\n\n{result.content}"
        else:
            prompt = f"Führe eine {analysis_type} des folgenden Textes durch:\n\n{result.content}"
        
        raw_result = analysis.real_ai_analyse_fortext(prompt)
        
        return self._create_follow_up_result(
            raw_result, result, action, context, "custom_analysis"
        )
    
    def _execute_explain(
        self,
        result: ProcessedResult,
        action: Action,
        context: AnalysisContext
    ) -> ProcessedResult:
        """Execute explain-simply action."""
        audience = action.parameters.get('audience', 'Anfänger')

        prompt = (
            f"Erkläre den folgenden Text so einfach wie möglich für {audience}. "
            f"Vermeide Fachjargon oder erkläre unbekannte Begriffe kurz:\n\n{result.content}"
        )

        raw_result = analysis.real_ai_analyse_fortext(prompt)

        return self._create_follow_up_result(
            raw_result, result, action, context, "simple_explanation"
        )

    def _execute_export(
        self, 
        result: ProcessedResult, 
        action: Action, 
        context: AnalysisContext
    ) -> ProcessedResult:
        """Execute export action (placeholder - actual export handled by other components)."""
        export_format = action.parameters.get('format', 'excel')
        
        # This would typically trigger the actual export process
        # For now, we create a result indicating the export was requested
        export_summary = f"Export-Anfrage erstellt für Format: {export_format}"
        if result.has_exportable_data():
            tables_count = len(result.extracted_data.get_exportable_tables())
            export_summary += f"\nAnzahl exportierbarer Tabellen: {tables_count}"
        else:
            export_summary += "\nKeine strukturierten Daten zum Export verfügbar."
        
        return self._create_follow_up_result(
            export_summary, result, action, context, "export_request"
        )
    
    def _execute_visualize(
        self, 
        result: ProcessedResult, 
        action: Action, 
        context: AnalysisContext
    ) -> ProcessedResult:
        """Execute visualization action (placeholder - actual visualization handled by other components)."""
        chart_type = action.parameters.get('chart_type', 'auto')
        
        # This would typically trigger the actual visualization process
        viz_summary = f"Visualisierung angefordert (Typ: {chart_type})"
        if result.has_visualizable_data():
            numeric_count = len(result.extracted_data.numeric_values)
            viz_summary += f"\nAnzahl numerischer Werte: {numeric_count}"
        else:
            viz_summary += "\nKeine visualisierbaren Daten verfügbar."
        
        return self._create_follow_up_result(
            viz_summary, result, action, context, "visualization_request"
        )
    
    def _create_follow_up_result(
        self, 
        raw_result: str, 
        original_result: ProcessedResult, 
        action: Action, 
        context: AnalysisContext,
        analysis_type: str
    ) -> ProcessedResult:
        """Create a follow-up result with proper metadata."""
        from results_processor import ResultsProcessor
        
        # Create a temporary processor to handle the result processing
        processor = ResultsProcessor()
        
        # Determine source path
        source_path = "follow_up"
        if original_result.source_info:
            source_path = original_result.source_info.file_path or original_result.source_info.url or "follow_up"
        
        # Process the result
        follow_up_result = processor.process_analysis_result(
            raw_result=raw_result,
            source_path=source_path,
            analysis_type=f"follow_up_{analysis_type}",
            model_used=original_result.metadata.model_used or "gpt-4o"
        )
        
        return follow_up_result


class AnalysisHistoryManager:
    """
    Manager for analysis history and navigation.
    
    This class handles the storage, retrieval, and navigation of analysis
    steps and their relationships.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path) if storage_path else Path("analysis_history")
        self.storage_path.mkdir(exist_ok=True)
        
        self.current_session: List[AnalysisStep] = []
        self.step_relationships: Dict[str, List[str]] = {}  # parent_id -> [child_ids]
    
    def add_step(
        self, 
        result: ProcessedResult, 
        context: Optional[AnalysisContext] = None,
        parent_step_id: Optional[str] = None
    ) -> AnalysisStep:
        """
        Add a new analysis step to the history.
        
        Args:
            result: The analysis result
            context: Analysis context
            parent_step_id: ID of the parent step
            
        Returns:
            The created AnalysisStep
        """
        if context is None:
            context = AnalysisContext(
                original_result_id=result.id,
                step_number=1
            )
        
        step = AnalysisStep(
            result=result,
            context=context,
            parent_step_id=parent_step_id
        )
        
        self.current_session.append(step)
        
        # Update relationships
        if parent_step_id:
            if parent_step_id not in self.step_relationships:
                self.step_relationships[parent_step_id] = []
            self.step_relationships[parent_step_id].append(result.id)
        
        return step
    
    def get_step_by_id(self, step_id: str) -> Optional[AnalysisStep]:
        """Get a step by its result ID."""
        for step in self.current_session:
            if step.result.id == step_id:
                return step
        return None
    
    def get_analysis_chain(self, step_id: str) -> List[AnalysisStep]:
        """
        Get the complete analysis chain leading to a specific step.
        
        Args:
            step_id: The target step ID
            
        Returns:
            List of steps in chronological order
        """
        chain = []
        current_step = self.get_step_by_id(step_id)
        
        while current_step:
            chain.insert(0, current_step)
            if current_step.parent_step_id:
                current_step = self.get_step_by_id(current_step.parent_step_id)
            else:
                break
        
        return chain
    
    def get_child_steps(self, step_id: str) -> List[AnalysisStep]:
        """Get all direct child steps of a given step."""
        child_ids = self.step_relationships.get(step_id, [])
        return [step for step in self.current_session if step.result.id in child_ids]
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the current analysis session."""
        if not self.current_session:
            return {'total_steps': 0, 'analysis_chains': []}
        
        # Find root steps (steps without parents)
        root_steps = [step for step in self.current_session if step.parent_step_id is None]
        
        chains = []
        for root_step in root_steps:
            chain = self.get_analysis_chain(root_step.result.id)
            chains.append({
                'root_id': root_step.result.id,
                'length': len(chain),
                'actions': [step.context.action_chain for step in chain if step.context.action_chain],
                'created_at': root_step.context.created_at.isoformat()
            })
        
        return {
            'total_steps': len(self.current_session),
            'analysis_chains': chains,
            'session_start': min(step.context.created_at for step in self.current_session).isoformat() if self.current_session else None
        }
    
    def save_session(self, session_name: str) -> str:
        """
        Save the current session to disk.
        
        Args:
            session_name: Name for the saved session
            
        Returns:
            Path to the saved session file
        """
        session_data = {
            'session_name': session_name,
            'created_at': datetime.now().isoformat(),
            'steps': [step.to_dict() for step in self.current_session],
            'relationships': self.step_relationships,
            'summary': self.get_session_summary()
        }
        
        session_file = self.storage_path / f"{session_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        return str(session_file)
    
    def load_session(self, session_file: str):
        """
        Load a session from disk.
        
        Args:
            session_file: Path to the session file
        """
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        self.current_session = []
        self.step_relationships = session_data.get('relationships', {})
        
        for step_data in session_data['steps']:
            result = ProcessedResult.from_dict(step_data['result'])
            context = AnalysisContext.from_dict(step_data['context'])
            step = AnalysisStep(
                result=result,
                context=context,
                parent_step_id=step_data.get('parent_step_id')
            )
            self.current_session.append(step)
    
    def clear_session(self):
        """Clear the current session."""
        self.current_session.clear()
        self.step_relationships.clear()
    
    def navigate_to_step(self, step_id: str) -> Optional[ProcessedResult]:
        """
        Navigate to a specific step and return its result.
        
        Args:
            step_id: The step ID to navigate to
            
        Returns:
            The ProcessedResult of the step, or None if not found
        """
        step = self.get_step_by_id(step_id)
        return step.result if step else None


class FollowUpActionSystem:
    """
    Complete follow-up action system integrating execution and history management.
    
    This is the main interface for the follow-up action system.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.executor = FollowUpActionExecutor()
        self.history_manager = AnalysisHistoryManager(storage_path)
    
    def execute_follow_up_action(
        self, 
        result: ProcessedResult, 
        action: Action,
        parent_step_id: Optional[str] = None
    ) -> ProcessedResult:
        """
        Execute a follow-up action and track it in history.
        
        Args:
            result: The result to act upon
            action: The action to execute
            parent_step_id: Optional parent step ID for chaining
            
        Returns:
            New ProcessedResult from the action
        """
        # Get context from parent step if available
        context = None
        if parent_step_id:
            parent_step = self.history_manager.get_step_by_id(parent_step_id)
            if parent_step:
                context = parent_step.context
        
        # Execute the action
        new_result = self.executor.execute_action(result, action, context)
        
        # Add to history
        new_context = context or AnalysisContext(
            original_result_id=result.id,
            step_number=1
        )
        
        self.history_manager.add_step(
            result=new_result,
            context=new_context,
            parent_step_id=parent_step_id or result.id
        )
        
        return new_result
    
    def get_analysis_history(self) -> List[AnalysisStep]:
        """Get the current analysis history."""
        return self.history_manager.current_session.copy()
    
    def get_step_chain(self, step_id: str) -> List[AnalysisStep]:
        """Get the analysis chain for a specific step."""
        return self.history_manager.get_analysis_chain(step_id)
    
    def navigate_to_step(self, step_id: str) -> Optional[ProcessedResult]:
        """Navigate to a specific step in the history."""
        return self.history_manager.navigate_to_step(step_id)
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the current analysis session."""
        return self.history_manager.get_session_summary()
    
    def save_session(self, session_name: str) -> str:
        """Save the current analysis session."""
        return self.history_manager.save_session(session_name)
    
    def load_session(self, session_file: str):
        """Load an analysis session from file."""
        self.history_manager.load_session(session_file)
    
    def clear_history(self):
        """Clear the analysis history."""
        self.history_manager.clear_session()


# Factory function for creating the follow-up action system
def create_follow_up_system(storage_path: Optional[str] = None) -> FollowUpActionSystem:
    """
    Create a configured FollowUpActionSystem.
    
    Args:
        storage_path: Optional path for storing analysis history
        
    Returns:
        Configured FollowUpActionSystem
    """
    return FollowUpActionSystem(storage_path)