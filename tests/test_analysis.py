
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from analysis import extract_transkript, text_extraction_youtube_website

class TestAnalysis(unittest.TestCase):
    @patch('analysis.YouTubeTranscriptApi')
    def test_extract_transkript(self, mock_api):
        # Mock the transcript return value
        mock_api.get_transcript.return_value = [
            {"text": "Hello", "start": 0.0, "duration": 1.0},
            {"text": "World", "start": 1.0, "duration": 1.0}
        ]

        # Test with a dummy YouTube link
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        result = extract_transkript(url)

        # Verify the output
        expected_output = "Hello World "
        self.assertEqual(result, expected_output)

        # Verify that get_transcript was called with correct arguments
        mock_api.get_transcript.assert_called_with('dQw4w9WgXcQ', languages=['de', 'en'])

    @patch('analysis.YouTubeTranscriptApi')
    def test_extract_transkript_youtu_be(self, mock_api):
        # Mock the transcript return value
        mock_api.get_transcript.return_value = [
            {"text": "Short", "start": 0.0, "duration": 1.0},
            {"text": "Link", "start": 1.0, "duration": 1.0}
        ]

        # Test with a dummy YouTube link
        url = "https://youtu.be/dQw4w9WgXcQ"
        result = extract_transkript(url)

        # Verify the output
        expected_output = "Short Link "
        self.assertEqual(result, expected_output)
        mock_api.get_transcript.assert_called_with('dQw4w9WgXcQ', languages=['de', 'en'])

    @patch('analysis.YouTubeTranscriptApi')
    def test_extract_transkript_empty(self, mock_api):
        # Mock empty transcript
        mock_api.get_transcript.return_value = []

        url = "https://www.youtube.com/watch?v=empty"
        result = extract_transkript(url)

        self.assertEqual(result, "")

    def test_binary_file_not_read_as_text(self):
        """Non-text files must not be opened with text encoding."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4 fake pdf content")
            path = f.name
        try:
            result = text_extraction_youtube_website(path)
            self.assertIn("PDF", result)
            self.assertNotIn("%PDF-1.4", result)
        finally:
            os.unlink(path)


if __name__ == '__main__':
    unittest.main()
