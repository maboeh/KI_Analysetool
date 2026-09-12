"""
Chart generation module for automatic visualization creation.

This module provides the ChartGenerator class that can automatically suggest
and create charts based on structured data characteristics.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
import io
import os
from datetime import datetime
import logging

from data_models import (
    StructuredData, ChartType, ChartConfig, Visualization, 
    DataTable, NumericValue, TemporalValue
)
from error_handler import ErrorHandler, ErrorResult, handle_errors


@dataclass
class ChartSuggestion:
    """Represents a suggested chart type with reasoning."""
    chart_type: ChartType
    confidence: float
    reasoning: str
    data_source: str
    suggested_config: ChartConfig


class ChartGenerator:
    """
    Generates charts automatically based on structured data characteristics.
    
    This class analyzes the structure and content of data to suggest appropriate
    chart types and automatically generates visualizations with proper formatting.
    """
    
    def __init__(self):
        """Initialize the chart generator with default settings."""
        self.error_handler = ErrorHandler()
        self.logger = logging.getLogger(__name__)
        
        # Set matplotlib style for better-looking charts
        try:
            plt.style.use('seaborn-v0_8')
            sns.set_palette("husl")
        except Exception as e:
            self.logger.warning(f"Could not set matplotlib style: {e}")
            # Continue with default style
        
        # Default color schemes
        self.color_schemes = {
            'default': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'],
            'pastel': ['#AEC7E8', '#FFBB78', '#98DF8A', '#FF9896', '#C5B0D5'],
            'dark': ['#1f1f1f', '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4'],
            'professional': ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#592E83']
        }
        
        # Chart type thresholds and rules
        self.suggestion_rules = {
            'min_numeric_for_chart': 2,
            'max_categories_for_pie': 8,
            'min_temporal_for_line': 3,
            'max_bars_for_readability': 20
        }
    
    def suggest_chart_types(self, data: StructuredData) -> List[ChartSuggestion]:
        """
        Analyze structured data and suggest appropriate chart types.
        
        Args:
            data: StructuredData object containing extracted information
            
        Returns:
            List of ChartSuggestion objects ordered by confidence
        """
        suggestions = []
        
        # Analyze tables for chart opportunities
        for i, table in enumerate(data.tables):
            table_suggestions = self._analyze_table_for_charts(table, f"table_{i}")
            suggestions.extend(table_suggestions)
        
        # Analyze numeric values for distribution charts
        if len(data.numeric_values) >= self.suggestion_rules['min_numeric_for_chart']:
            numeric_suggestions = self._analyze_numeric_values(data.numeric_values)
            suggestions.extend(numeric_suggestions)
        
        # Analyze temporal data for time series
        if len(data.temporal_data) >= self.suggestion_rules['min_temporal_for_line']:
            temporal_suggestions = self._analyze_temporal_data(data.temporal_data)
            suggestions.extend(temporal_suggestions)
        
        # Sort by confidence score
        suggestions.sort(key=lambda x: x.confidence, reverse=True)
        
        return suggestions
    
    def _analyze_table_for_charts(self, table: DataTable, source_id: str) -> List[ChartSuggestion]:
        """Analyze a data table and suggest appropriate chart types."""
        suggestions = []
        
        if not table.headers or not table.rows:
            return suggestions
        
        # Analyze column types
        numeric_columns = []
        categorical_columns = []
        
        for col_idx, header in enumerate(table.headers):
            column_data = [row[col_idx] for row in table.rows if col_idx < len(row)]
            
            if self._is_numeric_column(column_data):
                numeric_columns.append((col_idx, header))
            else:
                categorical_columns.append((col_idx, header))
        
        # Suggest charts based on column composition
        if len(numeric_columns) >= 1 and len(categorical_columns) >= 1:
            # Mixed data - good for bar charts
            config = ChartConfig(
                title=table.title or f"Vergleich: {table.headers[0]} vs {table.headers[1]}",
                x_label=categorical_columns[0][1] if categorical_columns else "Kategorie",
                y_label=numeric_columns[0][1] if numeric_columns else "Wert"
            )
            
            suggestions.append(ChartSuggestion(
                chart_type=ChartType.BAR,
                confidence=0.9,
                reasoning="Tabelle enthält kategorische und numerische Daten - ideal für Balkendiagramm",
                data_source=source_id,
                suggested_config=config
            ))
            
            # Also suggest pie chart if reasonable number of categories
            if len(table.rows) <= self.suggestion_rules['max_categories_for_pie']:
                pie_config = ChartConfig(
                    title=table.title or "Verteilung der Kategorien"
                )
                suggestions.append(ChartSuggestion(
                    chart_type=ChartType.PIE,
                    confidence=0.7,
                    reasoning="Wenige Kategorien mit numerischen Werten - geeignet für Kreisdiagramm",
                    data_source=source_id,
                    suggested_config=pie_config
                ))
        
        elif len(numeric_columns) >= 2:
            # Multiple numeric columns - suggest scatter plot or line chart
            config = ChartConfig(
                title=table.title or f"Korrelation: {numeric_columns[0][1]} vs {numeric_columns[1][1]}",
                x_label=numeric_columns[0][1],
                y_label=numeric_columns[1][1]
            )
            
            suggestions.append(ChartSuggestion(
                chart_type=ChartType.SCATTER,
                confidence=0.8,
                reasoning="Mehrere numerische Spalten - Streudiagramm zeigt Korrelationen",
                data_source=source_id,
                suggested_config=config
            ))
        
        return suggestions
    
    def _analyze_numeric_values(self, numeric_values: List[NumericValue]) -> List[ChartSuggestion]:
        """Analyze standalone numeric values for visualization opportunities."""
        suggestions = []
        
        # Group by value type
        value_groups = {}
        for nv in numeric_values:
            group_key = nv.value_type or "general"
            if group_key not in value_groups:
                value_groups[group_key] = []
            value_groups[group_key].append(nv)
        
        # Suggest histogram for value distributions
        if len(numeric_values) >= 5:
            config = ChartConfig(
                title="Verteilung der numerischen Werte",
                x_label="Wert",
                y_label="Häufigkeit"
            )
            
            suggestions.append(ChartSuggestion(
                chart_type=ChartType.HISTOGRAM,
                confidence=0.7,
                reasoning="Viele numerische Werte - Histogramm zeigt Verteilung",
                data_source="numeric_values",
                suggested_config=config
            ))
        
        return suggestions
    
    def _analyze_temporal_data(self, temporal_data: List[TemporalValue]) -> List[ChartSuggestion]:
        """Analyze temporal data for time series visualization."""
        suggestions = []
        
        if len(temporal_data) >= 3:
            config = ChartConfig(
                title="Zeitlicher Verlauf",
                x_label="Zeit",
                y_label="Ereignisse"
            )
            
            suggestions.append(ChartSuggestion(
                chart_type=ChartType.LINE,
                confidence=0.8,
                reasoning="Zeitliche Daten vorhanden - Liniendiagramm zeigt Trends",
                data_source="temporal_data",
                suggested_config=config
            ))
        
        return suggestions
    
    def _is_numeric_column(self, column_data: List[str]) -> bool:
        """Check if a column contains primarily numeric data."""
        if not column_data:
            return False
        
        numeric_count = 0
        for value in column_data:
            try:
                float(str(value).replace(',', '.').replace('%', '').replace('€', '').strip())
                numeric_count += 1
            except (ValueError, AttributeError):
                continue
        
        return numeric_count / len(column_data) > 0.7
    
    def create_chart(self, data: StructuredData, chart_type: ChartType, 
                    config: Optional[ChartConfig] = None, 
                    data_source: Optional[str] = None) -> Visualization:
        """
        Create a chart from structured data.
        
        Args:
            data: StructuredData containing the information to visualize
            chart_type: Type of chart to create
            config: Optional configuration for chart appearance
            data_source: Optional identifier for the data source to use
            
        Returns:
            Visualization object containing the generated chart
        """
        context = {
            "operation": "visualization",
            "chart_type": chart_type.value if hasattr(chart_type, 'value') else (str(chart_type) if chart_type else "unknown"),
            "data_source": data_source
        }
        
        try:
            if config is None:
                config = ChartConfig()
            
            # Validate data before creating chart
            if not self._validate_data_for_chart(data, chart_type):
                context["error_details"] = "Insufficient or invalid data for chart type"
                error_result = self.error_handler.handle_error(
                    ValueError("Insufficient data for visualization"), 
                    context=context
                )
                raise ValueError(self.error_handler.create_user_friendly_message(error_result))
            
            # Create matplotlib figure
            fig, ax = plt.subplots(figsize=config.size)
            
            # Generate chart based on type
            if chart_type == ChartType.BAR:
                self._create_bar_chart(ax, data, config, data_source)
            elif chart_type == ChartType.LINE:
                self._create_line_chart(ax, data, config, data_source)
            elif chart_type == ChartType.PIE:
                self._create_pie_chart(ax, data, config, data_source)
            elif chart_type == ChartType.SCATTER:
                self._create_scatter_chart(ax, data, config, data_source)
            elif chart_type == ChartType.HISTOGRAM:
                self._create_histogram(ax, data, config, data_source)
            else:
                context["error_details"] = f"Chart type {chart_type} not supported"
                error_result = self.error_handler.handle_error(
                    ValueError(f"Unsupported chart type: {chart_type}"), 
                    context=context
                )
                raise ValueError(self.error_handler.create_user_friendly_message(error_result))
            
            # Apply common formatting
            self._apply_chart_formatting(ax, config, chart_type)
            
            # Create visualization object
            visualization = Visualization(
                chart_type=chart_type,
                data_source=data_source or "unknown",
                config=config,
                interactive=False
            )
            
            # Store the figure in the visualization (we'll handle file saving separately)
            visualization._figure = fig
            
            return visualization
            
        except Exception as e:
            # If the exception already contains a user-friendly message (starts with ❌),
            # re-raise it directly to avoid double-processing
            if str(e).startswith("❌"):
                raise
            context["error_details"] = str(e)
            error_result = self.error_handler.handle_error(e, context=context)
            raise type(e)(self.error_handler.create_user_friendly_message(error_result))
    
    def _create_bar_chart(self, ax, data: StructuredData, config: ChartConfig, data_source: str):
        """Create a bar chart from the data."""
        # Find appropriate table or create from numeric values
        chart_data = self._extract_bar_chart_data(data, data_source)
        
        if not chart_data:
            raise ValueError("Keine geeigneten Daten für Balkendiagramm gefunden")
        
        labels, values = chart_data
        colors = config.colors or self.color_schemes['default'][:len(labels)]
        
        bars = ax.bar(labels, values, color=colors)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}', ha='center', va='bottom')
        
        # Rotate x-axis labels if too many or too long
        if len(labels) > 5 or any(len(str(label)) > 10 for label in labels):
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    
    def _create_line_chart(self, ax, data: StructuredData, config: ChartConfig, data_source: str):
        """Create a line chart from the data."""
        chart_data = self._extract_line_chart_data(data, data_source)
        
        if not chart_data:
            raise ValueError("Keine geeigneten Daten für Liniendiagramm gefunden")
        
        x_values, y_values = chart_data
        color = config.colors[0] if config.colors else self.color_schemes['default'][0]
        
        ax.plot(x_values, y_values, marker='o', linewidth=2, color=color)
        ax.grid(True, alpha=0.3)
    
    def _create_pie_chart(self, ax, data: StructuredData, config: ChartConfig, data_source: str):
        """Create a pie chart from the data."""
        chart_data = self._extract_pie_chart_data(data, data_source)
        
        if not chart_data:
            raise ValueError("Keine geeigneten Daten für Kreisdiagramm gefunden")
        
        labels, values = chart_data
        colors = config.colors or self.color_schemes['pastel'][:len(labels)]
        
        wedges, texts, autotexts = ax.pie(values, labels=labels, colors=colors, 
                                         autopct='%1.1f%%', startangle=90)
        
        # Improve text readability
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
    
    def _create_scatter_chart(self, ax, data: StructuredData, config: ChartConfig, data_source: str):
        """Create a scatter plot from the data."""
        chart_data = self._extract_scatter_chart_data(data, data_source)
        
        if not chart_data:
            raise ValueError("Keine geeigneten Daten für Streudiagramm gefunden")
        
        x_values, y_values = chart_data
        color = config.colors[0] if config.colors else self.color_schemes['default'][0]
        
        ax.scatter(x_values, y_values, alpha=0.7, color=color, s=50)
        ax.grid(True, alpha=0.3)
    
    def _create_histogram(self, ax, data: StructuredData, config: ChartConfig, data_source: str):
        """Create a histogram from the data."""
        values = self._extract_histogram_data(data, data_source)
        
        if not values:
            raise ValueError("Keine geeigneten Daten für Histogramm gefunden")
        
        color = config.colors[0] if config.colors else self.color_schemes['default'][0]
        
        n_bins = min(20, max(5, len(values) // 5))  # Adaptive bin count
        ax.hist(values, bins=n_bins, alpha=0.7, color=color, edgecolor='black')
        ax.grid(True, alpha=0.3, axis='y')
    
    def _extract_bar_chart_data(self, data: StructuredData, data_source: str) -> Optional[Tuple[List[str], List[float]]]:
        """Extract data suitable for bar charts."""
        # Try to find data in tables first
        for i, table in enumerate(data.tables):
            if data_source and f"table_{i}" not in data_source:
                continue
                
            if len(table.headers) >= 2 and len(table.rows) > 0:
                # Use first column as labels, second as values
                labels = []
                values = []
                
                for row in table.rows:
                    if len(row) >= 2:
                        labels.append(str(row[0]))
                        try:
                            value = float(str(row[1]).replace(',', '.').replace('%', '').replace('€', '').strip())
                            values.append(value)
                        except (ValueError, AttributeError):
                            continue
                
                if labels and values and len(labels) == len(values):
                    return labels, values
        
        # Fallback: use numeric values grouped by context
        if data.numeric_values:
            context_groups = {}
            for nv in data.numeric_values:
                context = nv.context or nv.value_type or "Wert"
                if context not in context_groups:
                    context_groups[context] = []
                context_groups[context].append(nv.value)
            
            if len(context_groups) > 1:
                labels = list(context_groups.keys())
                values = [sum(group) / len(group) for group in context_groups.values()]  # Average
                return labels, values
        
        return None
    
    def _extract_line_chart_data(self, data: StructuredData, data_source: str) -> Optional[Tuple[List, List[float]]]:
        """Extract data suitable for line charts."""
        # Use temporal data if available
        if data.temporal_data:
            sorted_temporal = sorted(data.temporal_data, key=lambda x: x.value)
            x_values = [td.value for td in sorted_temporal]
            y_values = list(range(1, len(x_values) + 1))  # Count of events over time
            return x_values, y_values
        
        # Try to find time series in tables
        for table in data.tables:
            if len(table.headers) >= 2 and len(table.rows) > 2:
                # Check if first column could be time-based
                x_values = []
                y_values = []
                
                for row in table.rows:
                    if len(row) >= 2:
                        try:
                            # Try to parse as number for x-axis
                            x_val = float(str(row[0]).replace(',', '.'))
                            y_val = float(str(row[1]).replace(',', '.').replace('%', '').replace('€', '').strip())
                            x_values.append(x_val)
                            y_values.append(y_val)
                        except (ValueError, AttributeError):
                            continue
                
                if len(x_values) >= 3:
                    return x_values, y_values
        
        return None
    
    def _extract_pie_chart_data(self, data: StructuredData, data_source: str) -> Optional[Tuple[List[str], List[float]]]:
        """Extract data suitable for pie charts."""
        return self._extract_bar_chart_data(data, data_source)  # Same logic as bar chart
    
    def _extract_scatter_chart_data(self, data: StructuredData, data_source: str) -> Optional[Tuple[List[float], List[float]]]:
        """Extract data suitable for scatter plots."""
        # Look for tables with at least 2 numeric columns
        for table in data.tables:
            if len(table.headers) >= 2 and len(table.rows) > 2:
                x_values = []
                y_values = []
                
                for row in table.rows:
                    if len(row) >= 2:
                        try:
                            x_val = float(str(row[0]).replace(',', '.').replace('%', '').replace('€', '').strip())
                            y_val = float(str(row[1]).replace(',', '.').replace('%', '').replace('€', '').strip())
                            x_values.append(x_val)
                            y_values.append(y_val)
                        except (ValueError, AttributeError):
                            continue
                
                if len(x_values) >= 3:
                    return x_values, y_values
        
        return None
    
    def _extract_histogram_data(self, data: StructuredData, data_source: str) -> Optional[List[float]]:
        """Extract data suitable for histograms."""
        values = []
        
        # Collect all numeric values
        for nv in data.numeric_values:
            if isinstance(nv.value, (int, float)):
                values.append(float(nv.value))
        
        # Also try to extract from tables
        for table in data.tables:
            for row in table.rows:
                for cell in row:
                    try:
                        value = float(str(cell).replace(',', '.').replace('%', '').replace('€', '').strip())
                        values.append(value)
                    except (ValueError, AttributeError):
                        continue
        
        return values if len(values) >= 5 else None
    
    def _apply_chart_formatting(self, ax, config: ChartConfig, chart_type: ChartType):
        """Apply common formatting to charts."""
        # Set title
        if config.title:
            ax.set_title(config.title, fontsize=14, fontweight='bold', pad=20)
        
        # Set axis labels
        if config.x_label and chart_type != ChartType.PIE:
            ax.set_xlabel(config.x_label, fontsize=12)
        
        if config.y_label and chart_type != ChartType.PIE:
            ax.set_ylabel(config.y_label, fontsize=12)
        
        # Improve layout
        plt.tight_layout()
        
        # Set style
        if config.style:
            plt.style.use(config.style)
    
    def _validate_data_for_chart(self, data: StructuredData, chart_type: ChartType) -> bool:
        """Validate that data is sufficient for the requested chart type."""
        if chart_type in [ChartType.BAR, ChartType.PIE]:
            # Need at least one table with data or numeric values
            return (data.tables and any(table.rows for table in data.tables)) or \
                   len(data.numeric_values) >= 2
        
        elif chart_type == ChartType.LINE:
            # Need temporal data or table with at least 3 rows
            return len(data.temporal_data) >= 3 or \
                   (data.tables and any(len(table.rows) >= 3 for table in data.tables))
        
        elif chart_type == ChartType.SCATTER:
            # Need table with at least 2 numeric columns and 3+ rows
            return data.tables and any(
                len(table.rows) >= 3 and len(table.headers) >= 2 
                for table in data.tables
            )
        
        elif chart_type == ChartType.HISTOGRAM:
            # Need at least 5 numeric values
            return len(data.numeric_values) >= 5
        
        return False
    
    def export_chart(self, visualization: Visualization, file_path: str, 
                    format: str = 'png', dpi: int = 300) -> bool:
        """
        Export a chart to file.
        
        Args:
            visualization: Visualization object containing the chart
            file_path: Path where to save the file
            format: Export format ('png', 'pdf', 'svg')
            dpi: Resolution for raster formats
            
        Returns:
            True if export was successful, False otherwise
        """
        context = {
            "operation": "export", 
            "file_path": file_path, 
            "format": format,
            "chart_type": visualization.chart_type.value if hasattr(visualization, 'chart_type') else "unknown"
        }
        
        try:
            if not hasattr(visualization, '_figure'):
                error_result = self.error_handler.handle_error(
                    ValueError("Visualization does not contain a figure to export"), 
                    context=context
                )
                self.logger.error(self.error_handler.create_user_friendly_message(error_result))
                return False
            
            # Ensure directory exists (only if there's a directory part)
            dir_path = os.path.dirname(file_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            
            # Save the figure
            visualization._figure.savefig(
                file_path, 
                format=format, 
                dpi=dpi, 
                bbox_inches='tight',
                facecolor='white',
                edgecolor='none'
            )
            
            # Update visualization with file path
            visualization.file_path = file_path
            
            return True
            
        except Exception as e:
            context["error_details"] = str(e)
            error_result = self.error_handler.handle_error(e, context=context)
            self.logger.error(self.error_handler.create_user_friendly_message(error_result))
            return False
    
    def get_chart_as_bytes(self, visualization: Visualization, format: str = 'png', dpi: int = 300) -> bytes:
        """
        Get chart as bytes for embedding or transmission.
        
        Args:
            visualization: Visualization object containing the chart
            format: Export format ('png', 'pdf', 'svg')
            dpi: Resolution for raster formats
            
        Returns:
            Chart data as bytes
        """
        if not hasattr(visualization, '_figure'):
            raise ValueError("Visualization does not contain a figure to export")
        
        buffer = io.BytesIO()
        visualization._figure.savefig(
            buffer, 
            format=format, 
            dpi=dpi, 
            bbox_inches='tight',
            facecolor='white',
            edgecolor='none'
        )
        buffer.seek(0)
        return buffer.getvalue()
    
    def create_interactive_chart(self, visualization: Visualization) -> 'InteractiveChart':
        """
        Create an interactive version of a chart for Tkinter integration.
        
        Args:
            visualization: Visualization object containing the chart
            
        Returns:
            InteractiveChart object that can be embedded in Tkinter
        """
        return InteractiveChart(visualization)


class InteractiveChart:
    """
    Wrapper for matplotlib charts that can be embedded in Tkinter applications.
    """
    
    def __init__(self, visualization: Visualization):
        """Initialize with a visualization object."""
        self.visualization = visualization
        self.canvas = None
        self.toolbar = None
    
    def embed_in_tkinter(self, parent_widget):
        """
        Embed the chart in a Tkinter widget.
        
        Args:
            parent_widget: Tkinter widget to embed the chart in
            
        Returns:
            Tuple of (canvas, toolbar) widgets
        """
        if not hasattr(self.visualization, '_figure'):
            raise ValueError("Visualization does not contain a figure to embed")
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.visualization._figure, parent_widget)
        self.canvas.draw()
        
        # Create toolbar for interaction
        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
        self.toolbar = NavigationToolbar2Tk(self.canvas, parent_widget)
        self.toolbar.update()
        
        return self.canvas, self.toolbar
    
    def update_chart(self, new_data: StructuredData):
        """Update the chart with new data."""
        # This would require regenerating the chart
        # Implementation depends on specific requirements
        pass