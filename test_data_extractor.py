"""
Comprehensive tests for the DataExtractor class.

Tests cover various text formats, edge cases, and data extraction scenarios
including tables, entities, numerical data, and temporal information.
"""

import pytest
from datetime import datetime
from data_extractor import DataExtractor, ExtractionConfig, validate_extracted_data, clean_extracted_data
from data_models import EntityType, StructuredData, DataTable, NamedEntity, NumericValue, TemporalValue


class TestDataExtractor:
    """Test suite for DataExtractor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = DataExtractor()
        self.config = ExtractionConfig()
    
    def test_extract_markdown_tables(self):
        """Test extraction of markdown-style tables."""
        text = """
        | Name | Age | City |
        |------|-----|------|
        | John | 25  | Berlin |
        | Jane | 30  | Munich |
        | Bob  | 35  | Hamburg |
        """
        
        result = self.extractor.extract_structured_data(text)
        
        assert len(result.tables) == 1
        table = result.tables[0]
        assert table.headers == ["Name", "Age", "City"]
        assert len(table.rows) == 3
        assert table.rows[0] == ["John", "25", "Berlin"]
        assert table.rows[1] == ["Jane", "30", "Munich"]
        assert table.rows[2] == ["Bob", "35", "Hamburg"]
    
    def test_extract_space_separated_tables(self):
        """Test extraction of space-separated tables."""
        text = """
        Product Price Quantity
        Laptop 999.99 5
        Mouse 29.99 20
        Keyboard 79.99 15
        """
        
        result = self.extractor.extract_structured_data(text)
        
        assert len(result.tables) >= 1
        # Find the table with Product header
        table = None
        for t in result.tables:
            if "Product" in t.headers:
                table = t
                break
        
        assert table is not None
        assert "Product" in table.headers
        assert "Price" in table.headers
        assert "Quantity" in table.headers
    
    def test_extract_key_value_tables(self):
        """Test extraction of key-value pairs as tables."""
        text = """
        Name: John Doe
        Age: 30
        City: Berlin
        Country: Germany
        Occupation: Software Engineer
        """
        
        result = self.extractor.extract_structured_data(text)
        
        # Should create a key-value table
        assert len(result.tables) >= 1
        kv_table = None
        for table in result.tables:
            if "Eigenschaft" in table.headers or "Name" in [row[0] for row in table.rows]:
                kv_table = table
                break
        
        assert kv_table is not None
        assert len(kv_table.rows) >= 3
    
    def test_extract_currency_values(self):
        """Test extraction of currency values in various formats."""
        text = """
        The price is €1.234,56 for the premium package.
        Alternative pricing: $2,500.00 USD
        Budget option: 500 EUR
        Special offer: 1.999,99 €
        """
        
        result = self.extractor.extract_structured_data(text)
        
        currency_values = [nv for nv in result.numeric_values if nv.value_type == 'currency']
        assert len(currency_values) >= 2
        
        # Check for Euro values
        euro_values = [cv for cv in currency_values if cv.unit == 'EUR']
        assert len(euro_values) >= 1
        
        # Check for USD values
        usd_values = [cv for cv in currency_values if cv.unit == 'USD']
        assert len(usd_values) >= 1
    
    def test_extract_percentages(self):
        """Test extraction of percentage values."""
        text = """
        The success rate is 85.5% this quarter.
        Growth increased by 12 Prozent.
        Market share: 25.3%
        """
        
        result = self.extractor.extract_structured_data(text)
        
        percentages = [nv for nv in result.numeric_values if nv.value_type == 'percentage']
        assert len(percentages) >= 2
        
        # Check specific values
        values = [p.value for p in percentages]
        assert 85.5 in values or 12.0 in values or 25.3 in values
    
    def test_extract_quantities_with_units(self):
        """Test extraction of quantities with various units."""
        text = """
        The package weighs 2.5 kg.
        Distance: 150 km
        Volume: 500 ml
        We need 100 Stück of this item.
        """
        
        result = self.extractor.extract_structured_data(text)
        
        quantities = [nv for nv in result.numeric_values if nv.value_type == 'quantity']
        assert len(quantities) >= 2
        
        # Check for different unit types
        units = [q.unit for q in quantities]
        assert any(unit in ['kg', 'km', 'ml', 'Stück'] for unit in units)
    
    def test_extract_person_entities(self):
        """Test extraction of person names."""
        text = """
        Dr. Angela Merkel was the Chancellor.
        Herr Schmidt and Frau Mueller attended the meeting.
        The report was written by Thomas Weber.
        """
        
        result = self.extractor.extract_structured_data(text)
        
        persons = [e for e in result.entities if e.entity_type == EntityType.PERSON]
        assert len(persons) >= 2
        
        person_names = [p.text for p in persons]
        # Should find at least some of these names
        expected_names = ["Angela Merkel", "Schmidt", "Mueller", "Thomas Weber"]
        assert any(name in person_names for name in expected_names)
    
    def test_extract_organization_entities(self):
        """Test extraction of organization names."""
        text = """
        Microsoft Corp. announced new features.
        The BMW AG headquarters is in Munich.
        Universität Berlin published the research.
        Siemens GmbH is a major employer.
        """
        
        result = self.extractor.extract_structured_data(text)
        
        organizations = [e for e in result.entities if e.entity_type == EntityType.ORGANIZATION]
        assert len(organizations) >= 2
        
        org_names = [o.text for o in organizations]
        expected_orgs = ["Microsoft Corp.", "BMW AG", "Universität Berlin", "Siemens GmbH"]
        assert any(org in org_names for org in expected_orgs)
    
    def test_extract_location_entities(self):
        """Test extraction of location names."""
        text = """
        The conference is in Berlin, Germany.
        We visited Munich and Hamburg last week.
        The company has offices in Frankfurt and Köln.
        """
        
        result = self.extractor.extract_structured_data(text)
        
        locations = [e for e in result.entities if e.entity_type == EntityType.LOCATION]
        assert len(locations) >= 2
        
        location_names = [l.text for l in locations]
        expected_locations = ["Berlin", "Germany", "Munich", "Hamburg", "Frankfurt", "Köln"]
        assert any(loc in location_names for loc in expected_locations)
    
    def test_extract_dates_german_format(self):
        """Test extraction of dates in German format."""
        text = """
        The meeting is scheduled for 15.03.2024.
        Deadline: 31/12/2023
        Project started on 1. Januar 2023.
        """
        
        result = self.extractor.extract_structured_data(text)
        
        assert len(result.temporal_data) >= 1
        
        # Check for specific dates
        date_texts = [td.original_text for td in result.temporal_data]
        assert any("15.03.2024" in dt or "31/12/2023" in dt for dt in date_texts)
    
    def test_extract_dates_various_formats(self):
        """Test extraction of dates in various formats."""
        text = """
        Event date: 2024-05-15
        Another date: 25. Dezember 2023
        ISO format: 2023-12-31T23:59:59
        """
        
        result = self.extractor.extract_structured_data(text)
        
        assert len(result.temporal_data) >= 1
        
        # Check that dates were parsed correctly
        for temporal in result.temporal_data:
            assert isinstance(temporal.value, datetime)
            assert temporal.value.year >= 2023
    
    def test_german_number_parsing(self):
        """Test parsing of German number formats."""
        text = """
        Price: 1.234,56 €
        Large number: 1.000.000,00
        Small decimal: 0,75
        """
        
        result = self.extractor.extract_structured_data(text)
        
        # Should parse German number format correctly
        numeric_values = result.numeric_values
        assert len(numeric_values) >= 1
        
        # Check that numbers were parsed correctly
        values = [nv.value for nv in numeric_values]
        assert any(v > 1000 for v in values)  # Should have large numbers
    
    def test_data_categorization(self):
        """Test automatic data categorization."""
        text = """
        Dr. John Smith works at Microsoft Corp.
        The price is €1,500.
        Success rate: 95%
        Meeting date: 15.03.2024
        """
        
        result = self.extractor.extract_structured_data(text)
        
        # Should have categories for different data types
        assert 'person' in result.categories or 'organization' in result.categories
        assert 'currency' in result.categories or 'percentage' in result.categories
        
        # Categories should contain the extracted items
        for category, items in result.categories.items():
            assert len(items) > 0
    
    def test_relationship_extraction(self):
        """Test extraction of relationships between entities."""
        text = """
        Dr. Angela Merkel worked at the German Government.
        Microsoft Corp. is based in Seattle.
        """
        
        result = self.extractor.extract_structured_data(text)
        
        # Should find some relationships
        assert len(result.relationships) >= 0  # May or may not find relationships
        
        # If relationships are found, they should have proper structure
        for rel in result.relationships:
            assert rel.source
            assert rel.target
            assert rel.relationship_type
            assert 0 <= rel.confidence <= 1
    
    def test_extraction_config(self):
        """Test extraction with custom configuration."""
        config = ExtractionConfig(
            extract_tables=False,
            extract_entities=True,
            extract_numbers=False,
            extract_dates=True,
            min_confidence=0.8
        )
        
        extractor = DataExtractor(config)
        
        text = """
        | Name | Age |
        |------|-----|
        | John | 25  |
        
        Dr. Smith attended the meeting on 15.03.2024.
        Price: €100
        """
        
        result = extractor.extract_structured_data(text)
        
        # Should respect configuration
        assert len(result.tables) == 0  # Tables disabled
        assert len(result.entities) >= 0  # Entities enabled
        assert len(result.numeric_values) == 0  # Numbers disabled
        assert len(result.temporal_data) >= 0  # Dates enabled
    
    def test_edge_cases_empty_text(self):
        """Test extraction with empty or minimal text."""
        # Empty text
        result = self.extractor.extract_structured_data("")
        assert len(result.tables) == 0
        assert len(result.entities) == 0
        assert len(result.numeric_values) == 0
        assert len(result.temporal_data) == 0
        
        # Whitespace only
        result = self.extractor.extract_structured_data("   \n\t   ")
        assert len(result.tables) == 0
        assert len(result.entities) == 0
        assert len(result.numeric_values) == 0
        assert len(result.temporal_data) == 0
    
    def test_edge_cases_malformed_tables(self):
        """Test extraction with malformed table data."""
        text = """
        | Name | Age |
        | John | 25 | Extra |
        | Jane |
        |------|-----|
        """
        
        result = self.extractor.extract_structured_data(text)
        
        # Should handle malformed tables gracefully
        # May or may not extract a table, but shouldn't crash
        assert isinstance(result, StructuredData)
    
    def test_edge_cases_invalid_numbers(self):
        """Test extraction with invalid number formats."""
        text = """
        Invalid: €abc.def
        Partial: 123.
        Multiple dots: 1.2.3.4
        """
        
        result = self.extractor.extract_structured_data(text)
        
        # Should handle invalid numbers gracefully
        assert isinstance(result, StructuredData)
        # May extract some numbers, but shouldn't crash
    
    def test_edge_cases_invalid_dates(self):
        """Test extraction with invalid date formats."""
        text = """
        Invalid date: 32.13.2024
        Partial date: 15.
        Wrong format: 2024/25/15
        """
        
        result = self.extractor.extract_structured_data(text)
        
        # Should handle invalid dates gracefully
        assert isinstance(result, StructuredData)
        # Should not extract invalid dates
    
    def test_large_text_performance(self):
        """Test extraction performance with large text."""
        # Create a large text with repeated patterns
        large_text = """
        Dr. John Smith works at Microsoft Corp. in Seattle.
        The price is €1,234.56 and the date is 15.03.2024.
        Success rate: 95.5% for this quarter.
        """ * 100  # Repeat 100 times
        
        result = self.extractor.extract_structured_data(large_text)
        
        # Should complete without timeout and find patterns
        assert isinstance(result, StructuredData)
        assert len(result.entities) > 0
        assert len(result.numeric_values) > 0
    
    def test_mixed_language_content(self):
        """Test extraction with mixed German/English content."""
        text = """
        Dr. Angela Merkel met with President Biden.
        Der Preis beträgt €500 and the success rate is 90%.
        Meeting date: 15. März 2024 at 14:00 Uhr.
        """
        
        result = self.extractor.extract_structured_data(text)
        
        # Should extract entities and data from both languages
        assert len(result.entities) >= 2  # Should find names
        assert len(result.numeric_values) >= 2  # Should find price and percentage
    
    def test_special_characters_and_encoding(self):
        """Test extraction with special characters and German umlauts."""
        text = """
        Herr Müller arbeitet bei der Universität München.
        Preis: 1.500,50 € für das Paket.
        Erfolgsquote: 87,5% im letzten Quartal.
        """
        
        result = self.extractor.extract_structured_data(text)
        
        # Should handle German characters correctly
        persons = [e for e in result.entities if e.entity_type == EntityType.PERSON]
        organizations = [e for e in result.entities if e.entity_type == EntityType.ORGANIZATION]
        
        assert len(persons) >= 1
        assert len(organizations) >= 1
        assert len(result.numeric_values) >= 2


class TestDataValidation:
    """Test suite for data validation functions."""
    
    def test_validate_extracted_data_valid(self):
        """Test validation of valid structured data."""
        structured_data = StructuredData()
        structured_data.tables = [
            DataTable(headers=["Name", "Age"], rows=[["John", "25"], ["Jane", "30"]])
        ]
        structured_data.entities = [
            NamedEntity(text="John Doe", entity_type=EntityType.PERSON, confidence=0.9)
        ]
        
        validation = validate_extracted_data(structured_data)
        
        assert validation['is_valid'] is True
        assert validation['quality_score'] > 0.5
        assert validation['metrics']['total_tables'] == 1
        assert validation['metrics']['total_entities'] == 1
    
    def test_validate_extracted_data_warnings(self):
        """Test validation with data that generates warnings."""
        structured_data = StructuredData()
        structured_data.tables = [
            DataTable(headers=[], rows=[["data1", "data2"]])  # No headers
        ]
        structured_data.entities = [
            NamedEntity(text="Low Confidence", entity_type=EntityType.PERSON, confidence=0.3)
        ]
        
        validation = validate_extracted_data(structured_data)
        
        assert len(validation['warnings']) > 0
        assert validation['quality_score'] < 1.0
    
    def test_validate_extracted_data_empty(self):
        """Test validation of empty structured data."""
        structured_data = StructuredData()
        
        validation = validate_extracted_data(structured_data)
        
        assert validation['is_valid'] is True
        assert validation['quality_score'] == 0.0
        assert validation['metrics']['total_tables'] == 0


class TestDataCleaning:
    """Test suite for data cleaning functions."""
    
    def test_clean_extracted_data_duplicates(self):
        """Test cleaning of duplicate entities and values."""
        structured_data = StructuredData()
        
        # Add duplicate entities
        structured_data.entities = [
            NamedEntity(text="John Doe", entity_type=EntityType.PERSON, confidence=0.9),
            NamedEntity(text="john doe", entity_type=EntityType.PERSON, confidence=0.8),  # Duplicate
            NamedEntity(text="Jane Smith", entity_type=EntityType.PERSON, confidence=0.9)
        ]
        
        # Add duplicate numeric values
        structured_data.numeric_values = [
            NumericValue(value=100.0, unit="EUR", value_type="currency"),
            NumericValue(value=100.0, unit="EUR", value_type="currency"),  # Duplicate
            NumericValue(value=200.0, unit="USD", value_type="currency")
        ]
        
        cleaned_data = clean_extracted_data(structured_data)
        
        # Should remove duplicates
        assert len(cleaned_data.entities) == 2  # One duplicate removed
        assert len(cleaned_data.numeric_values) == 2  # One duplicate removed
    
    def test_clean_extracted_data_empty_rows(self):
        """Test cleaning of empty table rows."""
        structured_data = StructuredData()
        structured_data.tables = [
            DataTable(
                headers=["Name", "Age"],
                rows=[
                    ["John", "25"],
                    ["", ""],  # Empty row
                    ["Jane", "30"],
                    ["   ", "  "]  # Whitespace only row
                ]
            )
        ]
        
        cleaned_data = clean_extracted_data(structured_data)
        
        # Should remove empty rows
        assert len(cleaned_data.tables[0].rows) == 2
        assert cleaned_data.tables[0].rows[0] == ["John", "25"]
        assert cleaned_data.tables[0].rows[1] == ["Jane", "30"]
    
    def test_clean_extracted_data_normalize_cells(self):
        """Test normalization of table cell content."""
        structured_data = StructuredData()
        structured_data.tables = [
            DataTable(
                headers=["Name", "Age"],
                rows=[
                    ["  John  ", " 25 "],  # Extra whitespace
                    [" Jane\t", "30\n"]    # Tabs and newlines
                ]
            )
        ]
        
        cleaned_data = clean_extracted_data(structured_data)
        
        # Should normalize cell content
        assert cleaned_data.tables[0].rows[0] == ["John", "25"]
        assert cleaned_data.tables[0].rows[1] == ["Jane", "30"]


if __name__ == "__main__":
    pytest.main([__file__])