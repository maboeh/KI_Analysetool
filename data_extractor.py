"""
Data extraction engine for structured data recognition.

This module provides the DataExtractor class that can extract various types of
structured data from text, including tables, lists, numerical data, entities,
and temporal information.
"""

import re
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from dateutil import parser as date_parser
from data_models import (
    StructuredData, DataTable, NamedEntity, NumericValue, TemporalValue,
    EntityType, DataRelationship
)


@dataclass
class ExtractionConfig:
    """Configuration for data extraction behavior."""
    extract_tables: bool = True
    extract_entities: bool = True
    extract_numbers: bool = True
    extract_dates: bool = True
    min_confidence: float = 0.5
    max_table_rows: int = 1000
    date_formats: List[str] = None
    
    def __post_init__(self):
        if self.date_formats is None:
            self.date_formats = [
                "%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y",
                "%B %d, %Y", "%d. %B %Y", "%m/%d/%Y"
            ]


class DataExtractor:
    """
    Main class for extracting structured data from text content.
    
    Supports extraction of:
    - Tables and lists
    - Named entities (persons, places, organizations, dates)
    - Numerical data (currency, percentages, quantities)
    - Temporal data (dates and times)
    - Data relationships
    """
    
    def __init__(self, config: Optional[ExtractionConfig] = None):
        self.config = config or ExtractionConfig()
        self._init_patterns()
    
    def _init_patterns(self):
        """Initialize regex patterns for data extraction."""
        # Currency patterns (Euro, Dollar, etc.)
        self.currency_patterns = [
            r'€\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)',  # €1.234,56
            r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)\s*€',  # 1.234,56 €
            r'\$\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)', # $1,234.56
            r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)\s*USD', # 1,234.56 USD
            r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)\s*EUR', # 1,234.56 EUR
        ]
        
        # Percentage patterns
        self.percentage_patterns = [
            r'(\d+(?:[.,]\d+)?)\s*%',  # 25.5%
            r'(\d+(?:[.,]\d+)?)\s*Prozent',  # 25 Prozent
        ]
        
        # Quantity patterns
        self.quantity_patterns = [
            r'(\d+(?:[.,]\d+)?)\s*(kg|g|mg|t|Tonnen?)',  # Weight
            r'(\d+(?:[.,]\d+)?)\s*(km|m|cm|mm)',  # Distance
            r'(\d+(?:[.,]\d+)?)\s*(l|ml|Liter)',  # Volume
            r'(\d+(?:[.,]\d+)?)\s*(Stück|Stk\.?|Einheiten?)',  # Count
        ]
        
        # General number patterns
        self.number_patterns = [
            r'\b(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,4})?)\b',  # General numbers
        ]
        
        # Entity patterns
        self.person_patterns = [
            r'\b([A-ZÄÖÜ][a-zäöüß]+\s+[A-ZÄÖÜ][a-zäöüß]+)\b',  # First Last
            r'\b(Dr\.|Prof\.|Herr|Frau)\s+([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)*)\b',
        ]
        
        self.organization_patterns = [
            r'\b([A-ZÄÖÜ][A-Za-zäöüß\s&]+(?:GmbH|AG|e\.V\.|Inc\.|Corp\.|Ltd\.))\b',
            r'\b([A-ZÄÖÜ][A-Za-zäöüß\s&]+ (?:Universität|University|Institut|Institute))\b',
        ]
        
        # Date patterns (German format)
        self.date_patterns = [
            r'\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b',  # DD.MM.YYYY
            r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b',   # DD/MM/YYYY
            r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b',   # YYYY-MM-DD
            r'\b(\d{1,2})\.\s*(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s*(\d{4})\b',
        ]
        
        # Table detection patterns
        self.table_patterns = [
            r'^\s*\|.*\|\s*$',  # Markdown table rows
            r'^\s*[^\s]+\s+[^\s]+\s+[^\s]+.*$',  # Space-separated columns
        ]
    
    def extract_structured_data(self, text: str) -> StructuredData:
        """
        Extract all types of structured data from text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            StructuredData object containing all extracted information
        """
        structured_data = StructuredData()
        
        if self.config.extract_tables:
            structured_data.tables = self.extract_tables(text)
        
        if self.config.extract_entities:
            structured_data.entities = self.extract_entities(text)
        
        if self.config.extract_numbers:
            structured_data.numeric_values = self.extract_numerical_data(text)
        
        if self.config.extract_dates:
            structured_data.temporal_data = self.extract_dates(text)
        
        # Extract categories based on found data
        structured_data.categories = self._categorize_data(structured_data)
        
        # Extract relationships
        structured_data.relationships = self._extract_relationships(text, structured_data)
        
        return structured_data
    
    def extract_tables(self, text: str) -> List[DataTable]:
        """
        Extract tables from text content.
        
        Args:
            text: Input text containing potential tables
            
        Returns:
            List of DataTable objects
        """
        tables = []
        lines = text.split('\n')
        
        # Try to detect markdown tables
        markdown_tables = self._extract_markdown_tables(lines)
        tables.extend(markdown_tables)
        
        # Try to detect space-separated tables
        space_tables = self._extract_space_separated_tables(lines)
        tables.extend(space_tables)
        
        # Try to detect colon-separated key-value pairs as tables
        kv_tables = self._extract_key_value_tables(lines)
        tables.extend(kv_tables)
        
        return tables[:self.config.max_table_rows]  # Limit number of tables
    
    def _extract_markdown_tables(self, lines: List[str]) -> List[DataTable]:
        """Extract markdown-style tables."""
        tables = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Check if this looks like a markdown table header
            if '|' in line and line.count('|') >= 2:
                # Look for separator line
                if i + 1 < len(lines) and re.match(r'^\s*\|[\s\-\|:]+\|\s*$', lines[i + 1]):
                    # Extract table
                    headers = [h.strip() for h in line.split('|')[1:-1]]
                    rows = []
                    
                    j = i + 2  # Skip separator line
                    while j < len(lines) and '|' in lines[j] and lines[j].count('|') >= 2:
                        row_data = [cell.strip() for cell in lines[j].split('|')[1:-1]]
                        if len(row_data) == len(headers):
                            rows.append(row_data)
                        j += 1
                    
                    if rows:
                        tables.append(DataTable(headers=headers, rows=rows, title=f"Table {len(tables) + 1}"))
                    
                    i = j
                else:
                    i += 1
            else:
                i += 1
        
        return tables
    
    def _extract_space_separated_tables(self, lines: List[str]) -> List[DataTable]:
        """Extract space-separated tables."""
        tables = []
        current_table_lines = []
        processed_line_indices = set()
        
        for i, line in enumerate(lines):
            # Skip lines that were already processed as markdown tables
            if i in processed_line_indices:
                continue
                
            stripped = line.strip()
            
            # Skip markdown table lines (contain |)
            if '|' in stripped:
                continue
            
            # Check if line looks like table data (multiple words separated by spaces)
            if stripped and len(stripped.split()) >= 3:
                # Check if all "columns" have consistent spacing
                words = stripped.split()
                if len(words) >= 3 and all(len(w) > 0 for w in words):
                    current_table_lines.append(words)
            else:
                # End of potential table
                if len(current_table_lines) >= 2:  # At least header + 1 row
                    # Check if all rows have same number of columns
                    col_counts = [len(row) for row in current_table_lines]
                    if len(set(col_counts)) == 1:  # All rows have same column count
                        headers = current_table_lines[0]
                        rows = current_table_lines[1:]
                        tables.append(DataTable(headers=headers, rows=rows, title=f"Table {len(tables) + 1}"))
                
                current_table_lines = []
        
        # Check final table
        if len(current_table_lines) >= 2:
            col_counts = [len(row) for row in current_table_lines]
            if len(set(col_counts)) == 1:
                headers = current_table_lines[0]
                rows = current_table_lines[1:]
                tables.append(DataTable(headers=headers, rows=rows, title=f"Table {len(tables) + 1}"))
        
        return tables
    
    def _extract_key_value_tables(self, lines: List[str]) -> List[DataTable]:
        """Extract key-value pairs as tables."""
        tables = []
        kv_pairs = []
        
        for line in lines:
            stripped = line.strip()
            
            # Look for key: value patterns
            if ':' in stripped:
                parts = stripped.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    if key and value and len(key) < 100:  # Reasonable key length
                        kv_pairs.append([key, value])
            else:
                # End of key-value section
                if len(kv_pairs) >= 3:  # At least 3 pairs to make a table
                    headers = ["Eigenschaft", "Wert"]
                    tables.append(DataTable(headers=headers, rows=kv_pairs, title="Eigenschaften"))
                kv_pairs = []
        
        # Check final pairs
        if len(kv_pairs) >= 3:
            headers = ["Eigenschaft", "Wert"]
            tables.append(DataTable(headers=headers, rows=kv_pairs, title="Eigenschaften"))
        
        return tables
    
    def extract_entities(self, text: str) -> List[NamedEntity]:
        """
        Extract named entities from text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of NamedEntity objects
        """
        entities = []
        
        # Extract persons
        entities.extend(self._extract_persons(text))
        
        # Extract organizations
        entities.extend(self._extract_organizations(text))
        
        # Extract locations (basic pattern matching)
        entities.extend(self._extract_locations(text))
        
        return entities
    
    def _extract_persons(self, text: str) -> List[NamedEntity]:
        """Extract person names from text."""
        persons = []
        
        for pattern in self.person_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                name = match.group(1) if match.lastindex >= 1 else match.group(0)
                persons.append(NamedEntity(
                    text=name,
                    entity_type=EntityType.PERSON,
                    confidence=0.8,
                    start_pos=match.start(),
                    end_pos=match.end()
                ))
        
        return persons
    
    def _extract_organizations(self, text: str) -> List[NamedEntity]:
        """Extract organization names from text."""
        organizations = []
        
        for pattern in self.organization_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                org_name = match.group(1) if match.lastindex >= 1 else match.group(0)
                organizations.append(NamedEntity(
                    text=org_name,
                    entity_type=EntityType.ORGANIZATION,
                    confidence=0.7,
                    start_pos=match.start(),
                    end_pos=match.end()
                ))
        
        return organizations
    
    def _extract_locations(self, text: str) -> List[NamedEntity]:
        """Extract location names from text (basic implementation)."""
        locations = []
        
        # Simple pattern for German cities and countries
        location_patterns = [
            r'\b(Berlin|München|Hamburg|Köln|Frankfurt|Stuttgart|Düsseldorf|Dortmund|Essen|Leipzig|Bremen|Dresden|Hannover|Nürnberg|Duisburg|Bochum|Wuppertal|Bielefeld|Bonn|Münster|Karlsruhe|Mannheim|Augsburg|Wiesbaden|Gelsenkirchen|Mönchengladbach|Braunschweig|Chemnitz|Kiel|Aachen|Halle|Magdeburg|Freiburg|Krefeld|Lübeck|Oberhausen|Erfurt|Mainz|Rostock|Kassel|Hagen|Hamm|Saarbrücken|Mülheim|Potsdam|Ludwigshafen|Oldenburg|Leverkusen|Osnabrück|Solingen|Heidelberg|Herne|Neuss|Darmstadt|Paderborn|Regensburg|Ingolstadt|Würzburg|Fürth|Wolfsburg|Offenbach|Ulm|Heilbronn|Pforzheim|Göttingen|Bottrop|Trier|Recklinghausen|Reutlingen|Bremerhaven|Koblenz|Bergisch Gladbach|Jena|Remscheid|Erlangen|Moers|Siegen|Hildesheim|Salzgitter)\b',
            r'\b(Deutschland|Germany|Österreich|Austria|Schweiz|Switzerland|Frankreich|France|Italien|Italy|Spanien|Spain|Niederlande|Netherlands|Belgien|Belgium|Polen|Poland|Tschechien|Czech Republic)\b'
        ]
        
        for pattern in location_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                location = match.group(0)
                locations.append(NamedEntity(
                    text=location,
                    entity_type=EntityType.LOCATION,
                    confidence=0.6,
                    start_pos=match.start(),
                    end_pos=match.end()
                ))
        
        return locations
    
    def extract_numerical_data(self, text: str) -> List[NumericValue]:
        """
        Extract numerical data including currency, percentages, and quantities.
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of NumericValue objects
        """
        numeric_values = []
        
        # Extract currency values
        numeric_values.extend(self._extract_currency(text))
        
        # Extract percentages
        numeric_values.extend(self._extract_percentages(text))
        
        # Extract quantities with units
        numeric_values.extend(self._extract_quantities(text))
        
        # Extract general numbers
        numeric_values.extend(self._extract_general_numbers(text))
        
        return numeric_values
    
    def _extract_currency(self, text: str) -> List[NumericValue]:
        """Extract currency values from text."""
        currency_values = []
        
        for pattern in self.currency_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                value_str = match.group(1)
                # Convert German number format to float
                value = self._parse_german_number(value_str)
                
                # Determine currency unit
                full_match = match.group(0)
                if '€' in full_match or 'EUR' in full_match:
                    unit = 'EUR'
                elif '$' in full_match or 'USD' in full_match:
                    unit = 'USD'
                else:
                    unit = 'currency'
                
                currency_values.append(NumericValue(
                    value=value,
                    unit=unit,
                    context=self._get_context(text, match.start(), match.end()),
                    value_type='currency'
                ))
        
        return currency_values
    
    def _extract_percentages(self, text: str) -> List[NumericValue]:
        """Extract percentage values from text."""
        percentages = []
        
        for pattern in self.percentage_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                value_str = match.group(1)
                value = self._parse_german_number(value_str)
                
                percentages.append(NumericValue(
                    value=value,
                    unit='%',
                    context=self._get_context(text, match.start(), match.end()),
                    value_type='percentage'
                ))
        
        return percentages
    
    def _extract_quantities(self, text: str) -> List[NumericValue]:
        """Extract quantities with units from text."""
        quantities = []
        
        for pattern in self.quantity_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                value_str = match.group(1)
                unit = match.group(2)
                value = self._parse_german_number(value_str)
                
                quantities.append(NumericValue(
                    value=value,
                    unit=unit,
                    context=self._get_context(text, match.start(), match.end()),
                    value_type='quantity'
                ))
        
        return quantities
    
    def _extract_general_numbers(self, text: str) -> List[NumericValue]:
        """Extract general numeric values from text."""
        numbers = []
        processed_positions = set()
        
        for pattern in self.number_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                # Skip if this position was already processed by more specific patterns
                if any(pos in processed_positions for pos in range(match.start(), match.end())):
                    continue
                
                value_str = match.group(1)
                try:
                    value = self._parse_german_number(value_str)
                    
                    # Only include if it's a significant number (not just years, etc.)
                    if value > 1900 and value < 2100:
                        continue  # Skip likely years
                    
                    numbers.append(NumericValue(
                        value=value,
                        context=self._get_context(text, match.start(), match.end()),
                        value_type='number'
                    ))
                    
                    # Mark positions as processed
                    for pos in range(match.start(), match.end()):
                        processed_positions.add(pos)
                        
                except ValueError:
                    continue
        
        return numbers
    
    def extract_dates(self, text: str) -> List[TemporalValue]:
        """
        Extract dates and temporal information from text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of TemporalValue objects
        """
        dates = []
        
        # Extract using predefined patterns
        for pattern in self.date_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                date_str = match.group(0)
                try:
                    # Try to parse the date
                    parsed_date = self._parse_date(date_str)
                    if parsed_date:
                        precision = self._determine_date_precision(date_str)
                        dates.append(TemporalValue(
                            value=parsed_date,
                            original_text=date_str,
                            precision=precision
                        ))
                except Exception:
                    continue
        
        # Try dateutil parser for more flexible parsing
        words = text.split()
        for i, word in enumerate(words):
            if len(word) >= 4:  # Minimum reasonable date length
                try:
                    # Try to parse individual words or combinations
                    for j in range(i, min(i + 3, len(words))):  # Try up to 3 words
                        date_candidate = ' '.join(words[i:j+1])
                        if len(date_candidate) >= 4:
                            parsed_date = date_parser.parse(date_candidate, fuzzy=True, default=datetime(2000, 1, 1))
                            if parsed_date.year > 1900 and parsed_date.year < 2100:
                                dates.append(TemporalValue(
                                    value=parsed_date,
                                    original_text=date_candidate,
                                    precision=self._determine_date_precision(date_candidate)
                                ))
                                break
                except Exception:
                    continue
        
        # Remove duplicates based on original text
        seen_texts = set()
        unique_dates = []
        for date in dates:
            if date.original_text not in seen_texts:
                seen_texts.add(date.original_text)
                unique_dates.append(date)
        
        return unique_dates
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse a date string using various formats."""
        for fmt in self.config.date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Try dateutil as fallback
        try:
            return date_parser.parse(date_str, dayfirst=True)
        except Exception:
            return None
    
    def _determine_date_precision(self, date_str: str) -> str:
        """Determine the precision of a date string."""
        if re.search(r'\d{1,2}:\d{2}', date_str):
            return 'minute'
        elif re.search(r'\d{1,2}\.\d{1,2}\.\d{4}', date_str):
            return 'day'
        elif re.search(r'\d{1,2}/\d{4}', date_str):
            return 'month'
        elif re.search(r'\d{4}', date_str):
            return 'year'
        else:
            return 'day'  # Default
    
    def _parse_german_number(self, number_str: str) -> float:
        """Parse German number format (1.234,56) to float."""
        # Handle German number format
        if ',' in number_str and '.' in number_str:
            # Both comma and dot - assume German format (1.234,56)
            number_str = number_str.replace('.', '').replace(',', '.')
        elif ',' in number_str:
            # Only comma - could be decimal separator or thousands separator
            parts = number_str.split(',')
            if len(parts) == 2 and len(parts[1]) <= 2:
                # Likely decimal separator (e.g., 1,50)
                number_str = number_str.replace(',', '.')
            else:
                # Likely thousands separator (e.g., 1,500) - remove comma
                number_str = number_str.replace(',', '')
        
        return float(number_str)
    
    def _get_context(self, text: str, start: int, end: int, window: int = 50) -> str:
        """Get context around a match for better understanding."""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end].strip()
    
    def _categorize_data(self, structured_data: StructuredData) -> Dict[str, List[str]]:
        """Categorize extracted data into logical groups."""
        categories = {}
        
        # Categorize entities by type
        for entity in structured_data.entities:
            entity_type = entity.entity_type.value
            if entity_type not in categories:
                categories[entity_type] = []
            categories[entity_type].append(entity.text)
        
        # Categorize numeric values by type
        for numeric in structured_data.numeric_values:
            if numeric.value_type:
                if numeric.value_type not in categories:
                    categories[numeric.value_type] = []
                categories[numeric.value_type].append(f"{numeric.value} {numeric.unit or ''}")
        
        # Add table categories
        if structured_data.tables:
            categories['tables'] = [table.title or f"Table {i+1}" for i, table in enumerate(structured_data.tables)]
        
        return categories
    
    def _extract_relationships(self, text: str, structured_data: StructuredData) -> List[DataRelationship]:
        """Extract relationships between data elements."""
        relationships = []
        
        # Simple relationship extraction based on proximity and patterns
        entities = structured_data.entities
        
        for i, entity1 in enumerate(entities):
            for j, entity2 in enumerate(entities[i+1:], i+1):
                # Check if entities are close to each other in text
                if entity1.start_pos and entity2.start_pos:
                    distance = abs(entity1.start_pos - entity2.start_pos)
                    if distance < 100:  # Within 100 characters
                        # Determine relationship type based on entity types
                        rel_type = self._determine_relationship_type(entity1, entity2)
                        if rel_type:
                            relationships.append(DataRelationship(
                                source=entity1.text,
                                target=entity2.text,
                                relationship_type=rel_type,
                                confidence=0.6
                            ))
        
        return relationships
    
    def _determine_relationship_type(self, entity1: NamedEntity, entity2: NamedEntity) -> Optional[str]:
        """Determine the type of relationship between two entities."""
        type1, type2 = entity1.entity_type, entity2.entity_type
        
        if type1 == EntityType.PERSON and type2 == EntityType.ORGANIZATION:
            return "works_at"
        elif type1 == EntityType.ORGANIZATION and type2 == EntityType.PERSON:
            return "employs"
        elif type1 == EntityType.PERSON and type2 == EntityType.LOCATION:
            return "located_in"
        elif type1 == EntityType.ORGANIZATION and type2 == EntityType.LOCATION:
            return "based_in"
        elif type1 == EntityType.PERSON and type2 == EntityType.PERSON:
            return "associated_with"
        
        return None


# Utility functions for data validation and cleaning
def validate_extracted_data(structured_data: StructuredData) -> Dict[str, Any]:
    """
    Validate extracted structured data and return quality metrics.
    
    Args:
        structured_data: The extracted structured data to validate
        
    Returns:
        Dictionary containing validation results and quality metrics
    """
    validation_results = {
        'is_valid': True,
        'warnings': [],
        'errors': [],
        'quality_score': 0.0,
        'metrics': {}
    }
    
    # Validate tables
    for i, table in enumerate(structured_data.tables):
        if not table.headers:
            validation_results['warnings'].append(f"Table {i+1} has no headers")
        if not table.rows:
            validation_results['warnings'].append(f"Table {i+1} has no data rows")
        
        # Check for consistent column counts
        if table.rows:
            header_count = len(table.headers)
            for j, row in enumerate(table.rows):
                if len(row) != header_count:
                    validation_results['warnings'].append(
                        f"Table {i+1}, row {j+1}: Column count mismatch"
                    )
    
    # Validate entities
    low_confidence_entities = [e for e in structured_data.entities if e.confidence < 0.5]
    if low_confidence_entities:
        validation_results['warnings'].append(
            f"{len(low_confidence_entities)} entities have low confidence scores"
        )
    
    # Calculate quality score
    total_items = (len(structured_data.tables) + len(structured_data.entities) + 
                  len(structured_data.numeric_values) + len(structured_data.temporal_data))
    
    if total_items > 0:
        warning_penalty = len(validation_results['warnings']) * 0.1
        error_penalty = len(validation_results['errors']) * 0.3
        validation_results['quality_score'] = max(0.0, 1.0 - warning_penalty - error_penalty)
    
    # Set metrics
    validation_results['metrics'] = {
        'total_tables': len(structured_data.tables),
        'total_entities': len(structured_data.entities),
        'total_numeric_values': len(structured_data.numeric_values),
        'total_temporal_values': len(structured_data.temporal_data),
        'total_relationships': len(structured_data.relationships)
    }
    
    return validation_results


def clean_extracted_data(structured_data: StructuredData) -> StructuredData:
    """
    Clean and normalize extracted structured data.
    
    Args:
        structured_data: The structured data to clean
        
    Returns:
        Cleaned StructuredData object
    """
    # Remove duplicate entities
    seen_entities = set()
    unique_entities = []
    for entity in structured_data.entities:
        entity_key = (entity.text.lower(), entity.entity_type)
        if entity_key not in seen_entities:
            seen_entities.add(entity_key)
            unique_entities.append(entity)
    
    structured_data.entities = unique_entities
    
    # Remove duplicate numeric values (same value and context)
    seen_numeric = set()
    unique_numeric = []
    for numeric in structured_data.numeric_values:
        numeric_key = (numeric.value, numeric.unit, numeric.value_type)
        if numeric_key not in seen_numeric:
            seen_numeric.add(numeric_key)
            unique_numeric.append(numeric)
    
    structured_data.numeric_values = unique_numeric
    
    # Clean table data
    for table in structured_data.tables:
        # Remove empty rows
        table.rows = [row for row in table.rows if any(cell.strip() for cell in row)]
        
        # Normalize cell content
        for row in table.rows:
            for i, cell in enumerate(row):
                row[i] = cell.strip()
    
    return structured_data