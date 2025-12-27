import unittest
from unittest.mock import patch
from security import validate_url, SecurityException
import socket

class TestSecurity(unittest.TestCase):
    @patch('socket.getaddrinfo')
    def test_valid_url(self, mock_getaddrinfo):
        # Mock a public IP for google.com
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('142.250.190.46', 80))
        ]
        try:
            validate_url("https://google.com")
        except SecurityException as e:
            self.fail(f"validate_url raised SecurityException unexpectedly: {e}")

    def test_invalid_scheme(self):
        with self.assertRaises(SecurityException) as cm:
            validate_url("ftp://example.com")
        self.assertIn("Invalid URL scheme", str(cm.exception))

    @patch('socket.getaddrinfo')
    def test_localhost_ip(self, mock_getaddrinfo):
        mock_getaddrinfo.return_value = [
             (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('127.0.0.1', 80))
        ]
        with self.assertRaises(SecurityException) as cm:
            validate_url("http://127.0.0.1")
        self.assertIn("URL points to a restricted IP address", str(cm.exception))

    @patch('socket.getaddrinfo')
    def test_private_ip(self, mock_getaddrinfo):
        mock_getaddrinfo.return_value = [
             (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('192.168.1.1', 80))
        ]
        with self.assertRaises(SecurityException) as cm:
            validate_url("http://192.168.1.1")
        self.assertIn("URL points to a restricted IP address", str(cm.exception))

    @patch('socket.getaddrinfo')
    def test_link_local_ip(self, mock_getaddrinfo):
        # AWS Metadata IP
        mock_getaddrinfo.return_value = [
             (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('169.254.169.254', 80))
        ]
        with self.assertRaises(SecurityException) as cm:
            validate_url("http://169.254.169.254")
        self.assertIn("URL points to a restricted IP address", str(cm.exception))

    @patch('socket.getaddrinfo')
    def test_ipv6_localhost_ip(self, mock_getaddrinfo):
        mock_getaddrinfo.return_value = [
             (socket.AF_INET6, socket.SOCK_STREAM, 6, '', ('::1', 80, 0, 0))
        ]
        with self.assertRaises(SecurityException) as cm:
            # Note: urllib.parse handles bracketed IPv6 literals in hostname
            validate_url("http://[::1]")
        self.assertIn("URL points to a restricted IP address", str(cm.exception))

    def test_no_hostname(self):
        with self.assertRaises(SecurityException) as cm:
            validate_url("https://")
        self.assertIn("No hostname found", str(cm.exception))

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
