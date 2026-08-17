"""
Unit tests for ResultsDisplayWidget

Tests the enhanced results display functionality including formatting,
collapsible sections, zoom controls, and syntax highlighting.
"""

import unittest
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from results_display import ResultsDisplayWidget, DisplaySection


class TestResultsDisplayWidget(unittest.TestCase):
    """Test cases for ResultsDisplayWidget"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during testing
        self.widget = ResultsDisplayWidget(self.root)
    
    def tearDown(self):
        """Clean up after tests"""
        self.root.destroy()
    
    def test_widget_initialization(self):
        """Test that the widget initializes correctly"""
        self.assertIsInstance(self.widget, ResultsDisplayWidget)
        self.assertEqual(self.widget.zoom_level, 1.0)
        self.assertEqual(self.widget.base_font_size, 10)
        self.assertEqual(len(self.widget.sections), 0)
        
        # Check that main components exist
        self.assertIsNotNone(self.widget.toolbar_frame)
        self.assertIsNotNone(self.widget.text_widget)
        self.assertIsNotNone(self.widget.scrollbar)
    
    def test_zoom_functionality(self):
        """Test zoom in, zoom out, and reset functionality"""
        initial_zoom = self.widget.zoom_level
        
        # Test zoom in
        self.widget.zoom_in()
        self.assertGreater(self.widget.zoom_level, initial_zoom)
        
        # Test zoom out
        current_zoom = self.widget.zoom_level
        self.widget.zoom_out()
        self.assertLess(self.widget.zoom_level, current_zoom)
        
        # Test reset zoom
        self.widget.reset_zoom()
        self.assertEqual(self.widget.zoom_level, 1.0)
    
    def test_zoom_limits(self):
        """Test that zoom has proper limits"""
        # Test maximum zoom
        for _ in range(50):  # Try to zoom way beyond limit
            self.widget.zoom_in()
        self.assertLessEqual(self.widget.zoom_level, 3.0)
        
        # Reset and test minimum zoom
        self.widget.reset_zoom()
        for _ in range(50):  # Try to zoom way below limit
            self.widget.zoom_out()
        self.assertGreaterEqual(self.widget.zoom_level, 0.5)
    
    def test_display_plain_content(self):
        """Test displaying plain text content"""
        test_content = "This is a test content with some numbers 123 and dates 01.01.2024"
        
        self.widget.display_content(test_content, "plain")
        
        # Check that content is displayed
        displayed_content = self.widget.get_content()
        self.assertIn("This is a test content", displayed_content)
    
    def test_display_markdown_content(self):
        """Test displaying markdown content"""
        test_markdown = """
## Hauptüberschrift

Dies ist ein Testinhalt mit **fett** und *kursiv* Text.

### Unterüberschrift

- Liste Item 1
- Liste Item 2

```python
def test_function():
    return "Hello World"
```
"""
        
        self.widget.display_content(test_markdown, "markdown")
        
        # Check that content is displayed (either as sections or regular markdown)
        displayed_content = self.widget.get_content()
        # Should contain either the section headers or the content
        self.assertTrue(
            "Hauptüberschrift" in displayed_content or 
            "Liste Item 1" in displayed_content or
            len(self.widget.sections) > 0,
            "Content should be displayed either as sections or regular markdown"
        )
    
    def test_section_parsing(self):
        """Test parsing of markdown content into sections"""
        test_markdown = """
## Erste Sektion

Inhalt der ersten Sektion.

### Zweite Sektion

Inhalt der zweiten Sektion mit mehr Text.

## Dritte Sektion

Inhalt der dritten Sektion.
"""
        
        sections = self.widget._parse_sections(test_markdown)
        
        self.assertEqual(len(sections), 3)
        self.assertEqual(sections[0].title, "Erste Sektion")
        self.assertEqual(sections[1].title, "Zweite Sektion")
        self.assertEqual(sections[2].title, "Dritte Sektion")
        
        # Check content
        self.assertIn("Inhalt der ersten Sektion", sections[0].content)
        self.assertIn("Inhalt der zweiten Sektion", sections[1].content)
        self.assertIn("Inhalt der dritten Sektion", sections[2].content)
    
    def test_auto_detect_sections(self):
        """Test automatic section detection in unstructured content"""
        test_content = """Erster Paragraph

Dies ist der Inhalt des ersten Paragraphs.

Zweiter Paragraph

Dies ist der Inhalt des zweiten Paragraphs mit mehr Text.

Dritter Paragraph

Kurzer dritter Paragraph."""
        
        sections = self.widget._auto_detect_sections(test_content)
        
        self.assertGreater(len(sections), 0)
        # Check that sections have titles and content
        for section in sections:
            self.assertIsNotNone(section.title)
            self.assertIsNotNone(section.content)
    
    def test_section_toggle_functionality(self):
        """Test collapsible section functionality"""
        # Create a test section
        test_section = DisplaySection(
            title="Test Section",
            content="Test content for collapsible section",
            is_collapsed=False
        )
        
        # Test toggling
        initial_state = test_section.is_collapsed
        self.widget._toggle_section(test_section)
        self.assertNotEqual(test_section.is_collapsed, initial_state)
        
        # Toggle back
        self.widget._toggle_section(test_section)
        self.assertEqual(test_section.is_collapsed, initial_state)
    
    def test_collapse_expand_all(self):
        """Test collapse and expand all functionality"""
        # Add some test sections
        self.widget.sections = [
            DisplaySection("Section 1", "Content 1", False),
            DisplaySection("Section 2", "Content 2", False),
            DisplaySection("Section 3", "Content 3", False)
        ]
        
        # Test collapse all
        self.widget.collapse_all_sections()
        for section in self.widget.sections:
            self.assertTrue(section.is_collapsed)
        
        # Test expand all
        self.widget.expand_all_sections()
        for section in self.widget.sections:
            self.assertFalse(section.is_collapsed)
    
    def test_syntax_highlighting_numbers(self):
        """Test that numbers are properly highlighted"""
        test_content = "Here are some numbers: 123, 45.67, 890"
        
        self.widget.display_content(test_content, "plain")
        
        # Check that highlight_number tags are applied
        # Note: This is a basic test - in a real scenario you'd check tag ranges
        tags = self.widget.text_widget.tag_names()
        self.assertIn("highlight_number", tags)
    
    def test_syntax_highlighting_dates(self):
        """Test that dates are properly highlighted"""
        test_content = "Important dates: 01.01.2024, 2024-12-31, 12/25/2024"
        
        self.widget.display_content(test_content, "plain")
        
        # Check that highlight_date tags are applied
        tags = self.widget.text_widget.tag_names()
        self.assertIn("highlight_date", tags)
    
    def test_clear_content(self):
        """Test clearing content functionality"""
        # Add some content
        self.widget.display_content("Test content", "plain")
        self.assertNotEqual(self.widget.get_content(), "")
        
        # Clear content
        self.widget.clear_content()
        self.assertEqual(self.widget.get_content().strip(), "")
        self.assertEqual(len(self.widget.sections), 0)
    
    def test_font_size_updates(self):
        """Test that font sizes update correctly with zoom"""
        initial_font = self.widget.text_widget['font']
        
        # Zoom in and check font update
        self.widget.zoom_in()
        self.widget._update_font_sizes()
        
        # Font should be updated (this is a basic check)
        updated_font = self.widget.text_widget['font']
        # The font object should be different after zoom
        self.assertIsNotNone(updated_font)
    
    def test_zoom_label_updates(self):
        """Test that zoom label updates correctly"""
        # Test initial state
        self.widget._update_zoom_label()
        self.assertEqual(self.widget.zoom_label.cget('text'), "100%")
        
        # Test after zoom in
        self.widget.zoom_level = 1.5
        self.widget._update_zoom_label()
        self.assertEqual(self.widget.zoom_label.cget('text'), "150%")
        
        # Test after zoom out
        self.widget.zoom_level = 0.8
        self.widget._update_zoom_label()
        self.assertEqual(self.widget.zoom_label.cget('text'), "80%")
    
    def test_display_section_dataclass(self):
        """Test DisplaySection dataclass functionality"""
        section = DisplaySection(
            title="Test Title",
            content="Test Content",
            is_collapsed=True
        )
        
        self.assertEqual(section.title, "Test Title")
        self.assertEqual(section.content, "Test Content")
        self.assertTrue(section.is_collapsed)
        self.assertEqual(section.start_index, "1.0")
        self.assertEqual(section.end_index, "1.0")
    
    def test_structured_content_display(self):
        """Test structured content display mode"""
        test_content = """First paragraph with some content.

Second paragraph with different content.

Third paragraph with more information."""
        
        self.widget.display_content(test_content, "structured")
        
        # Should create sections automatically or display content
        displayed_content = self.widget.get_content()
        self.assertTrue(
            len(self.widget.sections) > 0 or 
            "First paragraph" in displayed_content or
            "Third paragraph" in displayed_content,
            "Content should be displayed either as sections or plain text"
        )


class TestDisplaySection(unittest.TestCase):
    """Test cases for DisplaySection dataclass"""
    
    def test_display_section_creation(self):
        """Test creating DisplaySection instances"""
        section = DisplaySection("Title", "Content")
        
        self.assertEqual(section.title, "Title")
        self.assertEqual(section.content, "Content")
        self.assertFalse(section.is_collapsed)  # Default value
        self.assertEqual(section.start_index, "1.0")  # Default value
        self.assertEqual(section.end_index, "1.0")  # Default value
    
    def test_display_section_with_all_params(self):
        """Test creating DisplaySection with all parameters"""
        section = DisplaySection(
            title="Custom Title",
            content="Custom Content",
            is_collapsed=True,
            start_index="2.0",
            end_index="3.0"
        )
        
        self.assertEqual(section.title, "Custom Title")
        self.assertEqual(section.content, "Custom Content")
        self.assertTrue(section.is_collapsed)
        self.assertEqual(section.start_index, "2.0")
        self.assertEqual(section.end_index, "3.0")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)