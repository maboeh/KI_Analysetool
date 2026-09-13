
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
from analysis import (
    AnalysisErrorCode,
    analyze_pdf,
    analyze_text,
    extract_content,
    extract_transkript,
    text_extraction_youtube_website,
)

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
            self.assertIn("pdf", result.lower())
            self.assertNotIn("%PDF-1.4", result)
        finally:
            os.unlink(path)

    def test_extract_content_returns_typed_invalid_input_error(self):
        outcome = extract_content("")
        self.assertFalse(outcome.success)
        self.assertEqual(outcome.error.code, AnalysisErrorCode.INVALID_INPUT)

    def test_extract_content_reads_supported_local_text(self):
        with tempfile.NamedTemporaryFile(suffix=".md", mode="w", encoding="utf-8", delete=False) as file:
            file.write("Lokaler Inhalt")
            path = file.name
        try:
            outcome = extract_content(path)
            self.assertTrue(outcome.success)
            self.assertEqual(outcome.content, "Lokaler Inhalt")
            self.assertEqual(outcome.source_type, "file")
        finally:
            os.unlink(path)

    def test_analyze_pdf_invalid_path_returns_typed_error(self):
        outcome = analyze_pdf("missing.pdf", "Analysiere")
        self.assertFalse(outcome.success)
        self.assertEqual(outcome.error.code, AnalysisErrorCode.FILE_NOT_FOUND)

    @patch('analysis.get_api_key', return_value="secret")
    @patch('analysis.OpenAI')
    def test_analyze_pdf_returns_typed_success_and_cleans_up(self, mock_openai, _mock_key):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as pdf_file:
            pdf_file.write(b"%PDF-1.4 test")
            path = pdf_file.name
        client = mock_openai.return_value
        remote_file = SimpleNamespace(id="file-1")
        assistant = SimpleNamespace(id="assistant-1")
        thread = SimpleNamespace(id="thread-1")
        run = SimpleNamespace(
            id="run-1",
            status="completed",
            usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5)
        )
        message = SimpleNamespace(
            role="assistant",
            content=[SimpleNamespace(text=SimpleNamespace(value="PDF result"))]
        )
        client.files.create.return_value = remote_file
        client.beta.assistants.create.return_value = assistant
        client.beta.threads.create.return_value = thread
        client.beta.threads.runs.create.return_value = run
        client.beta.threads.messages.list.return_value = SimpleNamespace(data=[message])
        try:
            outcome = analyze_pdf(path, "Analysiere")
        finally:
            os.unlink(path)
        self.assertTrue(outcome.success)
        self.assertEqual(outcome.content, "PDF result")
        self.assertEqual(outcome.prompt_tokens + outcome.completion_tokens, 15)
        client.files.delete.assert_called_once_with("file-1")
        client.beta.assistants.delete.assert_called_once_with("assistant-1")
        client.beta.threads.delete.assert_called_once_with("thread-1")

    @patch('analysis.get_api_key', return_value=None)
    def test_analyze_text_returns_typed_missing_key_error(self, _mock_key):
        outcome = analyze_text("Test")
        self.assertFalse(outcome.success)
        self.assertEqual(outcome.error.code, AnalysisErrorCode.MISSING_API_KEY)
        self.assertEqual(outcome.content, "")

    @patch('analysis.get_api_key', return_value="secret")
    @patch('analysis.OpenAI')
    def test_analyze_text_does_not_expose_sdk_error(self, mock_openai, _mock_key):
        mock_openai.return_value.chat.completions.create.side_effect = ValueError("secret detail")
        outcome = analyze_text("Test")
        self.assertFalse(outcome.success)
        self.assertEqual(outcome.error.code, AnalysisErrorCode.UNKNOWN)
        self.assertNotIn("secret detail", outcome.error.user_message)


if __name__ == '__main__':
    unittest.main()
