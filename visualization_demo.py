"""
Demo script for the visualization engine.

This script demonstrates the chart generation and visualization panel
functionality with sample data.
"""

import matplotlib.pyplot as plt
from chart_generator import ChartGenerator
from data_models import (
    StructuredData, DataTable, NumericValue, TemporalValue,
    ChartType, ChartConfig
)
from datetime import datetime


def create_sample_data():
    """Create sample data for demonstration."""
    # Sample sales data table
    sales_table = DataTable(
        headers=["Monat", "Umsatz", "Kosten"],
        rows=[
            ["Januar", "50000", "35000"],
            ["Februar", "62000", "40000"],
            ["März", "58000", "38000"],
            ["April", "71000", "45000"],
            ["Mai", "68000", "42000"],
            ["Juni", "75000", "48000"]
        ],
        title="Monatliche Verkaufsdaten 2024"
    )
    
    # Sample numeric values
    numeric_values = [
        NumericValue(value=50000, unit="€", context="Januar Umsatz", value_type="currency"),
        NumericValue(value=62000, unit="€", context="Februar Umsatz", value_type="currency"),
        NumericValue(value=58000, unit="€", context="März Umsatz", value_type="currency"),
        NumericValue(value=71000, unit="€", context="April Umsatz", value_type="currency"),
        NumericValue(value=68000, unit="€", context="Mai Umsatz", value_type="currency"),
        NumericValue(value=75000, unit="€", context="Juni Umsatz", value_type="currency"),
    ]
    
    # Sample temporal data
    temporal_data = [
        TemporalValue(
            value=datetime(2024, 1, 1),
            original_text="Januar 2024",
            precision="month"
        ),
        TemporalValue(
            value=datetime(2024, 2, 1),
            original_text="Februar 2024",
            precision="month"
        ),
        TemporalValue(
            value=datetime(2024, 3, 1),
            original_text="März 2024",
            precision="month"
        ),
        TemporalValue(
            value=datetime(2024, 4, 1),
            original_text="April 2024",
            precision="month"
        ),
        TemporalValue(
            value=datetime(2024, 5, 1),
            original_text="Mai 2024",
            precision="month"
        ),
        TemporalValue(
            value=datetime(2024, 6, 1),
            original_text="Juni 2024",
            precision="month"
        )
    ]
    
    return StructuredData(
        tables=[sales_table],
        numeric_values=numeric_values,
        temporal_data=temporal_data
    )


def demo_chart_suggestions():
    """Demonstrate chart type suggestions."""
    print("=== Chart Generator Demo ===")
    print()
    
    # Create chart generator
    generator = ChartGenerator()
    
    # Create sample data
    data = create_sample_data()
    
    print("Sample Data:")
    print(f"- Tables: {len(data.tables)}")
    print(f"- Numeric Values: {len(data.numeric_values)}")
    print(f"- Temporal Data: {len(data.temporal_data)}")
    print()
    
    # Get chart suggestions
    suggestions = generator.suggest_chart_types(data)
    
    print(f"Chart Suggestions ({len(suggestions)} found):")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"{i}. {suggestion.chart_type.value.upper()} "
              f"(Confidence: {suggestion.confidence:.0%})")
        print(f"   Reasoning: {suggestion.reasoning}")
        print()
    
    return generator, data, suggestions


def demo_chart_creation():
    """Demonstrate chart creation and export."""
    generator, data, suggestions = demo_chart_suggestions()
    
    if not suggestions:
        print("No chart suggestions available.")
        return
    
    print("=== Creating Charts ===")
    print()
    
    # Create charts for top 3 suggestions
    for i, suggestion in enumerate(suggestions[:3], 1):
        print(f"Creating {suggestion.chart_type.value.upper()} chart...")
        
        try:
            # Create the chart
            visualization = generator.create_chart(
                data,
                suggestion.chart_type,
                suggestion.suggested_config
            )
            
            print(f"✓ Chart created successfully")
            print(f"  Chart Type: {visualization.chart_type.value}")
            print(f"  Data Source: {visualization.data_source}")
            
            # Export as PNG
            filename = f"demo_chart_{suggestion.chart_type.value}_{i}.png"
            success = generator.export_chart(visualization, filename, format='png')
            
            if success:
                print(f"✓ Chart exported as {filename}")
            else:
                print(f"✗ Failed to export chart")
            
            # Clean up matplotlib figure
            if hasattr(visualization, '_figure'):
                plt.close(visualization._figure)
            
        except Exception as e:
            print(f"✗ Error creating chart: {e}")
        
        print()


def demo_custom_chart():
    """Demonstrate custom chart creation."""
    print("=== Custom Chart Demo ===")
    print()
    
    generator, data, _ = demo_chart_suggestions()
    
    # Create custom configuration
    custom_config = ChartConfig(
        title="Benutzerdefiniertes Umsatzdiagramm",
        x_label="Monate",
        y_label="Umsatz (€)",
        colors=["#2E86AB", "#A23B72", "#F18F01"],
        size=(12, 8)
    )
    
    try:
        # Create custom bar chart
        visualization = generator.create_chart(
            data,
            ChartType.BAR,
            custom_config
        )
        
        print("✓ Custom chart created successfully")
        print(f"  Title: {custom_config.title}")
        print(f"  Size: {custom_config.size}")
        print(f"  Colors: {len(custom_config.colors)} custom colors")
        
        # Export as PDF
        filename = "demo_custom_chart.pdf"
        success = generator.export_chart(visualization, filename, format='pdf')
        
        if success:
            print(f"✓ Custom chart exported as {filename}")
        else:
            print(f"✗ Failed to export custom chart")
        
        # Clean up
        if hasattr(visualization, '_figure'):
            plt.close(visualization._figure)
            
    except Exception as e:
        print(f"✗ Error creating custom chart: {e}")
    
    print()


def demo_chart_formats():
    """Demonstrate different export formats."""
    print("=== Export Formats Demo ===")
    print()
    
    generator, data, suggestions = demo_chart_suggestions()
    
    if not suggestions:
        print("No chart suggestions available.")
        return
    
    # Use the first suggestion
    suggestion = suggestions[0]
    
    try:
        # Create chart
        visualization = generator.create_chart(
            data,
            suggestion.chart_type,
            suggestion.suggested_config
        )
        
        # Export in different formats
        formats = ['png', 'pdf', 'svg']
        
        for fmt in formats:
            filename = f"demo_export.{fmt}"
            success = generator.export_chart(visualization, filename, format=fmt)
            
            if success:
                print(f"✓ Chart exported as {filename}")
            else:
                print(f"✗ Failed to export as {fmt}")
        
        # Test getting chart as bytes
        try:
            chart_bytes = generator.get_chart_as_bytes(visualization, format='png')
            print(f"✓ Chart converted to bytes ({len(chart_bytes)} bytes)")
        except Exception as e:
            print(f"✗ Failed to get chart as bytes: {e}")
        
        # Clean up
        if hasattr(visualization, '_figure'):
            plt.close(visualization._figure)
            
    except Exception as e:
        print(f"✗ Error in export demo: {e}")
    
    print()


def main():
    """Run all demos."""
    print("Visualization Engine Demo")
    print("=" * 50)
    print()
    
    try:
        # Run demos
        demo_chart_suggestions()
        demo_chart_creation()
        demo_custom_chart()
        demo_chart_formats()
        
        print("Demo completed successfully!")
        print()
        print("Generated files:")
        print("- demo_chart_*.png (chart examples)")
        print("- demo_custom_chart.pdf (custom chart)")
        print("- demo_export.* (format examples)")
        
    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()