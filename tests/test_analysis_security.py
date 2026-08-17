
import unittest
from unittest.mock import patch, MagicMock
from analysis import extract_text_from_website

class TestAnalysisSecurity(unittest.TestCase):

    @patch('analysis.requests.get')
    def test_extract_text_from_website_no_timeout(self, mock_get):
        # This test verifies that we can call the function, but since we are mocking,
        # we can't easily prove the LACK of timeout without inspecting the call args.
        # But we can check if it accepts arbitrary schemes if we mock the response.

        mock_response = MagicMock()
        mock_response.text = "<html><body><p>Test Content</p></body></html>"
        mock_get.return_value = mock_response

        # Test with a valid URL
        result = extract_text_from_website("http://example.com")
        self.assertEqual(result.strip(), "Test Content")

        # Verify requests.get was called.
        # We want to ensure 'timeout' is in kwargs in the future.
        args, kwargs = mock_get.call_args
        # NOW, timeout SHOULD be present.
        self.assertIn('timeout', kwargs, "Timeout should be present")
        self.assertEqual(kwargs['timeout'], 10, "Timeout should be 10 seconds")

    def test_extract_text_from_website_bad_scheme(self):
        # We want to ensure that non-http/https schemes are rejected.
        # Currently they are passed to requests.get
        with patch('analysis.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.text = "<html><body><p>File Content</p></body></html>"
            mock_get.return_value = mock_response

            # This should now raise a ValueError
            with self.assertRaises(ValueError) as cm:
                extract_text_from_website("file:///etc/passwd")

            self.assertIn("Invalid URL scheme", str(cm.exception))

            # requests.get should NOT be called
            mock_get.assert_not_called()

if __name__ == '__main__':
    unittest.main()
