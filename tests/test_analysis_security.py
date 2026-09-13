
import unittest
from unittest.mock import patch, MagicMock
from analysis import extract_text_from_website
from security import SecurityException

class TestAnalysisSecurity(unittest.TestCase):

    @patch('security.validate_url')
    @patch('security.safe_requests_get')
    def test_extract_text_from_website_no_timeout(self, mock_get, _mock_validate):
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
        self.assertEqual(kwargs['timeout'], 15, "Timeout should be 15 seconds")

    def test_extract_text_from_website_bad_scheme(self):
        with patch('security.safe_requests_get') as mock_get:
            with self.assertRaises(SecurityException) as cm:
                extract_text_from_website("file:///etc/passwd")

            self.assertIn("Invalid URL scheme", str(cm.exception))
            mock_get.assert_not_called()

if __name__ == '__main__':
    unittest.main()
