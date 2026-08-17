"""
Unit tests for core data models.

This module contains comprehensive tests for all data model classes
to ensure proper functionality, serialization, and validation.
"""

import unittest
from datetime import datetime
from data_models import (
    ProcessedResult, StructuredData, SourceInfo, NamedEntity, NumericValue,
    TemporalValue, DataTable, DataRelationship, Visualization, Action,
    ResultMetadata, ChartConfig, ResultSummary, ExtractedContent,
    ActionType, ChartType, EntityType, DataType,
    create_default_actions, create_source_info_from_path
)


class TestEnums(unittest.TestCase):
    """Test enum classes."""
    
    def test_action_type_enum(self):
        """Test ActionType enum values."""
        self.assertEqual(ActionType.SUMMARIZE.value, "zusammenfassen")
        self.assertEqual(ActionType.DEEPEN.value, "vertiefen")
        self.assertEqual(ActionType.TRANSLATE.value, "übersetzen")
        self.assertEqual(ActionType.ANALYZE.value, "analysieren")
        self.assertEqual(ActionType.EXPORT.value, "exportieren")
        self.assertEqual(ActionType.VISUALIZE.value, "visualisieren")
    
    def test_chart_type_enum(self):
        """Test ChartType enum values."""
        self.assertEqual(ChartType.BAR.value, "bar")
        self.assertEqual(ChartType.LINE.value, "line")
        self.assertEqual(ChartType.PIE.value, "pie")
        self.assertEqual(ChartType.SCATTER.value, "scatter")
        self.assertEqual(ChartType.HISTOGRAM.value, "histogram")
        self.assertEqual(ChartType.HEATMAP.value, "heatmap")
    
    def test_entity_type_enum(self):
        """Test EntityType enum values."""
        self.assertEqual(EntityType.PERSON.value, "person")
        self.assertEqual(EntityType.ORGANIZATION.value, "organization")
        self.assertEqual(EntityType.LOCATION.value, "location")
        self.assertEqual(EntityType.DATE.value, "date")
        self.assertEqual(EntityType.MONEY.value, "money")
        self.assertEqual(EntityType.PERCENTAGE.value, "percentage")
        self.assertEqual(EntityType.QUANTITY.value, "quantity")


class TestSourceInfo(unittest.TestCase):
    """Test SourceInfo data class."""
    
    def test_source_info_creation(self):
        """Test creating SourceInfo instances."""
        source = SourceInfo(
            type="youtube",
            url="https://www.youtube.com/watch?v=test",
            file_name="test.mp4"
        )
        
        self.assertEqual(source.type, "youtube")
        self.assertEqual(source.url, "https://www.youtube.com/watch?v=test")
        self.assertEqual(source.file_name, "test.mp4")
        self.assertIsNone(source.file_path)
    
    def test_source_info_to_dict(self):
        """Test SourceInfo serialization to dictionary."""
        source = SourceInfo(
            type="pdf",
            file_path="/path/to/file.pdf",
            file_name="file.pdf",
            file_size=1024
        )
        
        expected = {
            'type': 'pdf',
            'url': None,
            'file_path': '/path/to/file.pdf',
            'file_name': 'file.pdf',
            'file_size': 1024,
            'encoding': None
        }
        
        self.assertEqual(source.to_dict(), expected)


class TestNamedEntity(unittest.TestCase):
    """Test NamedEntity data class."""
    
    def test_named_entity_creation(self):
        """Test creating NamedEntity instances."""
        entity = NamedEntity(
            text="John Doe",
            entity_type=EntityType.PERSON,
            confidence=0.95,
            start_pos=0,
            end_pos=8
        )
        
        self.assertEqual(entity.text, "John Doe")
        self.assertEqual(entity.entity_type, EntityType.PERSON)
        self.assertEqual(entity.confidence, 0.95)
        self.assertEqual(entity.start_pos, 0)
        self.assertEqual(entity.end_pos, 8)
    
    def test_named_entity_serialization(self):
        """Test NamedEntity to_dict and from_dict methods."""
        entity = NamedEntity(
            text="Berlin",
            entity_type=EntityType.LOCATION,
            confidence=0.88
        )
        
        entity_dict = entity.to_dict()
        reconstructed = NamedEntity.from_dict(entity_dict)
        
        self.assertEqual(entity.text, reconstructed.text)
        self.assertEqual(entity.entity_type, reconstructed.entity_type)
        self.assertEqual(entity.confidence, reconstructed.confidence)


class TestNumericValue(unittest.TestCase):
    """Test NumericValue data class."""
    
    def test_numeric_value_creation(self):
        """Test creating NumericValue instances."""
        value = NumericValue(
            value=100.50,
            unit="EUR",
            context="Preis für Produkt",
            value_type="currency"
        )
        
        self.assertEqual(value.value, 100.50)
        self.assertEqual(value.unit, "EUR")
        self.assertEqual(value.context, "Preis für Produkt")
        self.assertEqual(value.value_type, "currency")
    
    def test_numeric_value_serialization(self):
        """Test NumericValue to_dict and from_dict methods."""
        value = NumericValue(value=75, unit="%", value_type="percentage")
        
        value_dict = value.to_dict()
        reconstructed = NumericValue.from_dict(value_dict)
        
        self.assertEqual(value.value, reconstructed.value)
        self.assertEqual(value.unit, reconstructed.unit)
        self.assertEqual(value.value_type, reconstructed.value_type)


class TestTemporalValue(unittest.TestCase):
    """Test TemporalValue data class."""
    
    def test_temporal_value_creation(self):
        """Test creating TemporalValue instances."""
        test_date = datetime(2024, 1, 15, 10, 30)
        temporal = TemporalValue(
            value=test_date,
            original_text="15. Januar 2024",
            precision="day"
        )
        
        self.assertEqual(temporal.value, test_date)
        self.assertEqual(temporal.original_text, "15. Januar 2024")
        self.assertEqual(temporal.precision, "day")
    
    def test_temporal_value_serialization(self):
        """Test TemporalValue to_dict and from_dict methods."""
        test_date = datetime(2024, 6, 1, 14, 0)
        temporal = TemporalValue(
            value=test_date,
            original_text="1. Juni 2024",
            precision="day"
        )
        
        temporal_dict = temporal.to_dict()
        reconstructed = TemporalValue.from_dict(temporal_dict)
        
        self.assertEqual(temporal.value, reconstructed.value)
        self.assertEqual(temporal.original_text, reconstructed.original_text)
        self.assertEqual(temporal.precision, reconstructed.precision)


class TestDataTable(unittest.TestCase):
    """Test DataTable data class."""
    
    def test_data_table_creation(self):
        """Test creating DataTable instances."""
        table = DataTable(
            headers=["Name", "Age", "City"],
            rows=[
                ["Alice", "25", "Berlin"],
                ["Bob", "30", "Munich"]
            ],
            title="User Data"
        )
        
        self.assertEqual(table.headers, ["Name", "Age", "City"])
        self.assertEqual(len(table.rows), 2)
        self.assertEqual(table.title, "User Data")
    
    def test_data_table_serialization(self):
        """Test DataTable to_dict and from_dict methods."""
        table = DataTable(
            headers=["Product", "Price"],
            rows=[["Laptop", "999"], ["Mouse", "25"]]
        )
        
        table_dict = table.to_dict()
        reconstructed = DataTable.from_dict(table_dict)
        
        self.assertEqual(table.headers, reconstructed.headers)
        self.assertEqual(table.rows, reconstructed.rows)
    
    def test_data_table_excel_export(self):
        """Test DataTable Excel export format."""
        table = DataTable(
            headers=["Item", "Quantity"],
            rows=[["Apples", "10"], ["Oranges", "5"]],
            title="Inventory"
        )
        
        excel_format = table.to_excel_format()
        
        self.assertEqual(excel_format['sheet_name'], "Inventory")
        self.assertEqual(excel_format['headers'], ["Item", "Quantity"])
        self.assertEqual(excel_format['data'], [["Apples", "10"], ["Oranges", "5"]])
    
    def test_data_table_csv_export(self):
        """Test DataTable CSV export format."""
        table = DataTable(
            headers=["Name", "Score"],
            rows=[["Alice", "95"], ["Bob", "87"]]
        )
        
        csv_output = table.to_csv_format()
        
        self.assertIn("Name,Score", csv_output)
        self.assertIn("Alice,95", csv_output)
        self.assertIn("Bob,87", csv_output)


class TestStructuredData(unittest.TestCase):
    """Test StructuredData data class."""
    
    def setUp(self):
        """Set up test data."""
        self.entity = NamedEntity("Test Entity", EntityType.PERSON, 0.9)
        self.numeric = NumericValue(100, "EUR", "Test value", "currency")
        self.table = DataTable(["Col1", "Col2"], [["A", "B"]])
        
    def test_structured_data_creation(self):
        """Test creating StructuredData instances."""
        data = StructuredData(
            entities=[self.entity],
            numeric_values=[self.numeric],
            tables=[self.table]
        )
        
        self.assertEqual(len(data.entities), 1)
        self.assertEqual(len(data.numeric_values), 1)
        self.assertEqual(len(data.tables), 1)
    
    def test_structured_data_serialization(self):
        """Test StructuredData to_dict and from_dict methods."""
        data = StructuredData(
            entities=[self.entity],
            numeric_values=[self.numeric],
            categories={"test": ["item1", "item2"]}
        )
        
        data_dict = data.to_dict()
        reconstructed = StructuredData.from_dict(data_dict)
        
        self.assertEqual(len(reconstructed.entities), 1)
        self.assertEqual(len(reconstructed.numeric_values), 1)
        self.assertEqual(reconstructed.categories, {"test": ["item1", "item2"]})
    
    def test_has_visualizable_data(self):
        """Test has_visualizable_data method."""
        # Empty data should not be visualizable
        empty_data = StructuredData()
        self.assertFalse(empty_data.has_visualizable_data())
        
        # Data with numeric values should be visualizable
        data_with_numbers = StructuredData(numeric_values=[self.numeric])
        self.assertTrue(data_with_numbers.has_visualizable_data())
        
        # Data with tables should be visualizable
        data_with_tables = StructuredData(tables=[self.table])
        self.assertTrue(data_with_tables.has_visualizable_data())
    
    def test_get_exportable_tables(self):
        """Test get_exportable_tables method."""
        data = StructuredData(tables=[self.table])
        exportable = data.get_exportable_tables()
        
        self.assertEqual(len(exportable), 1)
        self.assertEqual(exportable[0], self.table)


class TestVisualization(unittest.TestCase):
    """Test Visualization data class."""
    
    def test_visualization_creation(self):
        """Test creating Visualization instances."""
        config = ChartConfig(title="Test Chart", x_label="X", y_label="Y")
        viz = Visualization(
            chart_type=ChartType.BAR,
            data_source="test_data",
            config=config,
            interactive=True
        )
        
        self.assertEqual(viz.chart_type, ChartType.BAR)
        self.assertEqual(viz.data_source, "test_data")
        self.assertTrue(viz.interactive)
        self.assertIsNotNone(viz.id)  # Should have auto-generated ID
    
    def test_visualization_serialization(self):
        """Test Visualization to_dict method."""
        viz = Visualization(chart_type=ChartType.LINE, data_source="line_data")
        viz_dict = viz.to_dict()
        
        self.assertEqual(viz_dict['chart_type'], 'line')
        self.assertEqual(viz_dict['data_source'], 'line_data')
        self.assertIn('id', viz_dict)


class TestAction(unittest.TestCase):
    """Test Action data class."""
    
    def test_action_creation(self):
        """Test creating Action instances."""
        action = Action(
            action_type=ActionType.SUMMARIZE,
            label="Zusammenfassen",
            description="Erstelle eine Zusammenfassung",
            parameters={"length": "short"},
            enabled=True
        )
        
        self.assertEqual(action.action_type, ActionType.SUMMARIZE)
        self.assertEqual(action.label, "Zusammenfassen")
        self.assertEqual(action.parameters["length"], "short")
        self.assertTrue(action.enabled)
    
    def test_action_serialization(self):
        """Test Action to_dict method."""
        action = Action(
            action_type=ActionType.TRANSLATE,
            label="Übersetzen",
            description="Übersetze den Text"
        )
        
        action_dict = action.to_dict()
        
        self.assertEqual(action_dict['action_type'], 'übersetzen')
        self.assertEqual(action_dict['label'], 'Übersetzen')
        self.assertEqual(action_dict['enabled'], True)


class TestProcessedResult(unittest.TestCase):
    """Test ProcessedResult data class."""
    
    def setUp(self):
        """Set up test data."""
        self.source_info = SourceInfo(type="website", url="https://example.com")
        self.structured_data = StructuredData()
        self.metadata = ResultMetadata(analysis_type="summary")
    
    def test_processed_result_creation(self):
        """Test creating ProcessedResult instances."""
        result = ProcessedResult(
            content="Test analysis result",
            source_info=self.source_info,
            extracted_data=self.structured_data,
            metadata=self.metadata
        )
        
        self.assertEqual(result.content, "Test analysis result")
        self.assertEqual(result.source_info.type, "website")
        self.assertIsNotNone(result.id)  # Should have auto-generated ID
        self.assertIsInstance(result.created_at, datetime)
    
    def test_processed_result_serialization(self):
        """Test ProcessedResult to_dict and from_dict methods."""
        result = ProcessedResult(
            content="Test content",
            source_info=self.source_info,
            metadata=self.metadata
        )
        
        result_dict = result.to_dict()
        reconstructed = ProcessedResult.from_dict(result_dict)
        
        self.assertEqual(result.content, reconstructed.content)
        self.assertEqual(result.id, reconstructed.id)
        self.assertEqual(result.source_info.type, reconstructed.source_info.type)
    
    def test_processed_result_methods(self):
        """Test ProcessedResult utility methods."""
        result = ProcessedResult()
        
        # Test timestamp update
        original_time = result.updated_at
        result.update_timestamp()
        self.assertGreater(result.updated_at, original_time)
        
        # Test adding visualization
        viz = Visualization(chart_type=ChartType.PIE, data_source="test")
        result.add_visualization(viz)
        self.assertEqual(len(result.visualizations), 1)
        
        # Test adding action
        action = Action(ActionType.SUMMARIZE, "Test", "Test action")
        result.add_follow_up_action(action)
        self.assertEqual(len(result.follow_up_actions), 1)
    
    def test_has_exportable_data(self):
        """Test has_exportable_data method."""
        result = ProcessedResult()
        
        # Initially should have no exportable data
        self.assertFalse(result.has_exportable_data())
        
        # Add a table to make it exportable
        table = DataTable(["Col1"], [["Value1"]])
        result.extracted_data.tables.append(table)
        self.assertTrue(result.has_exportable_data())
    
    def test_has_visualizable_data(self):
        """Test has_visualizable_data method."""
        result = ProcessedResult()
        
        # Initially should have no visualizable data
        self.assertFalse(result.has_visualizable_data())
        
        # Add numeric data to make it visualizable
        numeric = NumericValue(42, "units")
        result.extracted_data.numeric_values.append(numeric)
        self.assertTrue(result.has_visualizable_data())


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions."""
    
    def test_create_default_actions(self):
        """Test create_default_actions function."""
        actions = create_default_actions()
        
        self.assertEqual(len(actions), 3)
        
        action_types = [action.action_type for action in actions]
        self.assertIn(ActionType.SUMMARIZE, action_types)
        self.assertIn(ActionType.DEEPEN, action_types)
        self.assertIn(ActionType.TRANSLATE, action_types)
    
    def test_create_source_info_from_path(self):
        """Test create_source_info_from_path function."""
        # Test YouTube URL
        youtube_source = create_source_info_from_path("https://www.youtube.com/watch?v=test")
        self.assertEqual(youtube_source.type, "youtube")
        self.assertEqual(youtube_source.url, "https://www.youtube.com/watch?v=test")
        
        # Test website URL
        website_source = create_source_info_from_path("https://example.com")
        self.assertEqual(website_source.type, "website")
        self.assertEqual(website_source.url, "https://example.com")
        
        # Test PDF file
        pdf_source = create_source_info_from_path("/path/to/file.pdf")
        self.assertEqual(pdf_source.type, "pdf")
        self.assertEqual(pdf_source.file_path, "/path/to/file.pdf")
        self.assertEqual(pdf_source.file_name, "file.pdf")
        
        # Test Excel file
        excel_source = create_source_info_from_path("/path/to/data.xlsx")
        self.assertEqual(excel_source.type, "excel")
        self.assertEqual(excel_source.file_name, "data.xlsx")
        
        # Test CSV file
        csv_source = create_source_info_from_path("/path/to/data.csv")
        self.assertEqual(csv_source.type, "csv")
        
        # Test image file
        image_source = create_source_info_from_path("/path/to/image.png")
        self.assertEqual(image_source.type, "image")


class TestDataRelationship(unittest.TestCase):
    """Test DataRelationship data class."""
    
    def test_data_relationship_creation(self):
        """Test creating DataRelationship instances."""
        relationship = DataRelationship(
            source="Entity A",
            target="Entity B",
            relationship_type="related_to",
            confidence=0.85
        )
        
        self.assertEqual(relationship.source, "Entity A")
        self.assertEqual(relationship.target, "Entity B")
        self.assertEqual(relationship.relationship_type, "related_to")
        self.assertEqual(relationship.confidence, 0.85)
    
    def test_data_relationship_serialization(self):
        """Test DataRelationship to_dict method."""
        relationship = DataRelationship("A", "B", "connects", 0.9)
        relationship_dict = relationship.to_dict()
        
        expected = {
            'source': 'A',
            'target': 'B',
            'relationship_type': 'connects',
            'confidence': 0.9
        }
        
        self.assertEqual(relationship_dict, expected)


class TestChartConfig(unittest.TestCase):
    """Test ChartConfig data class."""
    
    def test_chart_config_creation(self):
        """Test creating ChartConfig instances."""
        config = ChartConfig(
            title="Test Chart",
            x_label="X Axis",
            y_label="Y Axis",
            colors=["red", "blue"],
            style="seaborn",
            size=(12, 8)
        )
        
        self.assertEqual(config.title, "Test Chart")
        self.assertEqual(config.x_label, "X Axis")
        self.assertEqual(config.colors, ["red", "blue"])
        self.assertEqual(config.size, (12, 8))
    
    def test_chart_config_serialization(self):
        """Test ChartConfig to_dict method."""
        config = ChartConfig(title="My Chart", size=(10, 6))
        config_dict = config.to_dict()
        
        self.assertEqual(config_dict['title'], "My Chart")
        self.assertEqual(config_dict['size'], (10, 6))


class TestResultSummary(unittest.TestCase):
    """Test ResultSummary data class."""
    
    def test_result_summary_creation(self):
        """Test creating ResultSummary instances."""
        test_date = datetime(2024, 1, 1)
        summary = ResultSummary(
            id="test-id",
            title="Test Analysis",
            analysis_type="summary",
            source_type="website",
            created_at=test_date,
            has_visualizations=True,
            has_exportable_data=False
        )
        
        self.assertEqual(summary.id, "test-id")
        self.assertEqual(summary.title, "Test Analysis")
        self.assertTrue(summary.has_visualizations)
        self.assertFalse(summary.has_exportable_data)
    
    def test_result_summary_serialization(self):
        """Test ResultSummary to_dict method."""
        test_date = datetime(2024, 6, 15)
        summary = ResultSummary(
            id="summary-1",
            title="Summary Test",
            analysis_type="keyword",
            source_type="pdf",
            created_at=test_date,
            has_visualizations=False,
            has_exportable_data=True
        )
        
        summary_dict = summary.to_dict()
        
        self.assertEqual(summary_dict['id'], "summary-1")
        self.assertEqual(summary_dict['title'], "Summary Test")
        self.assertEqual(summary_dict['created_at'], test_date.isoformat())


class TestExtractedContent(unittest.TestCase):
    """Test ExtractedContent data class."""
    
    def test_extracted_content_creation(self):
        """Test creating ExtractedContent instances."""
        structured_data = StructuredData()
        content = ExtractedContent(
            text="Extracted text content",
            metadata={"source": "test", "length": 100},
            structured_data=structured_data
        )
        
        self.assertEqual(content.text, "Extracted text content")
        self.assertEqual(content.metadata["source"], "test")
        self.assertEqual(content.structured_data, structured_data)
    
    def test_extracted_content_serialization(self):
        """Test ExtractedContent to_dict method."""
        content = ExtractedContent(
            text="Test text",
            metadata={"key": "value"}
        )
        
        content_dict = content.to_dict()
        
        self.assertEqual(content_dict['text'], "Test text")
        self.assertEqual(content_dict['metadata'], {"key": "value"})
        self.assertIsNone(content_dict['structured_data'])


if __name__ == '__main__':
    unittest.main()