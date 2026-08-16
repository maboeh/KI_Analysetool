"""
Tests for the Excel export functionality.

This module contains comprehensive tests for the ExcelExporter class,
including tests for various data structures and export scenarios.
"""

import unittest
import tempfile
import os
from datetime import datetime
from unittest.mock import patch, MagicMock

import pandas as pd
from openpyxl import load_workbook

from excel_exporter import (
    ExcelExporter, ExportTemplate, create_excel_export_filename, 
    validate_export_data
)
from data_models import (
    ProcessedResult, StructuredData, DataTable, NamedEntity, 
    NumericValue, TemporalValue, EntityType, SourceInfo, ResultMetadata
)


class TestExcelExporter(unittest.TestCase):
    """Test cases for ExcelExporter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.exporter = ExcelExporter()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create sample data
        self.sample_table = DataTable(
            headers=['Name', 'Alter', 'Stadt'],
            rows=[
                ['Max Mustermann', '30', 'Berlin'],
                ['Anna Schmidt', '25', 'München'],
                ['Peter Weber', '35', 'Hamburg']
            ],
            title='Personen'
        )
        
        self.sample_entities = [
            NamedEntity(
                text='Berlin',
                entity_type=EntityType.LOCATION,
                confidence=0.95,
                start_pos=10,
                end_pos=16
            ),
            NamedEntity(
                text='Max Mustermann',
                entity_type=EntityType.PERSON,
                confidence=0.88,
                start_pos=0,
                end_pos=13
            )
        ]
        
        self.sample_numeric_values = [
            NumericValue(value=100.50, unit='EUR', value_type='currency', context='Preis'),
            NumericValue(value=75, unit='%', value_type='percentage', context='Erfolgsrate')
        ]
        
        self.sample_temporal_data = [
            TemporalValue(
                value=datetime(2024, 1, 15, 10, 30),
                original_text='15. Januar 2024',
                precision='day'
            )
        ]
        
        self.sample_structured_data = StructuredData(
            tables=[self.sample_table],
            entities=self.sample_entities,
            numeric_values=self.sample_numeric_values,
            temporal_data=self.sample_temporal_data
        )
        
        self.sample_result = ProcessedResult(
            content='Dies ist ein Beispiel-Analyseergebnis mit verschiedenen Datentypen.',
            source_info=SourceInfo(type='test', file_name='test.txt'),
            extracted_data=self.sample_structured_data,
            metadata=ResultMetadata(analysis_type='Test-Analyse')
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary files
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)
    
    def test_default_templates_creation(self):
        """Test that default templates are created correctly."""
        templates = self.exporter.get_available_templates()
        
        self.assertIn('complete', templates)
        self.assertIn('tables_only', templates)
        self.assertIn('summary', templates)
        
        self.assertEqual(templates['complete'], 'Exportiert alle verfügbaren Daten in separate Arbeitsblätter')
    
    def test_export_complete_result(self):
        """Test exporting a complete result with all data types."""
        file_path = os.path.join(self.temp_dir, 'test_complete.xlsx')
        
        success = self.exporter.export_to_excel(self.sample_result, file_path, 'complete')
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(file_path))
        
        # Verify Excel file structure
        workbook = load_workbook(file_path)
        sheet_names = workbook.sheetnames
        
        self.assertIn('Zusammenfassung', sheet_names)
        self.assertIn('Tabellen', sheet_names)
        self.assertIn('Entitäten', sheet_names)
        self.assertIn('Numerische Daten', sheet_names)
        self.assertIn('Zeitdaten', sheet_names)
    
    def test_export_tables_only_template(self):
        """Test exporting with tables-only template."""
        file_path = os.path.join(self.temp_dir, 'test_tables_only.xlsx')
        
        success = self.exporter.export_to_excel(self.sample_result, file_path, 'tables_only')
        
        self.assertTrue(success)
        
        workbook = load_workbook(file_path)
        sheet_names = workbook.sheetnames
        
        self.assertIn('Zusammenfassung', sheet_names)
        self.assertIn('Tabellen', sheet_names)
        self.assertNotIn('Entitäten', sheet_names)
        self.assertNotIn('Numerische Daten', sheet_names)
    
    def test_export_summary_template(self):
        """Test exporting with summary template."""
        file_path = os.path.join(self.temp_dir, 'test_summary.xlsx')
        
        success = self.exporter.export_to_excel(self.sample_result, file_path, 'summary')
        
        self.assertTrue(success)
        
        workbook = load_workbook(file_path)
        sheet_names = workbook.sheetnames
        
        self.assertIn('Zusammenfassung', sheet_names)
        self.assertNotIn('Tabellen', sheet_names)
    
    def test_export_empty_result(self):
        """Test exporting a result with no structured data."""
        empty_result = ProcessedResult(
            content='Nur Text ohne strukturierte Daten',
            metadata=ResultMetadata(analysis_type='Einfache Analyse')
        )
        
        file_path = os.path.join(self.temp_dir, 'test_empty.xlsx')
        
        success = self.exporter.export_to_excel(empty_result, file_path)
        
        self.assertTrue(success)
        
        workbook = load_workbook(file_path)
        # Should at least have summary sheet
        self.assertIn('Zusammenfassung', workbook.sheetnames)
    
    def test_export_structured_data_directly(self):
        """Test exporting StructuredData directly."""
        file_path = os.path.join(self.temp_dir, 'test_structured.xlsx')
        
        success = self.exporter.export_structured_data_to_excel(
            self.sample_structured_data, file_path
        )
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(file_path))
    
    def test_table_data_integrity(self):
        """Test that table data is exported correctly."""
        file_path = os.path.join(self.temp_dir, 'test_table_data.xlsx')
        
        self.exporter.export_to_excel(self.sample_result, file_path)
        
        # Read back the Excel file and verify table data
        df = pd.read_excel(file_path, sheet_name='Tabellen', skiprows=2, nrows=3)
        
        self.assertEqual(len(df), 3)  # 3 data rows
        self.assertEqual(list(df.columns), ['Name', 'Alter', 'Stadt'])
        self.assertEqual(df.iloc[0]['Name'], 'Max Mustermann')
        self.assertEqual(df.iloc[1]['Stadt'], 'München')
    
    def test_entities_data_integrity(self):
        """Test that entity data is exported correctly."""
        file_path = os.path.join(self.temp_dir, 'test_entities.xlsx')
        
        self.exporter.export_to_excel(self.sample_result, file_path)
        
        df = pd.read_excel(file_path, sheet_name='Entitäten')
        
        self.assertEqual(len(df), 2)  # 2 entities
        self.assertIn('Berlin', df['Text'].values)
        self.assertIn('Max Mustermann', df['Text'].values)
        self.assertIn('location', df['Typ'].values)
        self.assertIn('person', df['Typ'].values)
    
    def test_numeric_data_integrity(self):
        """Test that numeric data is exported correctly."""
        file_path = os.path.join(self.temp_dir, 'test_numeric.xlsx')
        
        self.exporter.export_to_excel(self.sample_result, file_path)
        
        df = pd.read_excel(file_path, sheet_name='Numerische Daten')
        
        self.assertEqual(len(df), 2)  # 2 numeric values
        self.assertIn(100.50, df['Wert'].values)
        self.assertIn(75, df['Wert'].values)
        self.assertIn('EUR', df['Einheit'].values)
        self.assertIn('%', df['Einheit'].values)
    
    def test_temporal_data_integrity(self):
        """Test that temporal data is exported correctly."""
        file_path = os.path.join(self.temp_dir, 'test_temporal.xlsx')
        
        self.exporter.export_to_excel(self.sample_result, file_path)
        
        df = pd.read_excel(file_path, sheet_name='Zeitdaten')
        
        self.assertEqual(len(df), 1)  # 1 temporal value
        self.assertIn('15. Januar 2024', df['Original Text'].values)
        self.assertIn('day', df['Präzision'].values)
    
    def test_multiple_tables_export(self):
        """Test exporting multiple tables."""
        # Add another table
        second_table = DataTable(
            headers=['Produkt', 'Preis'],
            rows=[['Laptop', '999'], ['Maus', '25']],
            title='Produkte'
        )
        
        self.sample_result.extracted_data.tables.append(second_table)
        
        file_path = os.path.join(self.temp_dir, 'test_multiple_tables.xlsx')
        
        success = self.exporter.export_to_excel(self.sample_result, file_path)
        
        self.assertTrue(success)
        
        # Verify both tables are in the file
        workbook = load_workbook(file_path)
        tables_sheet = workbook['Tabellen']
        
        # Check for both table titles
        cell_values = [cell.value for row in tables_sheet.iter_rows() for cell in row if cell.value]
        self.assertIn('Personen', cell_values)
        self.assertIn('Produkte', cell_values)
    
    def test_custom_template(self):
        """Test adding and using a custom template."""
        custom_template = ExportTemplate(
            name='Nur Entitäten',
            description='Exportiert nur Entitätsdaten',
            include_summary=False,
            include_tables=False,
            include_numeric_data=False,
            include_temporal_data=False
        )
        
        self.exporter.add_custom_template('entities_only', custom_template)
        
        file_path = os.path.join(self.temp_dir, 'test_custom.xlsx')
        
        success = self.exporter.export_to_excel(self.sample_result, file_path, 'entities_only')
        
        self.assertTrue(success)
        
        workbook = load_workbook(file_path)
        sheet_names = workbook.sheetnames
        
        self.assertIn('Entitäten', sheet_names)
        self.assertNotIn('Zusammenfassung', sheet_names)
        self.assertNotIn('Tabellen', sheet_names)
    
    def test_preview_export_structure(self):
        """Test export preview functionality."""
        preview = self.exporter.preview_export_structure(self.sample_result, 'complete')
        
        self.assertEqual(preview['template'], 'Vollständiger Export')
        self.assertIn('Zusammenfassung', preview['sheets'])
        self.assertIn('Tabellen', preview['sheets'])
        self.assertIn('Entitäten', preview['sheets'])
        
        self.assertEqual(preview['data_summary']['tables'], 1)
        self.assertEqual(preview['data_summary']['entities'], 2)
        self.assertEqual(preview['data_summary']['numeric_values'], 2)
        self.assertEqual(preview['data_summary']['temporal_data'], 1)
    
    def test_export_with_invalid_path(self):
        """Test export with invalid file path."""
        invalid_path = '/invalid/path/test.xlsx'
        
        success = self.exporter.export_to_excel(self.sample_result, invalid_path)
        
        self.assertFalse(success)
    
    def test_export_with_special_characters(self):
        """Test export with special characters in data."""
        special_table = DataTable(
            headers=['Name', 'Beschreibung'],
            rows=[
                ['Müller & Co.', 'Spezial-Zeichen: äöüß'],
                ['Test "Quotes"', 'Umlaute: ÄÖÜ']
            ],
            title='Spezial-Zeichen Test'
        )
        
        result_with_special = ProcessedResult(
            content='Test mit Spezialzeichen: äöüß "quotes" & symbols',
            extracted_data=StructuredData(tables=[special_table]),
            metadata=ResultMetadata(analysis_type='Spezialzeichen-Test')
        )
        
        file_path = os.path.join(self.temp_dir, 'test_special.xlsx')
        
        success = self.exporter.export_to_excel(result_with_special, file_path)
        
        self.assertTrue(success)
        
        # Verify special characters are preserved
        df = pd.read_excel(file_path, sheet_name='Tabellen', skiprows=2, nrows=2)
        self.assertIn('Müller & Co.', df['Name'].values)
        self.assertIn('Spezial-Zeichen: äöüß', df['Beschreibung'].values)


class TestExcelExportUtilities(unittest.TestCase):
    """Test cases for Excel export utility functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_result = ProcessedResult(
            content='Test content',
            metadata=ResultMetadata(analysis_type='Test Analysis')
        )
    
    def test_create_excel_export_filename(self):
        """Test filename generation."""
        filename = create_excel_export_filename(self.sample_result)
        
        self.assertTrue(filename.endswith('.xlsx'))
        self.assertIn('analyse_ergebnis', filename)
        self.assertIn('test_analysis', filename)
        
        # Test with custom base name
        custom_filename = create_excel_export_filename(self.sample_result, 'custom_export')
        self.assertIn('custom_export', custom_filename)
    
    def test_validate_export_data_with_data(self):
        """Test validation with exportable data."""
        # Add some structured data
        table = DataTable(headers=['A', 'B'], rows=[['1', '2']])
        self.sample_result.extracted_data.tables = [table]
        
        validation = validate_export_data(self.sample_result)
        
        self.assertTrue(validation['has_exportable_data'])
        self.assertIn('tables', validation['data_types'])
        self.assertEqual(len(validation['warnings']), 0)
    
    def test_validate_export_data_without_data(self):
        """Test validation without exportable data."""
        empty_result = ProcessedResult(
            content='',
            metadata=ResultMetadata(analysis_type='Empty')
        )
        
        validation = validate_export_data(empty_result)
        
        self.assertFalse(validation['has_exportable_data'])
        self.assertIn('Keine strukturierten Daten zum Exportieren gefunden', validation['warnings'])
        self.assertIn('Kein Textinhalt vorhanden', validation['warnings'])
    
    def test_validate_export_data_with_entities(self):
        """Test validation with entity data."""
        entity = NamedEntity(text='Test', entity_type=EntityType.PERSON, confidence=0.9)
        self.sample_result.extracted_data.entities = [entity]
        
        validation = validate_export_data(self.sample_result)
        
        self.assertTrue(validation['has_exportable_data'])
        self.assertIn('entities', validation['data_types'])
    
    def test_validate_export_data_with_numeric_values(self):
        """Test validation with numeric data."""
        numeric = NumericValue(value=42, unit='kg')
        self.sample_result.extracted_data.numeric_values = [numeric]
        
        validation = validate_export_data(self.sample_result)
        
        self.assertTrue(validation['has_exportable_data'])
        self.assertIn('numeric_values', validation['data_types'])
    
    def test_validate_export_data_with_temporal_data(self):
        """Test validation with temporal data."""
        temporal = TemporalValue(
            value=datetime.now(),
            original_text='heute',
            precision='day'
        )
        self.sample_result.extracted_data.temporal_data = [temporal]
        
        validation = validate_export_data(self.sample_result)
        
        self.assertTrue(validation['has_exportable_data'])
        self.assertIn('temporal_data', validation['data_types'])


class TestExportTemplate(unittest.TestCase):
    """Test cases for ExportTemplate class."""
    
    def test_default_template_creation(self):
        """Test creating a template with default values."""
        template = ExportTemplate(
            name='Test Template',
            description='Test description'
        )
        
        self.assertTrue(template.include_summary)
        self.assertTrue(template.include_tables)
        self.assertTrue(template.include_entities)
        self.assertIsNotNone(template.sheet_names)
        self.assertEqual(template.sheet_names['summary'], 'Zusammenfassung')
    
    def test_custom_template_creation(self):
        """Test creating a template with custom values."""
        custom_sheet_names = {
            'summary': 'Übersicht',
            'tables': 'Daten',
            'entities': 'Begriffe'
        }
        
        template = ExportTemplate(
            name='Custom Template',
            description='Custom description',
            include_numeric_data=False,
            include_temporal_data=False,
            sheet_names=custom_sheet_names
        )
        
        self.assertFalse(template.include_numeric_data)
        self.assertFalse(template.include_temporal_data)
        self.assertEqual(template.sheet_names['summary'], 'Übersicht')
        self.assertEqual(template.sheet_names['tables'], 'Daten')


if __name__ == '__main__':
    unittest.main()