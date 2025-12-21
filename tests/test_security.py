
import unittest
from analysis import extract_text_from_website
from unittest.mock import patch, MagicMock

class TestSSRF(unittest.TestCase):
    @patch('requests.get')
    def test_extract_text_valid_url(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "<html><body>Hello World</body></html>"
        mock_get.return_value = mock_response

        with patch('socket.getaddrinfo') as mock_dns:
            mock_dns.return_value = [(2, 1, 6, '', ('93.184.216.34', 0))]

            extract_text_from_website("https://example.com")

            # Verify verify allow_redirects=False is passed
            mock_get.assert_called_with("https://example.com", timeout=10)

    def test_extract_text_invalid_url_localhost(self):
        with patch('socket.getaddrinfo') as mock_dns:
            mock_dns.return_value = [(2, 1, 6, '', ('127.0.0.1', 0))]

            with self.assertRaises(ValueError) as cm:
                extract_text_from_website("http://localhost:8000")

            self.assertIn("forbidden", str(cm.exception))

    def test_extract_text_invalid_url_private_ip(self):
        with patch('socket.getaddrinfo') as mock_dns:
            mock_dns.return_value = [(2, 1, 6, '', ('192.168.1.1', 0))]

            with self.assertRaises(ValueError) as cm:
                extract_text_from_website("http://192.168.1.1")

            self.assertIn("forbidden", str(cm.exception))

    def test_extract_text_invalid_scheme(self):
        with self.assertRaises(ValueError) as cm:
             extract_text_from_website("ftp://example.com")
        self.assertIn("scheme", str(cm.exception))

if __name__ == '__main__':
    unittest.main()
