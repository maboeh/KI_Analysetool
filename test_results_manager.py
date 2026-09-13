"""
Tests for the ResultsManager class.

This module contains comprehensive tests for result storage, retrieval,
filtering, and management functionality.
"""

import unittest
import tempfile
import shutil
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from results_manager import ResultsManager
from data_models import (
    ProcessedResult, SourceInfo, ResultMetadata, StructuredData,
    DataTable, NamedEntity, EntityType, Visualization, ChartType,
    Action, ActionType
)


class TestResultsManager(unittest.TestCase):
    """Test cases for ResultsManager functionality."""
    
    def setUp(self):
        """Set up test environment with temporary database and directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_results.db")
        self.results_dir = os.path.join(self.temp_dir, "test_results")
        self.manager = ResultsManager(self.db_path, self.results_dir)
        
        # Create sample results for testing
        self.sample_result1 = self._create_sample_result(
            content="Dies ist ein Testinhalt für die erste Analyse.",
            analysis_type="zusammenfassung",
            source_type="website"
        )
        
        self.sample_result2 = self._create_sample_result(
            content="Zweiter Testinhalt mit numerischen Daten: 100, 200, 300.",
            analysis_type="datenextraktion",
            source_type="excel",
            with_table=True
        )
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def _create_sample_result(self, content="Test content", analysis_type="test", 
                            source_type="text", with_table=False, with_visualization=False):
        """Create a sample ProcessedResult for testing."""
        source_info = SourceInfo(
            type=source_type,
            file_name="test_file.txt" if source_type != "website" else None,
            url="https://example.com" if source_type == "website" else None
        )
        
        metadata = ResultMetadata(
            analysis_type=analysis_type,
            processing_time=1.5,
            model_used="gpt-4",
            tokens_used=150,
            confidence_score=0.85,
            tags=["test", "sample"]
        )
        
        structured_data = StructuredData()
        if with_table:
            table = DataTable(
                headers=["Name", "Wert", "Einheit"],
                rows=[
                    ["Item 1", "100", "EUR"],
                    ["Item 2", "200", "EUR"],
                    ["Item 3", "300", "EUR"]
                ],
                title="Test Tabelle"
            )
            structured_data.tables.append(table)
        
        result = ProcessedResult(
            content=content,
            source_info=source_info,
            extracted_data=structured_data,
            metadata=metadata
        )
        
        if with_visualization:
            viz = Visualization(
                chart_type=ChartType.BAR,
                data_source="test_data"
            )
            result.add_visualization(viz)
        
        return result
    
    def test_save_and_load_result(self):
        """Test saving and loading a result."""
        # Save result
        result_id = self.manager.save_result(self.sample_result1, "Test Result 1")
        self.assertEqual(result_id, self.sample_result1.id)
        
        # Load result
        loaded_result = self.manager.load_result(result_id)
        self.assertIsNotNone(loaded_result)
        self.assertEqual(loaded_result.id, self.sample_result1.id)
        self.assertEqual(loaded_result.content, self.sample_result1.content)
        self.assertEqual(loaded_result.metadata.analysis_type, "zusammenfassung")
    
    def test_save_result_without_name(self):
        """Test saving a result without providing a custom name."""
        result_id = self.manager.save_result(self.sample_result1)
        self.assertEqual(result_id, self.sample_result1.id)
        
        # Check that a title was generated
        summaries = self.manager.list_results()
        self.assertEqual(len(summaries), 1)
        self.assertTrue(len(summaries[0].title) > 0)
    
    def test_load_nonexistent_result(self):
        """Test loading a result that doesn't exist."""
        result = self.manager.load_result("nonexistent_id")
        self.assertIsNone(result)
    
    def test_list_results_empty(self):
        """Test listing results when database is empty."""
        results = self.manager.list_results()
        self.assertEqual(len(results), 0)
    
    def test_list_results_with_data(self):
        """Test listing results with saved data."""
        # Save multiple results
        self.manager.save_result(self.sample_result1, "Result 1")
        self.manager.save_result(self.sample_result2, "Result 2")
        
        # List all results
        results = self.manager.list_results()
        self.assertEqual(len(results), 2)
        
        # Check that results are ordered by creation date (newest first)
        self.assertTrue(results[0].created_at >= results[1].created_at)
    
    def test_filter_by_analysis_type(self):
        """Test filtering results by analysis type."""
        self.manager.save_result(self.sample_result1, "Result 1")
        self.manager.save_result(self.sample_result2, "Result 2")
        
        # Filter by analysis type
        filtered = self.manager.list_results({"analysis_type": "zusammenfassung"})
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].analysis_type, "zusammenfassung")
    
    def test_filter_by_source_type(self):
        """Test filtering results by source type."""
        self.manager.save_result(self.sample_result1, "Result 1")
        self.manager.save_result(self.sample_result2, "Result 2")
        
        # Filter by source type
        filtered = self.manager.list_results({"source_type": "excel"})
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].source_type, "excel")
    
    def test_filter_by_date_range(self):
        """Test filtering results by date range."""
        # Save result with specific date
        old_result = self._create_sample_result()
        old_result.created_at = datetime.now() - timedelta(days=10)
        self.manager.save_result(old_result, "Old Result")
        
        # Save recent result
        self.manager.save_result(self.sample_result1, "Recent Result")
        
        # Filter by date range (last 5 days)
        date_from = datetime.now() - timedelta(days=5)
        filtered = self.manager.list_results({"date_from": date_from})
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].title, "Recent Result")
    
    def test_filter_by_exportable_data(self):
        """Test filtering results by exportable data presence."""
        self.manager.save_result(self.sample_result1, "No Data")
        self.manager.save_result(self.sample_result2, "With Data")
        
        # Filter by exportable data
        filtered = self.manager.list_results({"has_exportable_data": True})
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].title, "With Data")
    
    def test_search_text_filter(self):
        """Test text search in title and content."""
        self.manager.save_result(self.sample_result1, "Erste Analyse")
        self.manager.save_result(self.sample_result2, "Zweite Analyse")
        
        # Search for specific text
        filtered = self.manager.list_results({"search_text": "numerischen"})
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].title, "Zweite Analyse")
    
    def test_delete_result(self):
        """Test deleting a result."""
        # Save result
        result_id = self.manager.save_result(self.sample_result1, "To Delete")
        
        # Verify it exists
        self.assertIsNotNone(self.manager.load_result(result_id))
        
        # Delete result
        success = self.manager.delete_result(result_id)
        self.assertTrue(success)
        
        # Verify it's gone
        self.assertIsNone(self.manager.load_result(result_id))
        
        # Verify JSON file is also deleted
        json_path = Path(self.results_dir) / f"{result_id}.json"
        self.assertFalse(json_path.exists())
    
    def test_delete_nonexistent_result(self):
        """Test deleting a result that doesn't exist."""
        success = self.manager.delete_result("nonexistent_id")
        self.assertFalse(success)
    
    def test_export_result_json(self):
        """Test exporting a result as JSON."""
        result_id = self.manager.save_result(self.sample_result1, "Export Test")
        
        export_path = self.manager.export_result(result_id, "json")
        self.assertIsNotNone(export_path)
        self.assertTrue(os.path.exists(export_path))
        
        # Verify exported content
        import json
        with open(export_path, 'r', encoding='utf-8') as f:
            exported_data = json.load(f)
        
        self.assertEqual(exported_data['id'], result_id)
        self.assertEqual(exported_data['content'], self.sample_result1.content)
    
    def test_export_result_txt(self):
        """Test exporting a result as text."""
        result_id = self.manager.save_result(self.sample_result1, "Export Test")
        
        export_path = self.manager.export_result(result_id, "txt")
        self.assertIsNotNone(export_path)
        self.assertTrue(os.path.exists(export_path))
        
        # Verify exported content contains result content
        with open(export_path, 'r', encoding='utf-8') as f:
            exported_text = f.read()
        
        self.assertIn(self.sample_result1.content, exported_text)
        self.assertIn(result_id, exported_text)
    
    def test_export_result_csv(self):
        """Test exporting a result with table data as CSV."""
        result_id = self.manager.save_result(self.sample_result2, "CSV Export Test")
        
        export_path = self.manager.export_result(result_id, "csv")
        self.assertIsNotNone(export_path)
        self.assertTrue(os.path.exists(export_path))
        
        # Verify CSV content
        with open(export_path, 'r', encoding='utf-8') as f:
            csv_content = f.read()
        
        self.assertIn("Name,Wert,Einheit", csv_content)
        self.assertIn("Item 1,100,EUR", csv_content)
    
    def test_export_result_csv_no_data(self):
        """Test exporting a result without table data as CSV."""
        result_id = self.manager.save_result(self.sample_result1, "No CSV Data")
        
        export_path = self.manager.export_result(result_id, "csv")
        self.assertIsNone(export_path)  # Should return None for no tabular data
    
    def test_export_nonexistent_result(self):
        """Test exporting a result that doesn't exist."""
        export_path = self.manager.export_result("nonexistent_id", "json")
        self.assertIsNone(export_path)
    
    def test_get_statistics(self):
        """Test getting statistics about stored results."""
        # Save results with different characteristics
        self.manager.save_result(self.sample_result1, "Result 1")
        
        result_with_viz = self._create_sample_result(
            analysis_type="visualisierung",
            with_visualization=True
        )
        self.manager.save_result(result_with_viz, "Result with Viz")
        
        stats = self.manager.get_statistics()
        
        self.assertEqual(stats['total_results'], 2)
        self.assertIn('zusammenfassung', stats['by_analysis_type'])
        self.assertIn('visualisierung', stats['by_analysis_type'])
        self.assertEqual(stats['with_visualizations'], 1)
        self.assertEqual(stats['with_exportable_data'], 0)  # sample_result1 has no tables
    
    def test_update_result(self):
        """Test updating an existing result."""
        # Save initial result
        result_id = self.manager.save_result(self.sample_result1, "Original")
        original_updated_at = self.sample_result1.updated_at
        
        # Modify result
        self.sample_result1.content = "Updated content"
        self.sample_result1.metadata.analysis_type = "updated_analysis"
        
        # Update result
        success = self.manager.update_result(self.sample_result1)
        self.assertTrue(success)
        
        # Verify update
        loaded_result = self.manager.load_result(result_id)
        self.assertEqual(loaded_result.content, "Updated content")
        self.assertEqual(loaded_result.metadata.analysis_type, "updated_analysis")
        self.assertGreater(loaded_result.updated_at, original_updated_at)
    
    def test_update_restores_json_when_replace_fails(self):
        result_id = self.manager.save_result(self.sample_result1, "Original")
        self.sample_result1.content = "Must not persist"
        real_replace = os.replace

        def replace_with_failure(source, destination):
            if str(source).endswith(".tmp"):
                raise OSError("replace failed")
            return real_replace(source, destination)

        with patch("results_manager.os.replace", side_effect=replace_with_failure):
            with self.assertRaises(OSError):
                self.manager.update_result(self.sample_result1)

        loaded_result = self.manager.load_result(result_id)
        self.assertEqual(loaded_result.content, "Dies ist ein Testinhalt für die erste Analyse.")

    def test_update_nonexistent_result(self):
        """Test updating a result that doesn't exist."""
        fake_result = self._create_sample_result()
        fake_result.id = "nonexistent_id"
        
        success = self.manager.update_result(fake_result)
        self.assertFalse(success)
    
    def test_database_initialization(self):
        """Test that database is properly initialized."""
        # Create new manager to test initialization
        new_db_path = os.path.join(self.temp_dir, "new_test.db")
        new_manager = ResultsManager(new_db_path, self.results_dir)
        
        # Should be able to save and retrieve results
        result_id = new_manager.save_result(self.sample_result1, "Init Test")
        loaded_result = new_manager.load_result(result_id)
        self.assertIsNotNone(loaded_result)
    
    def test_title_generation(self):
        """Test automatic title generation."""
        # Result with short first line (should use as title)
        result_short_title = self._create_sample_result(
            content="Kurzer Titel\nDies ist der Rest des Inhalts."
        )
        result_id = self.manager.save_result(result_short_title)
        
        summaries = self.manager.list_results()
        self.assertEqual(summaries[0].title, "Kurzer Titel")
        
        # Result with long first line (should generate title from metadata)
        result_long_title = self._create_sample_result(
            content="Dies ist eine sehr lange erste Zeile die definitiv zu lang ist um als Titel verwendet zu werden und daher sollte ein anderer Titel generiert werden."
        )
        self.manager.save_result(result_long_title)
        
        summaries = self.manager.list_results()
        # Should find the result with generated title
        generated_titles = [s.title for s in summaries if "Test" in s.title]
        self.assertTrue(len(generated_titles) > 0)
    
    def test_concurrent_access(self):
        """Test that multiple operations don't interfere with each other."""
        # Save multiple results in sequence
        results = []
        for i in range(5):
            result = self._create_sample_result(
                content=f"Content {i}",
                analysis_type=f"type_{i}"
            )
            result_id = self.manager.save_result(result, f"Result {i}")
            results.append(result_id)
        
        # Verify all results are saved
        all_results = self.manager.list_results()
        self.assertEqual(len(all_results), 5)
        
        # Verify each result can be loaded
        for result_id in results:
            loaded = self.manager.load_result(result_id)
            self.assertIsNotNone(loaded)


if __name__ == '__main__':
    unittest.main()