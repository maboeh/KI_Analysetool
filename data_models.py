"""
Core data models for enhanced results processing.

This module contains the fundamental data structures used throughout the
enhanced results processing system, including ProcessedResult, StructuredData,
and related entities.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from abc import ABC, abstractmethod
import uuid


# Enums for type safety
class ActionType(Enum):
    """Types of follow-up actions available for results."""
    SUMMARIZE = "zusammenfassen"
    DEEPEN = "vertiefen" 
    TRANSLATE = "übersetzen"
    ANALYZE = "analysieren"
    EXPORT = "exportieren"
    VISUALIZE = "visualisieren"


class ChartType(Enum):
    """Supported chart types for visualization."""
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    HISTOGRAM = "histogram"
    HEATMAP = "heatmap"


class EntityType(Enum):
    """Types of named entities that can be extracted."""
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    DATE = "date"
    MONEY = "money"
    PERCENTAGE = "percentage"
    QUANTITY = "quantity"


class DataType(Enum):
    """Types of structured data."""
    TABLE = "table"
    LIST = "list"
    NUMERIC = "numeric"
    TEMPORAL = "temporal"
    TEXT = "text"


# Base interfaces for extensibility
class Extractable(ABC):
    """Base interface for extractable data types."""
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        pass
    
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Extractable':
        """Create instance from dictionary."""
        pass


class Exportable(ABC):
    """Base interface for exportable data types."""
    
    @abstractmethod
    def to_excel_format(self) -> Dict[str, Any]:
        """Convert to Excel-compatible format."""
        pass
    
    @abstractmethod
    def to_csv_format(self) -> str:
        """Convert to CSV format."""
        pass


# Core data model classes
@dataclass
class SourceInfo:
    """Information about the source of analyzed content."""
    type: str  # "youtube", "website", "pdf", "excel", "image", "csv"
    url: Optional[str] = None
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    encoding: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.type,
            'url': self.url,
            'file_path': self.file_path,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'encoding': self.encoding
        }


@dataclass
class NamedEntity(Extractable):
    """A named entity extracted from text."""
    text: str
    entity_type: EntityType
    confidence: float
    start_pos: Optional[int] = None
    end_pos: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'text': self.text,
            'entity_type': self.entity_type.value,
            'confidence': self.confidence,
            'start_pos': self.start_pos,
            'end_pos': self.end_pos
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NamedEntity':
        return cls(
            text=data['text'],
            entity_type=EntityType(data['entity_type']),
            confidence=data['confidence'],
            start_pos=data.get('start_pos'),
            end_pos=data.get('end_pos')
        )


@dataclass
class NumericValue(Extractable):
    """A numeric value extracted from text."""
    value: Union[int, float]
    unit: Optional[str] = None
    context: Optional[str] = None
    value_type: Optional[str] = None  # "currency", "percentage", "quantity", etc.
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'value': self.value,
            'unit': self.unit,
            'context': self.context,
            'value_type': self.value_type
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NumericValue':
        return cls(
            value=data['value'],
            unit=data.get('unit'),
            context=data.get('context'),
            value_type=data.get('value_type')
        )


@dataclass
class TemporalValue(Extractable):
    """A temporal value (date/time) extracted from text."""
    value: datetime
    original_text: str
    precision: str  # "year", "month", "day", "hour", "minute"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'value': self.value.isoformat(),
            'original_text': self.original_text,
            'precision': self.precision
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TemporalValue':
        return cls(
            value=datetime.fromisoformat(data['value']),
            original_text=data['original_text'],
            precision=data['precision']
        )


@dataclass
class DataTable(Extractable, Exportable):
    """A table extracted from content."""
    headers: List[str]
    rows: List[List[str]]
    title: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'headers': self.headers,
            'rows': self.rows,
            'title': self.title
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataTable':
        return cls(
            headers=data['headers'],
            rows=data['rows'],
            title=data.get('title')
        )
    
    def to_excel_format(self) -> Dict[str, Any]:
        """Convert table to Excel-compatible format."""
        return {
            'sheet_name': self.title or 'Table',
            'headers': self.headers,
            'data': self.rows
        }
    
    def to_csv_format(self) -> str:
        """Convert table to CSV format."""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(self.headers)
        writer.writerows(self.rows)
        return output.getvalue()


@dataclass
class DataRelationship:
    """Represents a relationship between data elements."""
    source: str
    target: str
    relationship_type: str
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source': self.source,
            'target': self.target,
            'relationship_type': self.relationship_type,
            'confidence': self.confidence
        }


@dataclass
class StructuredData:
    """Container for all structured data extracted from content."""
    tables: List[DataTable] = field(default_factory=list)
    entities: List[NamedEntity] = field(default_factory=list)
    numeric_values: List[NumericValue] = field(default_factory=list)
    temporal_data: List[TemporalValue] = field(default_factory=list)
    relationships: List[DataRelationship] = field(default_factory=list)
    categories: Dict[str, List[str]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'tables': [table.to_dict() for table in self.tables],
            'entities': [entity.to_dict() for entity in self.entities],
            'numeric_values': [num.to_dict() for num in self.numeric_values],
            'temporal_data': [temp.to_dict() for temp in self.temporal_data],
            'relationships': [rel.to_dict() for rel in self.relationships],
            'categories': self.categories
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StructuredData':
        return cls(
            tables=[DataTable.from_dict(t) for t in data.get('tables', [])],
            entities=[NamedEntity.from_dict(e) for e in data.get('entities', [])],
            numeric_values=[NumericValue.from_dict(n) for n in data.get('numeric_values', [])],
            temporal_data=[TemporalValue.from_dict(t) for t in data.get('temporal_data', [])],
            relationships=[DataRelationship(**r) for r in data.get('relationships', [])],
            categories=data.get('categories', {})
        )
    
    def has_visualizable_data(self) -> bool:
        """Check if the structured data contains data suitable for visualization."""
        return len(self.numeric_values) > 0 or len(self.tables) > 0
    
    def get_exportable_tables(self) -> List[DataTable]:
        """Get all tables that can be exported to Excel."""
        return self.tables


@dataclass
class ChartConfig:
    """Configuration for chart generation."""
    title: Optional[str] = None
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    colors: Optional[List[str]] = None
    style: Optional[str] = None
    size: tuple = (10, 6)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'x_label': self.x_label,
            'y_label': self.y_label,
            'colors': self.colors,
            'style': self.style,
            'size': self.size
        }


@dataclass
class Visualization:
    """Represents a generated visualization."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    chart_type: ChartType = ChartType.BAR
    data_source: str = ""
    config: ChartConfig = field(default_factory=ChartConfig)
    file_path: Optional[str] = None
    interactive: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'chart_type': self.chart_type.value,
            'data_source': self.data_source,
            'config': self.config.to_dict(),
            'file_path': self.file_path,
            'interactive': self.interactive
        }


@dataclass
class Action:
    """Represents a follow-up action that can be performed on results."""
    action_type: ActionType
    label: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'action_type': self.action_type.value,
            'label': self.label,
            'description': self.description,
            'parameters': self.parameters,
            'enabled': self.enabled
        }


@dataclass
class ResultMetadata:
    """Metadata for processed results."""
    analysis_type: str
    processing_time: Optional[float] = None
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None
    confidence_score: Optional[float] = None
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'analysis_type': self.analysis_type,
            'processing_time': self.processing_time,
            'model_used': self.model_used,
            'tokens_used': self.tokens_used,
            'confidence_score': self.confidence_score,
            'tags': self.tags
        }


@dataclass
class ProcessedResult:
    """Main container for processed analysis results."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    source_info: Optional[SourceInfo] = None
    extracted_data: StructuredData = field(default_factory=StructuredData)
    visualizations: List[Visualization] = field(default_factory=list)
    follow_up_actions: List[Action] = field(default_factory=list)
    metadata: ResultMetadata = field(default_factory=lambda: ResultMetadata(analysis_type="unknown"))
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'content': self.content,
            'source_info': self.source_info.to_dict() if self.source_info else None,
            'extracted_data': self.extracted_data.to_dict(),
            'visualizations': [viz.to_dict() for viz in self.visualizations],
            'follow_up_actions': [action.to_dict() for action in self.follow_up_actions],
            'metadata': self.metadata.to_dict(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessedResult':
        return cls(
            id=data['id'],
            content=data['content'],
            source_info=SourceInfo(**data['source_info']) if data.get('source_info') else None,
            extracted_data=StructuredData.from_dict(data.get('extracted_data', {})),
            visualizations=[Visualization(**viz) for viz in data.get('visualizations', [])],
            follow_up_actions=[Action(**action) for action in data.get('follow_up_actions', [])],
            metadata=ResultMetadata(**data.get('metadata', {})),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at'])
        )
    
    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now()
    
    def add_visualization(self, visualization: Visualization):
        """Add a visualization to the result."""
        self.visualizations.append(visualization)
        self.update_timestamp()
    
    def add_follow_up_action(self, action: Action):
        """Add a follow-up action to the result."""
        self.follow_up_actions.append(action)
        self.update_timestamp()
    
    def has_exportable_data(self) -> bool:
        """Check if the result contains data that can be exported."""
        return len(self.extracted_data.get_exportable_tables()) > 0
    
    def has_visualizable_data(self) -> bool:
        """Check if the result contains data suitable for visualization."""
        return self.extracted_data.has_visualizable_data()


# Utility classes for result summaries and filtering
@dataclass
class ResultSummary:
    """Summary information for result listings."""
    id: str
    title: str
    analysis_type: str
    source_type: str
    created_at: datetime
    has_visualizations: bool
    has_exportable_data: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'analysis_type': self.analysis_type,
            'source_type': self.source_type,
            'created_at': self.created_at.isoformat(),
            'has_visualizations': self.has_visualizations,
            'has_exportable_data': self.has_exportable_data
        }


@dataclass
class ExtractedContent:
    """Container for content extracted from files."""
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    structured_data: Optional[StructuredData] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'text': self.text,
            'metadata': self.metadata,
            'structured_data': self.structured_data.to_dict() if self.structured_data else None
        }


# Factory functions for creating common data structures
def create_default_actions() -> List[Action]:
    """Create default follow-up actions for results."""
    return [
        Action(
            action_type=ActionType.SUMMARIZE,
            label="Zusammenfassen",
            description="Erstelle eine Zusammenfassung des Ergebnisses"
        ),
        Action(
            action_type=ActionType.DEEPEN,
            label="Vertiefen",
            description="Führe eine tiefergehende Analyse durch"
        ),
        Action(
            action_type=ActionType.TRANSLATE,
            label="Übersetzen",
            description="Übersetze das Ergebnis in eine andere Sprache"
        )
    ]


def create_source_info_from_path(path: str) -> SourceInfo:
    """Create SourceInfo from a file path or URL."""
    import os
    
    if path.startswith(('http://', 'https://')):
        if 'youtu' in path.lower():
            return SourceInfo(type="youtube", url=path)
        else:
            return SourceInfo(type="website", url=path)
    else:
        file_name = os.path.basename(path)
        file_size = os.path.getsize(path) if os.path.exists(path) else None
        
        if path.lower().endswith('.pdf'):
            return SourceInfo(type="pdf", file_path=path, file_name=file_name, file_size=file_size)
        elif path.lower().endswith(('.xlsx', '.xls')):
            return SourceInfo(type="excel", file_path=path, file_name=file_name, file_size=file_size)
        elif path.lower().endswith('.csv'):
            return SourceInfo(type="csv", file_path=path, file_name=file_name, file_size=file_size)
        elif path.lower().endswith(('.png', '.jpg', '.jpeg')):
            return SourceInfo(type="image", file_path=path, file_name=file_name, file_size=file_size)
        else:
            return SourceInfo(type="text", file_path=path, file_name=file_name, file_size=file_size)