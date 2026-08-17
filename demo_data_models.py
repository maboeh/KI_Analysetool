"""
Demonstration script for the core data models.

This script shows how to use the data models in practice and demonstrates
the key functionality and workflows.
"""

from datetime import datetime
from data_models import (
    ProcessedResult, StructuredData, SourceInfo, NamedEntity, NumericValue,
    TemporalValue, DataTable, Action, ResultMetadata, Visualization, ChartConfig,
    ActionType, ChartType, EntityType,
    create_default_actions, create_source_info_from_path
)


def demo_basic_usage():
    """Demonstrate basic usage of data models."""
    print("=== Basic Data Model Usage ===")
    
    # Create a simple analysis result
    source = create_source_info_from_path("https://example.com/news-article")
    print(f"Source type: {source.type}")
    
    # Create some extracted entities
    entities = [
        NamedEntity("Apple Inc.", EntityType.ORGANIZATION, 0.95),
        NamedEntity("Tim Cook", EntityType.PERSON, 0.88),
        NamedEntity("Cupertino", EntityType.LOCATION, 0.92)
    ]
    
    # Create numeric values
    numeric_values = [
        NumericValue(1.5, "billion", "Revenue", "currency"),
        NumericValue(15.2, "%", "Growth rate", "percentage")
    ]
    
    # Create structured data
    structured_data = StructuredData(
        entities=entities,
        numeric_values=numeric_values
    )
    
    # Create a processed result
    result = ProcessedResult(
        content="Apple Inc. reported strong quarterly results with $1.5 billion in revenue, showing 15.2% growth.",
        source_info=source,
        extracted_data=structured_data,
        metadata=ResultMetadata(analysis_type="financial_analysis")
    )
    
    print(f"Result ID: {result.id}")
    print(f"Has exportable data: {result.has_exportable_data()}")
    print(f"Has visualizable data: {result.has_visualizable_data()}")
    print(f"Number of entities: {len(result.extracted_data.entities)}")
    print(f"Number of numeric values: {len(result.extracted_data.numeric_values)}")
    print()


def demo_table_operations():
    """Demonstrate table creation and export operations."""
    print("=== Table Operations Demo ===")
    
    # Create a sales data table
    sales_table = DataTable(
        headers=["Product", "Q1 Sales", "Q2 Sales", "Q3 Sales", "Q4 Sales"],
        rows=[
            ["iPhone", "50000", "55000", "48000", "62000"],
            ["iPad", "25000", "28000", "22000", "30000"],
            ["MacBook", "15000", "18000", "16000", "20000"]
        ],
        title="Product Sales by Quarter"
    )
    
    print(f"Table title: {sales_table.title}")
    print(f"Headers: {sales_table.headers}")
    print(f"Number of rows: {len(sales_table.rows)}")
    
    # Demonstrate Excel export format
    excel_format = sales_table.to_excel_format()
    print(f"Excel sheet name: {excel_format['sheet_name']}")
    
    # Demonstrate CSV export
    csv_output = sales_table.to_csv_format()
    print("CSV output (first 100 chars):")
    print(csv_output[:100] + "...")
    print()


def demo_visualization_setup():
    """Demonstrate visualization configuration."""
    print("=== Visualization Setup Demo ===")
    
    # Create chart configuration
    chart_config = ChartConfig(
        title="Quarterly Sales Performance",
        x_label="Quarter",
        y_label="Sales (Units)",
        colors=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"],
        size=(12, 8)
    )
    
    # Create visualization
    visualization = Visualization(
        chart_type=ChartType.BAR,
        data_source="quarterly_sales",
        config=chart_config,
        interactive=True
    )
    
    print(f"Chart type: {visualization.chart_type.value}")
    print(f"Chart title: {visualization.config.title}")
    print(f"Interactive: {visualization.interactive}")
    print(f"Chart size: {visualization.config.size}")
    print()


def demo_follow_up_actions():
    """Demonstrate follow-up actions system."""
    print("=== Follow-up Actions Demo ===")
    
    # Create default actions
    default_actions = create_default_actions()
    print("Default actions:")
    for action in default_actions:
        print(f"  - {action.label}: {action.description}")
    
    # Create custom actions
    custom_actions = [
        Action(
            action_type=ActionType.EXPORT,
            label="Export to Excel",
            description="Export structured data to Excel format",
            parameters={"format": "xlsx", "include_charts": True}
        ),
        Action(
            action_type=ActionType.VISUALIZE,
            label="Create Charts",
            description="Generate visualizations from numeric data",
            parameters={"auto_suggest": True, "chart_types": ["bar", "line", "pie"]}
        )
    ]
    
    print("\nCustom actions:")
    for action in custom_actions:
        print(f"  - {action.label}: {action.description}")
        if action.parameters:
            print(f"    Parameters: {action.parameters}")
    print()


def demo_complete_workflow():
    """Demonstrate a complete analysis workflow."""
    print("=== Complete Workflow Demo ===")
    
    # 1. Create source information
    source = create_source_info_from_path("/path/to/financial_report.pdf")
    
    # 2. Create extracted data
    entities = [
        NamedEntity("Microsoft Corporation", EntityType.ORGANIZATION, 0.98),
        NamedEntity("Satya Nadella", EntityType.PERSON, 0.95),
        NamedEntity("2024-01-15", EntityType.DATE, 0.90)
    ]
    
    numeric_values = [
        NumericValue(62.0, "billion USD", "Total revenue", "currency"),
        NumericValue(22.1, "billion USD", "Net income", "currency"),
        NumericValue(12.0, "%", "Revenue growth", "percentage")
    ]
    
    financial_table = DataTable(
        headers=["Metric", "Q4 2023", "Q4 2024", "Change"],
        rows=[
            ["Revenue", "52.7B", "62.0B", "+17.6%"],
            ["Net Income", "18.3B", "22.1B", "+20.8%"],
            ["Operating Income", "22.6B", "27.0B", "+19.5%"]
        ],
        title="Financial Performance"
    )
    
    structured_data = StructuredData(
        entities=entities,
        numeric_values=numeric_values,
        tables=[financial_table],
        categories={"metrics": ["Revenue", "Net Income", "Operating Income"]}
    )
    
    # 3. Create visualizations
    chart_config = ChartConfig(
        title="Financial Performance Comparison",
        x_label="Metrics",
        y_label="Amount (Billions USD)",
        colors=["#2E8B57", "#4169E1"]
    )
    
    visualization = Visualization(
        chart_type=ChartType.BAR,
        data_source="financial_comparison",
        config=chart_config
    )
    
    # 4. Create metadata
    metadata = ResultMetadata(
        analysis_type="financial_report_analysis",
        processing_time=3.2,
        model_used="gpt-4o",
        tokens_used=2150,
        confidence_score=0.92,
        tags=["financial", "quarterly", "microsoft"]
    )
    
    # 5. Create complete result
    result = ProcessedResult(
        content="Microsoft Corporation reported strong Q4 2024 results with $62.0 billion in revenue, representing 17.6% growth year-over-year. Net income increased to $22.1 billion, up 20.8% from the previous year.",
        source_info=source,
        extracted_data=structured_data,
        visualizations=[visualization],
        follow_up_actions=create_default_actions(),
        metadata=metadata
    )
    
    # 6. Display results
    print(f"Analysis completed for: {source.file_name}")
    print(f"Analysis type: {metadata.analysis_type}")
    print(f"Processing time: {metadata.processing_time}s")
    print(f"Confidence score: {metadata.confidence_score}")
    print(f"Entities found: {len(structured_data.entities)}")
    print(f"Numeric values: {len(structured_data.numeric_values)}")
    print(f"Tables: {len(structured_data.tables)}")
    print(f"Visualizations: {len(result.visualizations)}")
    print(f"Follow-up actions: {len(result.follow_up_actions)}")
    print(f"Has exportable data: {result.has_exportable_data()}")
    print(f"Has visualizable data: {result.has_visualizable_data()}")
    
    # 7. Demonstrate serialization
    result_dict = result.to_dict()
    print(f"Serialized result size: {len(str(result_dict))} characters")
    
    # 8. Demonstrate deserialization
    reconstructed = ProcessedResult.from_dict(result_dict)
    print(f"Reconstruction successful: {reconstructed.id == result.id}")
    print()


def demo_serialization():
    """Demonstrate serialization and deserialization."""
    print("=== Serialization Demo ===")
    
    # Create a simple result
    result = ProcessedResult(
        content="Test analysis content",
        metadata=ResultMetadata(analysis_type="test")
    )
    
    # Add some data
    result.extracted_data.entities.append(
        NamedEntity("Test Entity", EntityType.PERSON, 0.85)
    )
    
    # Serialize to dictionary
    result_dict = result.to_dict()
    print("Original result ID:", result.id)
    print("Serialized keys:", list(result_dict.keys()))
    
    # Deserialize back
    reconstructed = ProcessedResult.from_dict(result_dict)
    print("Reconstructed result ID:", reconstructed.id)
    print("IDs match:", result.id == reconstructed.id)
    print("Content matches:", result.content == reconstructed.content)
    print("Entities count matches:", len(result.extracted_data.entities) == len(reconstructed.extracted_data.entities))
    print()


if __name__ == "__main__":
    print("Data Models Demonstration")
    print("=" * 50)
    print()
    
    demo_basic_usage()
    demo_table_operations()
    demo_visualization_setup()
    demo_follow_up_actions()
    demo_complete_workflow()
    demo_serialization()
    
    print("Demo completed successfully!")