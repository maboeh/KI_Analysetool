"""
Data categorization and filtering system for structured data.

This module provides advanced categorization, filtering, and sorting mechanisms
for extracted structured data, including automatic data type classification
and data validation/cleaning functions.
"""

from typing import List, Dict, Any, Optional, Callable, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
from datetime import datetime, timedelta
from data_models import (
    StructuredData, DataTable, NamedEntity, NumericValue, TemporalValue,
    EntityType, DataRelationship
)


class CategoryType(Enum):
    """Types of data categories."""
    FINANCIAL = "financial"
    TEMPORAL = "temporal"
    GEOGRAPHICAL = "geographical"
    PERSONAL = "personal"
    ORGANIZATIONAL = "organizational"
    QUANTITATIVE = "quantitative"
    QUALITATIVE = "qualitative"
    TECHNICAL = "technical"


class FilterOperator(Enum):
    """Filter operators for data filtering."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IN_RANGE = "in_range"
    REGEX_MATCH = "regex_match"


class SortOrder(Enum):
    """Sort order options."""
    ASCENDING = "asc"
    DESCENDING = "desc"


@dataclass
class FilterCriteria:
    """Criteria for filtering data."""
    field: str
    operator: FilterOperator
    value: Any
    case_sensitive: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'field': self.field,
            'operator': self.operator.value,
            'value': self.value,
            'case_sensitive': self.case_sensitive
        }


@dataclass
class SortCriteria:
    """Criteria for sorting data."""
    field: str
    order: SortOrder = SortOrder.ASCENDING
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'field': self.field,
            'order': self.order.value
        }


@dataclass
class CategoryRule:
    """Rule for automatic categorization."""
    category: CategoryType
    condition: Callable[[Any], bool]
    priority: int = 0
    description: str = ""


@dataclass
class DataQualityMetrics:
    """Metrics for data quality assessment."""
    completeness_score: float  # 0-1, percentage of non-empty values
    consistency_score: float   # 0-1, consistency of data formats
    accuracy_score: float      # 0-1, estimated accuracy based on patterns
    uniqueness_score: float    # 0-1, percentage of unique values
    validity_score: float      # 0-1, percentage of valid values
    overall_score: float       # 0-1, weighted average of all scores
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'completeness_score': self.completeness_score,
            'consistency_score': self.consistency_score,
            'accuracy_score': self.accuracy_score,
            'uniqueness_score': self.uniqueness_score,
            'validity_score': self.validity_score,
            'overall_score': self.overall_score
        }


class DataCategorizer:
    """
    Advanced data categorization and filtering system.
    
    Provides automatic data type classification, filtering, sorting,
    and data quality assessment for structured data.
    """
    
    def __init__(self):
        self._init_category_rules()
        self._init_validation_patterns()
    
    def _init_category_rules(self):
        """Initialize categorization rules."""
        self.category_rules = [
            # Financial data
            CategoryRule(
                CategoryType.FINANCIAL,
                lambda x: self._is_financial_data(x),
                priority=10,
                description="Financial data including currency, prices, costs"
            ),
            
            # Temporal data
            CategoryRule(
                CategoryType.TEMPORAL,
                lambda x: self._is_temporal_data(x),
                priority=9,
                description="Temporal data including dates, times, durations"
            ),
            
            # Geographical data
            CategoryRule(
                CategoryType.GEOGRAPHICAL,
                lambda x: self._is_geographical_data(x),
                priority=8,
                description="Geographical data including locations, addresses"
            ),
            
            # Personal data
            CategoryRule(
                CategoryType.PERSONAL,
                lambda x: self._is_personal_data(x),
                priority=7,
                description="Personal data including names, contacts"
            ),
            
            # Organizational data
            CategoryRule(
                CategoryType.ORGANIZATIONAL,
                lambda x: self._is_organizational_data(x),
                priority=6,
                description="Organizational data including companies, institutions"
            ),
            
            # Quantitative data
            CategoryRule(
                CategoryType.QUANTITATIVE,
                lambda x: self._is_quantitative_data(x),
                priority=5,
                description="Quantitative data including measurements, counts"
            ),
        ]
    
    def _init_validation_patterns(self):
        """Initialize validation patterns for different data types."""
        self.validation_patterns = {
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'phone': r'^[\+]?[1-9][\d]{0,15}$',
            'url': r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$',
            'postal_code': r'^\d{5}(-\d{4})?$',
            'german_postal_code': r'^\d{5}$',
            'iban': r'^[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}([A-Z0-9]?){0,16}$',
        }
    
    def categorize_structured_data(self, structured_data: StructuredData) -> Dict[CategoryType, List[Any]]:
        """
        Automatically categorize all data in StructuredData.
        
        Args:
            structured_data: The structured data to categorize
            
        Returns:
            Dictionary mapping category types to lists of categorized items
        """
        categories = {cat_type: [] for cat_type in CategoryType}
        
        # Categorize entities
        for entity in structured_data.entities:
            category = self._categorize_entity(entity)
            if category:
                categories[category].append(entity)
        
        # Categorize numeric values
        for numeric in structured_data.numeric_values:
            category = self._categorize_numeric_value(numeric)
            if category:
                categories[category].append(numeric)
        
        # Categorize temporal data
        for temporal in structured_data.temporal_data:
            categories[CategoryType.TEMPORAL].append(temporal)
        
        # Categorize tables
        for table in structured_data.tables:
            table_categories = self._categorize_table(table)
            for category, items in table_categories.items():
                categories[category].extend(items)
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}
    
    def _categorize_entity(self, entity: NamedEntity) -> Optional[CategoryType]:
        """Categorize a named entity."""
        if entity.entity_type == EntityType.PERSON:
            return CategoryType.PERSONAL
        elif entity.entity_type == EntityType.ORGANIZATION:
            return CategoryType.ORGANIZATIONAL
        elif entity.entity_type == EntityType.LOCATION:
            return CategoryType.GEOGRAPHICAL
        elif entity.entity_type == EntityType.MONEY:
            return CategoryType.FINANCIAL
        elif entity.entity_type == EntityType.DATE:
            return CategoryType.TEMPORAL
        
        return None
    
    def _categorize_numeric_value(self, numeric: NumericValue) -> Optional[CategoryType]:
        """Categorize a numeric value."""
        if numeric.value_type in ['currency', 'money']:
            return CategoryType.FINANCIAL
        elif numeric.value_type in ['percentage']:
            return CategoryType.QUANTITATIVE
        elif numeric.value_type in ['quantity', 'measurement']:
            return CategoryType.QUANTITATIVE
        
        return CategoryType.QUANTITATIVE  # Default for numeric data
    
    def _categorize_table(self, table: DataTable) -> Dict[CategoryType, List[Any]]:
        """Categorize table data by analyzing headers and content."""
        categories = {cat_type: [] for cat_type in CategoryType}
        
        # Analyze headers for category hints
        financial_headers = ['price', 'cost', 'amount', 'revenue', 'profit', 'budget', 'salary', 'wage']
        temporal_headers = ['date', 'time', 'year', 'month', 'day', 'created', 'updated', 'deadline']
        geographical_headers = ['location', 'address', 'city', 'country', 'region', 'zip', 'postal']
        personal_headers = ['name', 'firstname', 'lastname', 'email', 'phone', 'contact']
        organizational_headers = ['company', 'organization', 'department', 'team', 'division']
        
        for i, header in enumerate(table.headers):
            header_lower = header.lower()
            
            # Determine category based on header
            category = None
            if any(fh in header_lower for fh in financial_headers):
                category = CategoryType.FINANCIAL
            elif any(th in header_lower for th in temporal_headers):
                category = CategoryType.TEMPORAL
            elif any(gh in header_lower for gh in geographical_headers):
                category = CategoryType.GEOGRAPHICAL
            elif any(ph in header_lower for ph in personal_headers):
                category = CategoryType.PERSONAL
            elif any(oh in header_lower for oh in organizational_headers):
                category = CategoryType.ORGANIZATIONAL
            
            if category:
                # Add column data to category
                column_data = [row[i] if i < len(row) else '' for row in table.rows]
                categories[category].extend(column_data)
        
        return categories
    
    def _is_financial_data(self, data: Any) -> bool:
        """Check if data is financial."""
        if isinstance(data, NumericValue):
            return data.value_type in ['currency', 'money'] or (data.unit and data.unit in ['EUR', 'USD', '€', '$'])
        elif isinstance(data, str):
            return bool(re.search(r'[€$£¥]|\b(EUR|USD|GBP|JPY)\b', data))
        return False
    
    def _is_temporal_data(self, data: Any) -> bool:
        """Check if data is temporal."""
        if isinstance(data, TemporalValue):
            return True
        elif isinstance(data, str):
            # Check for date patterns
            date_patterns = [
                r'\d{1,2}[./]\d{1,2}[./]\d{4}',
                r'\d{4}-\d{1,2}-\d{1,2}',
                r'\b\d{1,2}\.\s*(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s*\d{4}\b'
            ]
            return any(re.search(pattern, data) for pattern in date_patterns)
        return False
    
    def _is_geographical_data(self, data: Any) -> bool:
        """Check if data is geographical."""
        if isinstance(data, NamedEntity):
            return data.entity_type == EntityType.LOCATION
        elif isinstance(data, str):
            # Check for geographical indicators
            geo_patterns = [
                r'\b\d{5}\b',  # Postal codes
                r'\b(Straße|Str\.|Avenue|Ave\.|Road|Rd\.)\b',  # Street indicators
                r'\b(Berlin|München|Hamburg|Köln|Frankfurt|Stuttgart|Düsseldorf|Dortmund)\b'  # Major cities
            ]
            return any(re.search(pattern, data, re.IGNORECASE) for pattern in geo_patterns)
        return False
    
    def _is_personal_data(self, data: Any) -> bool:
        """Check if data is personal."""
        if isinstance(data, NamedEntity):
            return data.entity_type == EntityType.PERSON
        elif isinstance(data, str):
            # Check for personal data patterns
            personal_patterns = [
                r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',  # Email
                r'^\+?[\d\s\-\(\)]{7,15}$',  # Phone
                r'^(Herr|Frau|Dr\.|Prof\.)\s+[A-ZÄÖÜ][a-zäöüß]+',  # Titles with names
            ]
            return any(re.search(pattern, data) for pattern in personal_patterns)
        return False
    
    def _is_organizational_data(self, data: Any) -> bool:
        """Check if data is organizational."""
        if isinstance(data, NamedEntity):
            return data.entity_type == EntityType.ORGANIZATION
        elif isinstance(data, str):
            # Check for organizational indicators
            org_patterns = [
                r'(GmbH|AG|e\.V\.|Inc\.|Corp\.|Ltd\.)',
                r'(Universität|University|Institut|Institute)',
                r'(Abteilung|Department|Team|Division)'
            ]
            return any(re.search(pattern, data, re.IGNORECASE) for pattern in org_patterns)
        return False
    
    def _is_quantitative_data(self, data: Any) -> bool:
        """Check if data is quantitative."""
        if isinstance(data, NumericValue):
            return True
        elif isinstance(data, str):
            # Check for numeric patterns
            return bool(re.search(r'\d+([.,]\d+)?', data))
        return False
    
    def filter_data(self, data: List[Any], criteria: List[FilterCriteria]) -> List[Any]:
        """
        Filter data based on multiple criteria.
        
        Args:
            data: List of data items to filter
            criteria: List of filter criteria to apply
            
        Returns:
            Filtered list of data items
        """
        filtered_data = data.copy()
        
        for criterion in criteria:
            filtered_data = self._apply_filter_criterion(filtered_data, criterion)
        
        return filtered_data
    
    def _apply_filter_criterion(self, data: List[Any], criterion: FilterCriteria) -> List[Any]:
        """Apply a single filter criterion to data."""
        filtered = []
        
        for item in data:
            if self._matches_criterion(item, criterion):
                filtered.append(item)
        
        return filtered
    
    def _matches_criterion(self, item: Any, criterion: FilterCriteria) -> bool:
        """Check if an item matches a filter criterion."""
        # Get field value from item
        field_value = self._get_field_value(item, criterion.field)
        
        if field_value is None:
            return False
        
        # Apply operator
        if criterion.operator == FilterOperator.EQUALS:
            return self._compare_values(field_value, criterion.value, criterion.case_sensitive) == 0
        elif criterion.operator == FilterOperator.NOT_EQUALS:
            return self._compare_values(field_value, criterion.value, criterion.case_sensitive) != 0
        elif criterion.operator == FilterOperator.GREATER_THAN:
            return self._compare_numeric(field_value, criterion.value) > 0
        elif criterion.operator == FilterOperator.LESS_THAN:
            return self._compare_numeric(field_value, criterion.value) < 0
        elif criterion.operator == FilterOperator.GREATER_EQUAL:
            return self._compare_numeric(field_value, criterion.value) >= 0
        elif criterion.operator == FilterOperator.LESS_EQUAL:
            return self._compare_numeric(field_value, criterion.value) <= 0
        elif criterion.operator == FilterOperator.CONTAINS:
            return self._string_contains(field_value, criterion.value, criterion.case_sensitive)
        elif criterion.operator == FilterOperator.NOT_CONTAINS:
            return not self._string_contains(field_value, criterion.value, criterion.case_sensitive)
        elif criterion.operator == FilterOperator.STARTS_WITH:
            return self._string_starts_with(field_value, criterion.value, criterion.case_sensitive)
        elif criterion.operator == FilterOperator.ENDS_WITH:
            return self._string_ends_with(field_value, criterion.value, criterion.case_sensitive)
        elif criterion.operator == FilterOperator.IN_RANGE:
            return self._in_range(field_value, criterion.value)
        elif criterion.operator == FilterOperator.REGEX_MATCH:
            return self._regex_match(field_value, criterion.value, criterion.case_sensitive)
        
        return False
    
    def _get_field_value(self, item: Any, field: str) -> Any:
        """Get field value from an item."""
        if hasattr(item, field):
            return getattr(item, field)
        elif isinstance(item, dict) and field in item:
            return item[field]
        elif hasattr(item, 'to_dict'):
            item_dict = item.to_dict()
            return item_dict.get(field)
        
        return None
    
    def _compare_values(self, value1: Any, value2: Any, case_sensitive: bool = True) -> int:
        """Compare two values, returning -1, 0, or 1."""
        if isinstance(value1, str) and isinstance(value2, str):
            if not case_sensitive:
                value1, value2 = value1.lower(), value2.lower()
            return (value1 > value2) - (value1 < value2)
        elif isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
            return (value1 > value2) - (value1 < value2)
        else:
            return (str(value1) > str(value2)) - (str(value1) < str(value2))
    
    def _compare_numeric(self, value1: Any, value2: Any) -> int:
        """Compare numeric values."""
        try:
            num1 = float(value1) if not isinstance(value1, (int, float)) else value1
            num2 = float(value2) if not isinstance(value2, (int, float)) else value2
            return (num1 > num2) - (num1 < num2)
        except (ValueError, TypeError):
            return 0
    
    def _string_contains(self, text: Any, substring: str, case_sensitive: bool = True) -> bool:
        """Check if text contains substring."""
        text_str = str(text)
        if not case_sensitive:
            text_str, substring = text_str.lower(), substring.lower()
        return substring in text_str
    
    def _string_starts_with(self, text: Any, prefix: str, case_sensitive: bool = True) -> bool:
        """Check if text starts with prefix."""
        text_str = str(text)
        if not case_sensitive:
            text_str, prefix = text_str.lower(), prefix.lower()
        return text_str.startswith(prefix)
    
    def _string_ends_with(self, text: Any, suffix: str, case_sensitive: bool = True) -> bool:
        """Check if text ends with suffix."""
        text_str = str(text)
        if not case_sensitive:
            text_str, suffix = text_str.lower(), suffix.lower()
        return text_str.endswith(suffix)
    
    def _in_range(self, value: Any, range_values: Tuple[Any, Any]) -> bool:
        """Check if value is in range."""
        try:
            num_value = float(value) if not isinstance(value, (int, float)) else value
            min_val, max_val = range_values
            return min_val <= num_value <= max_val
        except (ValueError, TypeError):
            return False
    
    def _regex_match(self, text: Any, pattern: str, case_sensitive: bool = True) -> bool:
        """Check if text matches regex pattern."""
        flags = 0 if case_sensitive else re.IGNORECASE
        return bool(re.search(pattern, str(text), flags))
    
    def sort_data(self, data: List[Any], criteria: List[SortCriteria]) -> List[Any]:
        """
        Sort data based on multiple criteria.
        
        Args:
            data: List of data items to sort
            criteria: List of sort criteria to apply (in order of priority)
            
        Returns:
            Sorted list of data items
        """
        sorted_data = data.copy()
        
        # Apply sort criteria in reverse order (last criterion has highest priority)
        for criterion in reversed(criteria):
            sorted_data = self._apply_sort_criterion(sorted_data, criterion)
        
        return sorted_data
    
    def _apply_sort_criterion(self, data: List[Any], criterion: SortCriteria) -> List[Any]:
        """Apply a single sort criterion to data."""
        def sort_key(item):
            value = self._get_field_value(item, criterion.field)
            # Handle None values by putting them at the end
            if value is None:
                return (1, '')
            # Convert to comparable type
            if isinstance(value, str):
                return (0, value.lower())
            elif isinstance(value, (int, float)):
                return (0, value)
            elif isinstance(value, datetime):
                return (0, value)
            else:
                return (0, str(value).lower())
        
        reverse = criterion.order == SortOrder.DESCENDING
        return sorted(data, key=sort_key, reverse=reverse)
    
    def assess_data_quality(self, structured_data: StructuredData) -> DataQualityMetrics:
        """
        Assess the quality of structured data.
        
        Args:
            structured_data: The structured data to assess
            
        Returns:
            DataQualityMetrics object with quality scores
        """
        all_items = []
        
        # Collect all data items
        all_items.extend(structured_data.entities)
        all_items.extend(structured_data.numeric_values)
        all_items.extend(structured_data.temporal_data)
        
        # Add table data
        for table in structured_data.tables:
            for row in table.rows:
                all_items.extend(row)
        
        if not all_items:
            return DataQualityMetrics(0, 0, 0, 0, 0, 0)
        
        # Calculate completeness (non-empty values)
        non_empty_count = sum(1 for item in all_items if self._is_non_empty(item))
        completeness_score = non_empty_count / len(all_items)
        
        # Calculate consistency (format consistency)
        consistency_score = self._calculate_consistency_score(structured_data)
        
        # Calculate accuracy (pattern matching)
        accuracy_score = self._calculate_accuracy_score(structured_data)
        
        # Calculate uniqueness
        unique_items = set(str(item) for item in all_items)
        uniqueness_score = len(unique_items) / len(all_items) if all_items else 0
        
        # Calculate validity (valid formats)
        validity_score = self._calculate_validity_score(structured_data)
        
        # Calculate overall score (weighted average)
        weights = {
            'completeness': 0.25,
            'consistency': 0.20,
            'accuracy': 0.20,
            'uniqueness': 0.15,
            'validity': 0.20
        }
        
        overall_score = (
            completeness_score * weights['completeness'] +
            consistency_score * weights['consistency'] +
            accuracy_score * weights['accuracy'] +
            uniqueness_score * weights['uniqueness'] +
            validity_score * weights['validity']
        )
        
        return DataQualityMetrics(
            completeness_score=completeness_score,
            consistency_score=consistency_score,
            accuracy_score=accuracy_score,
            uniqueness_score=uniqueness_score,
            validity_score=validity_score,
            overall_score=overall_score
        )
    
    def _is_non_empty(self, item: Any) -> bool:
        """Check if an item is non-empty."""
        if item is None:
            return False
        elif isinstance(item, str):
            return bool(item.strip())
        elif isinstance(item, (list, dict)):
            return len(item) > 0
        else:
            return True
    
    def _calculate_consistency_score(self, structured_data: StructuredData) -> float:
        """Calculate consistency score based on format patterns."""
        # Check consistency of numeric values
        numeric_consistency = self._check_numeric_consistency(structured_data.numeric_values)
        
        # Check consistency of temporal values
        temporal_consistency = self._check_temporal_consistency(structured_data.temporal_data)
        
        # Check consistency of entity formats
        entity_consistency = self._check_entity_consistency(structured_data.entities)
        
        # Average consistency scores
        scores = [numeric_consistency, temporal_consistency, entity_consistency]
        return sum(scores) / len(scores) if scores else 0
    
    def _check_numeric_consistency(self, numeric_values: List[NumericValue]) -> float:
        """Check consistency of numeric value formats."""
        if not numeric_values:
            return 1.0
        
        # Group by value type
        type_groups = {}
        for nv in numeric_values:
            value_type = nv.value_type or 'unknown'
            if value_type not in type_groups:
                type_groups[value_type] = []
            type_groups[value_type].append(nv)
        
        # Check consistency within each type
        consistency_scores = []
        for group in type_groups.values():
            if len(group) <= 1:
                consistency_scores.append(1.0)
                continue
            
            # Check unit consistency
            units = [nv.unit for nv in group if nv.unit]
            if units:
                unit_consistency = len(set(units)) / len(units)
                consistency_scores.append(1.0 - unit_consistency + (1.0 / len(units)))
            else:
                consistency_scores.append(1.0)
        
        return sum(consistency_scores) / len(consistency_scores) if consistency_scores else 1.0
    
    def _check_temporal_consistency(self, temporal_values: List[TemporalValue]) -> float:
        """Check consistency of temporal value formats."""
        if not temporal_values:
            return 1.0
        
        # Check precision consistency
        precisions = [tv.precision for tv in temporal_values]
        unique_precisions = set(precisions)
        
        # More consistent if fewer different precisions
        consistency = 1.0 - (len(unique_precisions) - 1) / max(len(precisions), 1)
        return max(0.0, consistency)
    
    def _check_entity_consistency(self, entities: List[NamedEntity]) -> float:
        """Check consistency of entity formats."""
        if not entities:
            return 1.0
        
        # Group by entity type
        type_groups = {}
        for entity in entities:
            entity_type = entity.entity_type
            if entity_type not in type_groups:
                type_groups[entity_type] = []
            type_groups[entity_type].append(entity)
        
        # Check format consistency within each type
        consistency_scores = []
        for group in type_groups.values():
            if len(group) <= 1:
                consistency_scores.append(1.0)
                continue
            
            # Check text format patterns
            texts = [entity.text for entity in group]
            format_patterns = set()
            
            for text in texts:
                # Simple pattern classification
                if re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+$', text):
                    format_patterns.add('FirstName LastName')
                elif re.match(r'^(Dr\.|Prof\.|Herr|Frau)', text):
                    format_patterns.add('Title Name')
                else:
                    format_patterns.add('Other')
            
            # More consistent if fewer different patterns
            pattern_consistency = 1.0 - (len(format_patterns) - 1) / max(len(texts), 1)
            consistency_scores.append(max(0.0, pattern_consistency))
        
        return sum(consistency_scores) / len(consistency_scores) if consistency_scores else 1.0
    
    def _calculate_accuracy_score(self, structured_data: StructuredData) -> float:
        """Calculate accuracy score based on pattern matching confidence."""
        all_confidence_scores = []
        
        # Collect confidence scores from entities
        for entity in structured_data.entities:
            all_confidence_scores.append(entity.confidence)
        
        # Estimate confidence for numeric values based on context
        for numeric in structured_data.numeric_values:
            # Higher confidence if has unit and context
            confidence = 0.5  # Base confidence
            if numeric.unit:
                confidence += 0.2
            if numeric.context:
                confidence += 0.2
            if numeric.value_type:
                confidence += 0.1
            all_confidence_scores.append(min(1.0, confidence))
        
        # Estimate confidence for temporal values
        for temporal in structured_data.temporal_data:
            # Higher confidence for more precise dates
            confidence = 0.6  # Base confidence
            if temporal.precision in ['day', 'minute']:
                confidence += 0.3
            elif temporal.precision in ['month']:
                confidence += 0.2
            all_confidence_scores.append(min(1.0, confidence))
        
        return sum(all_confidence_scores) / len(all_confidence_scores) if all_confidence_scores else 0.5
    
    def _calculate_validity_score(self, structured_data: StructuredData) -> float:
        """Calculate validity score based on format validation."""
        valid_count = 0
        total_count = 0
        
        # Validate entities
        for entity in structured_data.entities:
            total_count += 1
            if self._validate_entity_format(entity):
                valid_count += 1
        
        # Validate numeric values
        for numeric in structured_data.numeric_values:
            total_count += 1
            if self._validate_numeric_format(numeric):
                valid_count += 1
        
        # Validate temporal values
        for temporal in structured_data.temporal_data:
            total_count += 1
            if self._validate_temporal_format(temporal):
                valid_count += 1
        
        return valid_count / total_count if total_count > 0 else 1.0
    
    def _validate_entity_format(self, entity: NamedEntity) -> bool:
        """Validate entity format."""
        text = entity.text
        
        if entity.entity_type == EntityType.PERSON:
            # Check for reasonable person name format
            return bool(re.match(r'^[A-ZÄÖÜ][a-zäöüß\s\-\.]+$', text)) and len(text) >= 2
        elif entity.entity_type == EntityType.ORGANIZATION:
            # Check for reasonable organization name format
            return len(text) >= 2 and not text.isdigit()
        elif entity.entity_type == EntityType.LOCATION:
            # Check for reasonable location name format
            return len(text) >= 2 and not text.isdigit()
        
        return True  # Default to valid for other types
    
    def _validate_numeric_format(self, numeric: NumericValue) -> bool:
        """Validate numeric value format."""
        # Check if value is reasonable
        if not isinstance(numeric.value, (int, float)):
            return False
        
        # Check for reasonable ranges based on type
        if numeric.value_type == 'percentage':
            return 0 <= numeric.value <= 100
        elif numeric.value_type == 'currency':
            return numeric.value >= 0  # Negative currency could be valid (debt)
        
        return True  # Default to valid
    
    def _validate_temporal_format(self, temporal: TemporalValue) -> bool:
        """Validate temporal value format."""
        # Check if date is reasonable (not too far in past/future)
        current_year = datetime.now().year
        return 1900 <= temporal.value.year <= current_year + 50


# Utility functions for advanced data operations
def create_filter_from_dict(filter_dict: Dict[str, Any]) -> FilterCriteria:
    """Create FilterCriteria from dictionary."""
    return FilterCriteria(
        field=filter_dict['field'],
        operator=FilterOperator(filter_dict['operator']),
        value=filter_dict['value'],
        case_sensitive=filter_dict.get('case_sensitive', False)
    )


def create_sort_from_dict(sort_dict: Dict[str, Any]) -> SortCriteria:
    """Create SortCriteria from dictionary."""
    return SortCriteria(
        field=sort_dict['field'],
        order=SortOrder(sort_dict.get('order', 'asc'))
    )


def merge_categories(categories1: Dict[CategoryType, List[Any]], 
                    categories2: Dict[CategoryType, List[Any]]) -> Dict[CategoryType, List[Any]]:
    """Merge two category dictionaries."""
    merged = categories1.copy()
    
    for category, items in categories2.items():
        if category in merged:
            merged[category].extend(items)
        else:
            merged[category] = items.copy()
    
    return merged


def get_category_statistics(categories: Dict[CategoryType, List[Any]]) -> Dict[str, Any]:
    """Get statistics about categorized data."""
    total_items = sum(len(items) for items in categories.values())
    
    stats = {
        'total_items': total_items,
        'total_categories': len(categories),
        'category_counts': {cat.value: len(items) for cat, items in categories.items()},
        'category_percentages': {}
    }
    
    if total_items > 0:
        stats['category_percentages'] = {
            cat.value: (len(items) / total_items) * 100 
            for cat, items in categories.items()
        }
    
    return stats