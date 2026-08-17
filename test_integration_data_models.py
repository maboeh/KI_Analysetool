"""
Integration tests for data models.

This module tests how the data models work together in realistic scenarios
to ensure proper integration and workflow functionality.
"""

import unittest
from datetime import datetime
from data_models import (
    ProcessedResult, StructuredData, SourceInfo, NamedEntity, NumericValue,
    TemporalValue, DataTable, Action, ResultMetadata, Visualization, ChartConfig,
    ActionType, ChartType, EntityType,
    create_default_actions, create_source_info_from_path
)


class TestDataModelIntegration(unittest.TestCase):
    """Test integration between different data model components."""
    
    def test_complete_analysis_workflow(self):
        """Test a complete analysis workflow using all data models."""
        # 1. Create source information
        source = create_source_info_from_path("https://example.com/article")
        
        # 2. Create extracted entities
        entities = [
            NamedEntity("Berlin", EntityType.LOCATION, 0.95),
            NamedEntity("Google Inc.", EntityType.ORGANIZATION, 0.88),
            NamedEntity("John Smith", EntityType.PERSON, 0.92)
        ]
        
        # 3. Create numeric values
        numeric_values = [
            NumericValue(1000, "EUR", "Revenue", "currency"),
            NumericValue(25.5, "%", "Growth rate", "percentage"),
            NumericValue(150, "units", "Quantity sold", "quantity")
        ]
        
        # 4. Create a data table
        table = DataTable(
            headers=["Product", "Sales", "Region"],
            rows=[
                ["Laptop", "500", "Europe"],
                ["Phone", "300", "Asia"],
                ["Tablet", "200", "America"]
            ],
            title="Sales Data"
        )
        
        # 5. Create structured data container
        structured_data = StructuredData(
            entities=entities,
            numeric_values=numeric_values,
            tables=[table],
            categories={"products": ["Laptop", "Phone", "Tablet"]}
        )
        
        # 6. Create visualization
        chart_config = ChartConfig(
            title="Sales by Region",
            x_label="Region",
            y_label="Sales",
            colors=["blue", "green", "red"]
        )
        visualization = Visualization(
            chart_type=ChartType.BAR,
            data_source="sales_table",
            config=chart_config,
            interactive=True
        )
        
        # 7. Create follow-up actions
        actions = create_default_actions()
        
        # 8. Create metadata
        metadata = ResultMetadata(
            analysis_type="comprehensive_analysis",
            processing_time=2.5,
            model_used="gpt-4o",
            tokens_used=1500,
            confidence_score=0.89,
            tags=["sales", "analysis", "business"]
        )
        
        # 9. Create the complete processed result
        result = ProcessedResult(
            content="This is a comprehensive analysis of sales data showing strong performance in Europe...",
            source_info=source,
            extracted_data=structured_data,
            visualizations=[visualization],
            follow_up_actions=actions,
            metadata=metadata
        )
        
        # Verify the complete result
        self.assertEqual(result.source_info.type, "website")
        self.assertEqual(len(result.extracted_data.entities), 3)
        self.assertEqual(len(result.extracted_data.numeric_values), 3)
        self.assertEqual(len(result.extracted_data.tables), 1)
        self.assertEqual(len(result.visualizations), 1)
        self.assertEqual(len(result.follow_up_actions), 3)
        
        # Test data capabilities
        self.assertTrue(result.has_exportable_data())
        self.assertTrue(result.has_visualizable_data())
        
        # Test serialization of complete result
        result_dict = result.to_dict()
        reconstructed = ProcessedResult.from_dict(result_dict)
        
        self.assertEqual(result.id, reconstructed.id)
        self.assertEqual(result.content, reconstructed.content)
        self.assertEqual(len(reconstructed.extracted_data.entities), 3)
        self.assertEqual(len(reconstructed.visualizations), 1)
    
    def test_excel_export_workflow(self):
        """Test the workflow for Excel export functionality."""
        # Create multiple tables for export
        sales_table = DataTable(
            headers=["Month", "Revenue", "Profit"],
            rows=[
                ["January", "10000", "2000"],
                ["February", "12000", "2400"],
                ["March", "11000", "2200"]
            ],
            title="Monthly Sales"
        )
        
        products_table = DataTable(
            headers=["Product", "Category", "Price"],
            rows=[
                ["Laptop Pro", "Electronics", "1299"],
                ["Wireless Mouse", "Accessories", "49"],
                ["Monitor 4K", "Electronics", "399"]
            ],
            title="Product Catalog"
        )
        
        structured_data = StructuredData(tables=[sales_table, products_table])
        
        result = ProcessedResult(
            content="Analysis of sales and product data",
            extracted_data=structured_data
        )
        
        # Test export capabilities
        self.assertTrue(result.has_exportable_data())
        exportable_tables = result.extracted_data.get_exportable_tables()
        self.assertEqual(len(exportable_tables), 2)
        
        # Test Excel format conversion
        for table in exportable_tables:
            excel_format = table.to_excel_format()
            self.assertIn('sheet_name', excel_format)
            self.assertIn('headers', excel_format)
            self.assertIn('data', excel_format)
            
            # Test CSV format conversion
            csv_output = table.to_csv_format()
            self.assertIsInstance(csv_output, str)
            self.assertTrue(len(csv_output) > 0)
    
    def test_visualization_workflow(self):
        """Test the workflow for creating visualizations."""
        # Create numeric data suitable for visualization
        numeric_values = [
            NumericValue(100, "units", "Q1 Sales", "quantity"),
            NumericValue(150, "units", "Q2 Sales", "quantity"),
            NumericValue(120, "units", "Q3 Sales", "quantity"),
            NumericValue(180, "units", "Q4 Sales", "quantity")
        ]
        
        # Create a table with numeric data
        quarterly_table = DataTable(
            headers=["Quarter", "Sales", "Growth"],
            rows=[
                ["Q1", "100", "5%"],
                ["Q2", "150", "50%"],
                ["Q3", "120", "-20%"],
                ["Q4", "180", "50%"]
            ],
            title="Quarterly Performance"
        )
        
        structured_data = StructuredData(
            numeric_values=numeric_values,
            tables=[quarterly_table]
        )
        
        result = ProcessedResult(
            content="Quarterly sales analysis",
            extracted_data=structured_data
        )
        
        # Verify visualization capability
        self.assertTrue(result.has_visualizable_data())
        
        # Create different types of visualizations
        bar_chart = Visualization(
            chart_type=ChartType.BAR,
            data_source="quarterly_sales",
            config=ChartConfig(title="Quarterly Sales", x_label="Quarter", y_label="Sales")
        )
        
        line_chart = Visualization(
            chart_type=ChartType.LINE,
            data_source="quarterly_growth",
            config=ChartConfig(title="Growth Trend", x_label="Quarter", y_label="Growth %")
        )
        
        pie_chart = Visualization(
            chart_type=ChartType.PIE,
            data_source="sales_distribution",
            config=ChartConfig(title="Sales Distribution")
        )
        
        # Add visualizations to result
        result.add_visualization(bar_chart)
        result.add_visualization(line_chart)
        result.add_visualization(pie_chart)
        
        self.assertEqual(len(result.visualizations), 3)
        
        # Test visualization serialization
        for viz in result.visualizations:
            viz_dict = viz.to_dict()
            self.assertIn('chart_type', viz_dict)
            self.assertIn('config', viz_dict)
    
    def test_follow_up_actions_workflow(self):
        """Test the workflow for follow-up actions."""
        # Create a result with various data types
        entities = [NamedEntity("Apple Inc.", EntityType.ORGANIZATION, 0.95)]
        numeric_values = [NumericValue(1000000, "USD", "Revenue", "currency")]
        
        structured_data = StructuredData(
            entities=entities,
            numeric_values=numeric_values
        )
        
        result = ProcessedResult(
            content="Apple Inc. reported revenue of $1,000,000 in the last quarter.",
            extracted_data=structured_data
        )
        
        # Add various follow-up actions
        summarize_action = Action(
            action_type=ActionType.SUMMARIZE,
            label="Zusammenfassen",
            description="Erstelle eine kurze Zusammenfassung",
            parameters={"length": "short", "focus": "financial"}
        )
        
        translate_action = Action(
            action_type=ActionType.TRANSLATE,
            label="Ins Deutsche übersetzen",
            description="Übersetze den Inhalt ins Deutsche",
            parameters={"target_language": "de", "preserve_numbers": True}
        )
        
        visualize_action = Action(
            action_type=ActionType.VISUALIZE,
            label="Visualisieren",
            description="Erstelle Diagramme aus den Daten",
            parameters={"chart_types": ["bar", "pie"], "auto_suggest": True}
        )
        
        export_action = Action(
            action_type=ActionType.EXPORT,
            label="Nach Excel exportieren",
            description="Exportiere strukturierte Daten nach Excel",
            parameters={"format": "xlsx", "include_charts": True}
        )
        
        # Add actions to result
        result.add_follow_up_action(summarize_action)
        result.add_follow_up_action(translate_action)
        result.add_follow_up_action(visualize_action)
        result.add_follow_up_action(export_action)
        
        self.assertEqual(len(result.follow_up_actions), 4)
        
        # Test action filtering by type
        export_actions = [a for a in result.follow_up_actions if a.action_type == ActionType.EXPORT]
        self.assertEqual(len(export_actions), 1)
        
        visualize_actions = [a for a in result.follow_up_actions if a.action_type == ActionType.VISUALIZE]
        self.assertEqual(len(visualize_actions), 1)
    
    def test_multi_source_analysis(self):
        """Test analysis workflow with multiple source types."""
        # Test different source types
        sources = [
            create_source_info_from_path("https://www.youtube.com/watch?v=test"),
            create_source_info_from_path("https://example.com/article"),
            create_source_info_from_path("/path/to/document.pdf"),
            create_source_info_from_path("/path/to/data.xlsx"),
            create_source_info_from_path("/path/to/image.png")
        ]
        
        expected_types = ["youtube", "website", "pdf", "excel", "image"]
        
        for source, expected_type in zip(sources, expected_types):
            self.assertEqual(source.type, expected_type)
            
            # Create a result for each source type
            result = ProcessedResult(
                content=f"Analysis from {expected_type} source",
                source_info=source,
                metadata=ResultMetadata(analysis_type=f"{expected_type}_analysis")
            )
            
            self.assertEqual(result.source_info.type, expected_type)
            self.assertEqual(result.metadata.analysis_type, f"{expected_type}_analysis")
    
    def test_data_model_extensibility(self):
        """Test that the data models support extensibility through interfaces."""
        # Test that all extractable classes implement the interface
        entity = NamedEntity("Test", EntityType.PERSON, 0.9)
        numeric = NumericValue(100, "EUR")
        temporal = TemporalValue(datetime.now(), "now", "minute")
        table = DataTable(["Col1"], [["Value1"]])
        
        extractables = [entity, numeric, temporal, table]
        
        # All should implement to_dict
        for extractable in extractables:
            result_dict = extractable.to_dict()
            self.assertIsInstance(result_dict, dict)
            self.assertTrue(len(result_dict) > 0)
        
        # Test that exportable classes implement the interface
        exportables = [table]  # Only DataTable implements Exportable currently
        
        for exportable in exportables:
            excel_format = exportable.to_excel_format()
            csv_format = exportable.to_csv_format()
            
            self.assertIsInstance(excel_format, dict)
            self.assertIsInstance(csv_format, str)
    
    def test_error_handling_and_validation(self):
        """Test error handling and data validation."""
        # Test with minimal data
        minimal_result = ProcessedResult()
        
        self.assertIsNotNone(minimal_result.id)
        self.assertIsInstance(minimal_result.created_at, datetime)
        self.assertFalse(minimal_result.has_exportable_data())
        self.assertFalse(minimal_result.has_visualizable_data())
        
        # Test serialization with minimal data
        minimal_dict = minimal_result.to_dict()
        reconstructed = ProcessedResult.from_dict(minimal_dict)
        
        self.assertEqual(minimal_result.id, reconstructed.id)
        
        # Test with empty structured data
        empty_structured = StructuredData()
        self.assertEqual(len(empty_structured.tables), 0)
        self.assertEqual(len(empty_structured.entities), 0)
        self.assertFalse(empty_structured.has_visualizable_data())
        
        # Test serialization roundtrip with empty data
        empty_dict = empty_structured.to_dict()
        reconstructed_structured = StructuredData.from_dict(empty_dict)
        
        self.assertEqual(len(reconstructed_structured.tables), 0)
        self.assertEqual(len(reconstructed_structured.entities), 0)


if __name__ == '__main__':
    unittest.main()