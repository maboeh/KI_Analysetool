
import unittest
from unittest.mock import patch, MagicMock
from analysis import extract_text_from_website
from security import validate_url


class TestSecurity(unittest.TestCase):

    def test_validate_url_allows_public(self):
        # google.com is public
        url = "https://google.com"
        # We don't want to actually hit the network in unit tests if possible,
        # but validate_url does DNS resolution.
        # For a hermetic test, we should mock socket.gethostbyname
        with patch('socket.gethostbyname') as mock_dns:
            mock_dns.return_value = "8.8.8.8"
            self.assertEqual(validate_url(url), url)

    def test_validate_url_blocks_private(self):
        url = "http://192.168.1.1"
        with patch('socket.gethostbyname') as mock_dns:
            mock_dns.return_value = "192.168.1.1"
            with self.assertRaises(ValueError) as cm:
                validate_url(url)
            self.assertIn("restricted IP", str(cm.exception))

    def test_validate_url_blocks_localhost(self):
        url = "http://localhost"
        with patch('socket.gethostbyname') as mock_dns:
            mock_dns.return_value = "127.0.0.1"
            with self.assertRaises(ValueError) as cm:
                validate_url(url)
            self.assertIn("restricted IP", str(cm.exception))

    def test_validate_url_blocks_scheme(self):
        url = "ftp://example.com"
        with self.assertRaises(ValueError) as cm:
            validate_url(url)
        self.assertIn("Invalid scheme", str(cm.exception))

    @patch('requests.get')
    def test_extract_text_blocks_unsafe(self, mock_get):
        # Ensure extract_text_from_website now calls validate_url
        # which raises ValueError for unsafe URLs

        url = "http://localhost:8080/sensitive"
        with patch('socket.gethostbyname') as mock_dns:
            mock_dns.return_value = "127.0.0.1"
            with self.assertRaises(ValueError):
                extract_text_from_website(url)

        # requests.get should NOT have been called
        mock_get.assert_not_called()

    @patch('requests.get')
    def test_extract_text_allows_safe(self, mock_get):
        url = "https://example.com"

        mock_response = MagicMock()
        mock_response.text = "<html><body>Safe content</body></html>"
        mock_get.return_value = mock_response

        with patch('socket.gethostbyname') as mock_dns:
            mock_dns.return_value = "93.184.216.34"  # example.com IP
            result = extract_text_from_website(url)

        self.assertIn("Safe content", result)
        mock_get.assert_called_once()
        # Verify timeout was added
        args, kwargs = mock_get.call_args
        self.assertEqual(kwargs.get('timeout'), 10)


if __name__ == '__main__':
    unittest.main()
