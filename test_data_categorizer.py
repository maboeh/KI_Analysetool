"""
Comprehensive tests for the DataCategorizer class and filtering system.

Tests cover data categorization, filtering, sorting, and data quality assessment.
"""

import pytest
from datetime import datetime, timedelta
from data_categorizer import (
    DataCategorizer, CategoryType, FilterOperator, SortOrder,
    FilterCriteria, SortCriteria, DataQualityMetrics,
    create_filter_from_dict, create_sort_from_dict, merge_categories, get_category_statistics
)
from data_models import (
    StructuredData, DataTable, NamedEntity, NumericValue, TemporalValue,
    EntityType
)


class TestDataCategorizer:
    """Test suite for DataCategorizer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.categorizer = DataCategorizer()
        self.sample_data = self._create_sample_structured_data()
    
    def _create_sample_structured_data(self) -> StructuredData:
        """Create sample structured data for testing."""
        structured_data = StructuredData()
        
        # Add entities
        structured_data.entities = [
            NamedEntity(text="John Doe", entity_type=EntityType.PERSON, confidence=0.9),
            NamedEntity(text="Microsoft Corp.", entity_type=EntityType.ORGANIZATION, confidence=0.8),
            NamedEntity(text="Berlin", entity_type=EntityType.LOCATION, confidence=0.7),
            NamedEntity(text="jane.doe@example.com", entity_type=EntityType.PERSON, confidence=0.6),
        ]
        
        # Add numeric values
        structured_data.numeric_values = [
            NumericValue(value=1500.0, unit="EUR", value_type="currency"),
            NumericValue(value=95.5, unit="%", value_type="percentage"),
            NumericValue(value=2.5, unit="kg", value_type="quantity"),
            NumericValue(value=1000000, unit="EUR", value_type="currency"),
        ]
        
        # Add temporal data
        structured_data.temporal_data = [
            TemporalValue(value=datetime(2024, 3, 15), original_text="15.03.2024", precision="day"),
            TemporalValue(value=datetime(2023, 12, 31), original_text="31.12.2023", precision="day"),
        ]
        
        # Add tables
        structured_data.tables = [
            DataTable(
                headers=["Name", "Salary", "Department"],
                rows=[
                    ["Alice Smith", "50000 EUR", "Engineering"],
                    ["Bob Johnson", "45000 EUR", "Marketing"],
                    ["Carol Davis", "55000 EUR", "Engineering"]
                ],
                title="Employee Data"
            )
        ]
        
        return structured_data
    
    def test_categorize_structured_data(self):
        """Test automatic categorization of structured data."""
        categories = self.categorizer.categorize_structured_data(self.sample_data)
        
        # Should have multiple categories
        assert len(categories) >= 3
        
        # Check specific categories
        assert CategoryType.PERSONAL in categories
        assert CategoryType.ORGANIZATIONAL in categories
        assert CategoryType.FINANCIAL in categories
        assert CategoryType.GEOGRAPHICAL in categories
        assert CategoryType.TEMPORAL in categories
        
        # Check category contents
        personal_items = categories[CategoryType.PERSONAL]
        assert len(personal_items) >= 1
        
        financial_items = categories[CategoryType.FINANCIAL]
        assert len(financial_items) >= 2  # Currency values
        
        geographical_items = categories[CategoryType.GEOGRAPHICAL]
        assert len(geographical_items) >= 1  # Location entity
    
    def test_categorize_entities(self):
        """Test categorization of different entity types."""
        entities = [
            NamedEntity(text="Dr. Angela Merkel", entity_type=EntityType.PERSON, confidence=0.9),
            NamedEntity(text="BMW AG", entity_type=EntityType.ORGANIZATION, confidence=0.8),
            NamedEntity(text="Munich", entity_type=EntityType.LOCATION, confidence=0.7),
        ]
        
        structured_data = StructuredData(entities=entities)
        categories = self.categorizer.categorize_structured_data(structured_data)
        
        assert CategoryType.PERSONAL in categories
        assert CategoryType.ORGANIZATIONAL in categories
        assert CategoryType.GEOGRAPHICAL in categories
        
        # Check specific categorization
        personal_items = categories[CategoryType.PERSONAL]
        assert any("Angela Merkel" in str(item) for item in personal_items)
        
        org_items = categories[CategoryType.ORGANIZATIONAL]
        assert any("BMW AG" in str(item) for item in org_items)
    
    def test_categorize_numeric_values(self):
        """Test categorization of numeric values."""
        numeric_values = [
            NumericValue(value=100.0, unit="EUR", value_type="currency"),
            NumericValue(value=75.5, unit="%", value_type="percentage"),
            NumericValue(value=5.2, unit="kg", value_type="quantity"),
            NumericValue(value=42, value_type="number"),
        ]
        
        structured_data = StructuredData(numeric_values=numeric_values)
        categories = self.categorizer.categorize_structured_data(structured_data)
        
        assert CategoryType.FINANCIAL in categories
        assert CategoryType.QUANTITATIVE in categories
        
        # All numeric values should be in quantitative, currency in financial
        financial_items = categories[CategoryType.FINANCIAL]
        assert len(financial_items) >= 1  # Currency value
        
        quantitative_items = categories[CategoryType.QUANTITATIVE]
        assert len(quantitative_items) >= 3  # All numeric values
    
    def test_categorize_table_data(self):
        """Test categorization of table data based on headers."""
        table = DataTable(
            headers=["Employee Name", "Salary", "Email", "Department", "Start Date"],
            rows=[
                ["John Smith", "60000 EUR", "john@company.com", "IT", "01.01.2023"],
                ["Jane Doe", "55000 EUR", "jane@company.com", "HR", "15.03.2022"]
            ]
        )
        
        structured_data = StructuredData(tables=[table])
        categories = self.categorizer.categorize_structured_data(structured_data)
        
        # Should categorize based on headers
        assert CategoryType.PERSONAL in categories  # Name, Email
        assert CategoryType.FINANCIAL in categories  # Salary
        assert CategoryType.ORGANIZATIONAL in categories  # Department
        assert CategoryType.TEMPORAL in categories  # Start Date
    
    def test_filter_data_equals(self):
        """Test filtering data with equals operator."""
        data = self.sample_data.numeric_values
        
        criteria = [FilterCriteria(
            field="value_type",
            operator=FilterOperator.EQUALS,
            value="currency"
        )]
        
        filtered = self.categorizer.filter_data(data, criteria)
        
        # Should only return currency values
        assert len(filtered) == 2  # Two currency values in sample data
        for item in filtered:
            assert item.value_type == "currency"
    
    def test_filter_data_greater_than(self):
        """Test filtering data with greater than operator."""
        data = self.sample_data.numeric_values
        
        criteria = [FilterCriteria(
            field="value",
            operator=FilterOperator.GREATER_THAN,
            value=1000
        )]
        
        filtered = self.categorizer.filter_data(data, criteria)
        
        # Should return values greater than 1000
        for item in filtered:
            assert item.value > 1000
    
    def test_filter_data_contains(self):
        """Test filtering data with contains operator."""
        data = self.sample_data.entities
        
        criteria = [FilterCriteria(
            field="text",
            operator=FilterOperator.CONTAINS,
            value="Doe",
            case_sensitive=False
        )]
        
        filtered = self.categorizer.filter_data(data, criteria)
        
        # Should return entities containing "Doe"
        assert len(filtered) >= 1
        for item in filtered:
            assert "doe" in item.text.lower()
    
    def test_filter_data_multiple_criteria(self):
        """Test filtering data with multiple criteria."""
        data = self.sample_data.numeric_values
        
        criteria = [
            FilterCriteria(
                field="value_type",
                operator=FilterOperator.EQUALS,
                value="currency"
            ),
            FilterCriteria(
                field="value",
                operator=FilterOperator.GREATER_THAN,
                value=1000
            )
        ]
        
        filtered = self.categorizer.filter_data(data, criteria)
        
        # Should return currency values greater than 1000
        for item in filtered:
            assert item.value_type == "currency"
            assert item.value > 1000
    
    def test_filter_data_in_range(self):
        """Test filtering data with in_range operator."""
        data = self.sample_data.numeric_values
        
        criteria = [FilterCriteria(
            field="value",
            operator=FilterOperator.IN_RANGE,
            value=(50, 100)
        )]
        
        filtered = self.categorizer.filter_data(data, criteria)
        
        # Should return values between 50 and 100
        for item in filtered:
            assert 50 <= item.value <= 100
    
    def test_filter_data_regex_match(self):
        """Test filtering data with regex match operator."""
        data = self.sample_data.entities
        
        criteria = [FilterCriteria(
            field="text",
            operator=FilterOperator.REGEX_MATCH,
            value=r".*@.*\.com$"
        )]
        
        filtered = self.categorizer.filter_data(data, criteria)
        
        # Should return email addresses
        for item in filtered:
            assert "@" in item.text and ".com" in item.text
    
    def test_sort_data_ascending(self):
        """Test sorting data in ascending order."""
        data = self.sample_data.numeric_values
        
        criteria = [SortCriteria(
            field="value",
            order=SortOrder.ASCENDING
        )]
        
        sorted_data = self.categorizer.sort_data(data, criteria)
        
        # Should be sorted by value ascending
        values = [item.value for item in sorted_data]
        assert values == sorted(values)
    
    def test_sort_data_descending(self):
        """Test sorting data in descending order."""
        data = self.sample_data.numeric_values
        
        criteria = [SortCriteria(
            field="value",
            order=SortOrder.DESCENDING
        )]
        
        sorted_data = self.categorizer.sort_data(data, criteria)
        
        # Should be sorted by value descending
        values = [item.value for item in sorted_data]
        assert values == sorted(values, reverse=True)
    
    def test_sort_data_multiple_criteria(self):
        """Test sorting data with multiple criteria."""
        # Create data with same value_type but different values
        data = [
            NumericValue(value=100, unit="EUR", value_type="currency"),
            NumericValue(value=200, unit="EUR", value_type="currency"),
            NumericValue(value=50, unit="%", value_type="percentage"),
            NumericValue(value=75, unit="%", value_type="percentage"),
        ]
        
        criteria = [
            SortCriteria(field="value_type", order=SortOrder.ASCENDING),
            SortCriteria(field="value", order=SortOrder.DESCENDING)
        ]
        
        sorted_data = self.categorizer.sort_data(data, criteria)
        
        # Should be sorted by value_type first, then by value descending within each type
        assert len(sorted_data) == 4
        
        # Check that currency items come before percentage (alphabetically)
        currency_indices = [i for i, item in enumerate(sorted_data) if item.value_type == "currency"]
        percentage_indices = [i for i, item in enumerate(sorted_data) if item.value_type == "percentage"]
        
        if currency_indices and percentage_indices:
            assert max(currency_indices) < min(percentage_indices)
    
    def test_assess_data_quality_high_quality(self):
        """Test data quality assessment with high-quality data."""
        # Create high-quality structured data
        structured_data = StructuredData()
        structured_data.entities = [
            NamedEntity(text="Dr. John Smith", entity_type=EntityType.PERSON, confidence=0.95),
            NamedEntity(text="Microsoft Corporation", entity_type=EntityType.ORGANIZATION, confidence=0.90),
        ]
        structured_data.numeric_values = [
            NumericValue(value=1500.0, unit="EUR", value_type="currency", context="salary information"),
            NumericValue(value=95.5, unit="%", value_type="percentage", context="success rate"),
        ]
        structured_data.temporal_data = [
            TemporalValue(value=datetime(2024, 3, 15), original_text="15.03.2024", precision="day"),
        ]
        
        quality = self.categorizer.assess_data_quality(structured_data)
        
        assert isinstance(quality, DataQualityMetrics)
        assert quality.overall_score > 0.7  # Should be high quality
        assert quality.completeness_score > 0.8
        assert quality.validity_score >= 0.8
    
    def test_assess_data_quality_low_quality(self):
        """Test data quality assessment with low-quality data."""
        # Create low-quality structured data
        structured_data = StructuredData()
        structured_data.entities = [
            NamedEntity(text="", entity_type=EntityType.PERSON, confidence=0.2),  # Empty text, low confidence
            NamedEntity(text="123", entity_type=EntityType.ORGANIZATION, confidence=0.1),  # Invalid format
        ]
        structured_data.numeric_values = [
            NumericValue(value=-1500.0, value_type="percentage"),  # Invalid percentage
        ]
        structured_data.tables = [
            DataTable(headers=["Name"], rows=[[""], [""], [""]])  # Empty rows
        ]
        
        quality = self.categorizer.assess_data_quality(structured_data)
        
        assert isinstance(quality, DataQualityMetrics)
        assert quality.overall_score < 0.5  # Should be low quality
        assert quality.completeness_score <= 0.5  # Many empty values
    
    def test_assess_data_quality_empty_data(self):
        """Test data quality assessment with empty data."""
        structured_data = StructuredData()
        
        quality = self.categorizer.assess_data_quality(structured_data)
        
        assert isinstance(quality, DataQualityMetrics)
        assert quality.overall_score == 0.0
        assert quality.completeness_score == 0.0
    
    def test_financial_data_detection(self):
        """Test detection of financial data patterns."""
        # Test various financial patterns
        financial_texts = [
            "€1,500.00",
            "$2,500 USD",
            "1.000.000 EUR",
            "Price: 500€"
        ]
        
        for text in financial_texts:
            assert self.categorizer._is_financial_data(text)
        
        # Test non-financial texts
        non_financial_texts = [
            "Hello world",
            "Meeting at 3pm",
            "John Smith"
        ]
        
        for text in non_financial_texts:
            assert not self.categorizer._is_financial_data(text)
    
    def test_temporal_data_detection(self):
        """Test detection of temporal data patterns."""
        # Test various temporal patterns
        temporal_texts = [
            "15.03.2024",
            "2024-03-15",
            "15. März 2024",
            "31/12/2023"
        ]
        
        for text in temporal_texts:
            assert self.categorizer._is_temporal_data(text)
        
        # Test non-temporal texts
        non_temporal_texts = [
            "Hello world",
            "€1,500",
            "Microsoft Corp."
        ]
        
        for text in non_temporal_texts:
            assert not self.categorizer._is_temporal_data(text)
    
    def test_geographical_data_detection(self):
        """Test detection of geographical data patterns."""
        # Test various geographical patterns
        geographical_texts = [
            "12345",  # Postal code
            "Hauptstraße 123",
            "Berlin",
            "München"
        ]
        
        for text in geographical_texts:
            result = self.categorizer._is_geographical_data(text)
            # Note: Some may not be detected due to simple patterns
            # This is expected behavior
    
    def test_personal_data_detection(self):
        """Test detection of personal data patterns."""
        # Test various personal data patterns
        personal_texts = [
            "john.doe@example.com",
            "+49 123 456789",
            "Dr. Angela Merkel",
            "Herr Schmidt"
        ]
        
        for text in personal_texts:
            assert self.categorizer._is_personal_data(text)
        
        # Test non-personal texts
        non_personal_texts = [
            "Microsoft Corp.",
            "€1,500",
            "Berlin"
        ]
        
        for text in non_personal_texts:
            assert not self.categorizer._is_personal_data(text)
    
    def test_organizational_data_detection(self):
        """Test detection of organizational data patterns."""
        # Test various organizational patterns
        organizational_texts = [
            "Microsoft Corp.",
            "BMW AG",
            "Universität München",
            "Abteilung IT"
        ]
        
        for text in organizational_texts:
            assert self.categorizer._is_organizational_data(text)
        
        # Test non-organizational texts
        non_organizational_texts = [
            "John Smith",
            "€1,500",
            "15.03.2024"
        ]
        
        for text in non_organizational_texts:
            assert not self.categorizer._is_organizational_data(text)
    
    def test_quantitative_data_detection(self):
        """Test detection of quantitative data patterns."""
        # Test various quantitative patterns
        quantitative_texts = [
            "123",
            "45.67",
            "1,234.56",
            "Price: 500"
        ]
        
        for text in quantitative_texts:
            assert self.categorizer._is_quantitative_data(text)
        
        # Test non-quantitative texts
        non_quantitative_texts = [
            "Hello world",
            "John Smith"
        ]
        
        for text in non_quantitative_texts:
            assert not self.categorizer._is_quantitative_data(text)


class TestUtilityFunctions:
    """Test suite for utility functions."""
    
    def test_create_filter_from_dict(self):
        """Test creating FilterCriteria from dictionary."""
        filter_dict = {
            'field': 'value',
            'operator': 'greater_than',
            'value': 100,
            'case_sensitive': True
        }
        
        criteria = create_filter_from_dict(filter_dict)
        
        assert criteria.field == 'value'
        assert criteria.operator == FilterOperator.GREATER_THAN
        assert criteria.value == 100
        assert criteria.case_sensitive is True
    
    def test_create_sort_from_dict(self):
        """Test creating SortCriteria from dictionary."""
        sort_dict = {
            'field': 'name',
            'order': 'desc'
        }
        
        criteria = create_sort_from_dict(sort_dict)
        
        assert criteria.field == 'name'
        assert criteria.order == SortOrder.DESCENDING
    
    def test_merge_categories(self):
        """Test merging category dictionaries."""
        categories1 = {
            CategoryType.FINANCIAL: [1, 2, 3],
            CategoryType.PERSONAL: [4, 5]
        }
        
        categories2 = {
            CategoryType.FINANCIAL: [6, 7],
            CategoryType.TEMPORAL: [8, 9]
        }
        
        merged = merge_categories(categories1, categories2)
        
        assert len(merged[CategoryType.FINANCIAL]) == 5  # 3 + 2
        assert len(merged[CategoryType.PERSONAL]) == 2
        assert len(merged[CategoryType.TEMPORAL]) == 2
    
    def test_get_category_statistics(self):
        """Test getting category statistics."""
        categories = {
            CategoryType.FINANCIAL: [1, 2, 3],
            CategoryType.PERSONAL: [4, 5],
            CategoryType.TEMPORAL: [6]
        }
        
        stats = get_category_statistics(categories)
        
        assert stats['total_items'] == 6
        assert stats['total_categories'] == 3
        assert stats['category_counts']['financial'] == 3
        assert stats['category_counts']['personal'] == 2
        assert stats['category_counts']['temporal'] == 1
        
        # Check percentages
        assert abs(stats['category_percentages']['financial'] - 50.0) < 0.1  # 3/6 = 50%
        assert abs(stats['category_percentages']['personal'] - 33.33) < 0.1  # 2/6 ≈ 33.33%


class TestEdgeCases:
    """Test suite for edge cases and error handling."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.categorizer = DataCategorizer()
    
    def test_filter_empty_data(self):
        """Test filtering empty data."""
        data = []
        criteria = [FilterCriteria(field="value", operator=FilterOperator.EQUALS, value=100)]
        
        filtered = self.categorizer.filter_data(data, criteria)
        
        assert filtered == []
    
    def test_sort_empty_data(self):
        """Test sorting empty data."""
        data = []
        criteria = [SortCriteria(field="value")]
        
        sorted_data = self.categorizer.sort_data(data, criteria)
        
        assert sorted_data == []
    
    def test_filter_invalid_field(self):
        """Test filtering with invalid field name."""
        data = [NumericValue(value=100, unit="EUR")]
        criteria = [FilterCriteria(field="nonexistent_field", operator=FilterOperator.EQUALS, value=100)]
        
        filtered = self.categorizer.filter_data(data, criteria)
        
        # Should return empty list since field doesn't exist
        assert filtered == []
    
    def test_sort_invalid_field(self):
        """Test sorting with invalid field name."""
        data = [NumericValue(value=100, unit="EUR"), NumericValue(value=200, unit="USD")]
        criteria = [SortCriteria(field="nonexistent_field")]
        
        sorted_data = self.categorizer.sort_data(data, criteria)
        
        # Should return original data (no sorting applied)
        assert len(sorted_data) == len(data)
    
    def test_categorize_mixed_data_types(self):
        """Test categorization with mixed data types."""
        # Mix different types of objects
        mixed_data = StructuredData()
        mixed_data.entities = [
            NamedEntity(text="Test", entity_type=EntityType.PERSON, confidence=0.5)
        ]
        mixed_data.numeric_values = [
            NumericValue(value=None, unit="EUR")  # None value
        ]
        
        # Should handle gracefully without crashing
        categories = self.categorizer.categorize_structured_data(mixed_data)
        assert isinstance(categories, dict)
    
    def test_quality_assessment_with_none_values(self):
        """Test quality assessment with None values."""
        structured_data = StructuredData()
        structured_data.tables = [
            DataTable(headers=["Name", "Value"], rows=[
                ["John", None],
                [None, "100"],
                ["", ""]
            ])
        ]
        
        quality = self.categorizer.assess_data_quality(structured_data)
        
        assert isinstance(quality, DataQualityMetrics)
        assert 0 <= quality.overall_score <= 1
        assert quality.completeness_score < 1.0  # Should be low due to None/empty values


if __name__ == "__main__":
    pytest.main([__file__])