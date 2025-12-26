import unittest
from unittest.mock import patch, MagicMock
from security import validate_url, SecurityException
import socket
from analysis import extract_text_from_website

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

    @patch('requests.Session')
    @patch('socket.getaddrinfo')
    def test_extract_text_blocks_unsafe(self, mock_getaddrinfo, mock_session_cls):
        # Ensure extract_text_from_website now calls validate_url
        # which raises SecurityException for unsafe URLs

        mock_getaddrinfo.return_value = [
             (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('127.0.0.1', 80))
        ]

        url = "http://localhost:8080/sensitive"

        with self.assertRaises(SecurityException):
            extract_text_from_website(url)

    @patch('requests.Session')
    @patch('socket.getaddrinfo')
    def test_extract_text_allows_safe(self, mock_getaddrinfo, mock_session_cls):
        url = "https://example.com"

        mock_getaddrinfo.return_value = [
             (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 80))
        ]

        mock_session = mock_session_cls.return_value
        mock_response = MagicMock()
        mock_response.text = "<html><body>Safe content</body></html>"
        mock_response.is_redirect = False
        mock_session.get.return_value = mock_response

        result = extract_text_from_website(url)

        self.assertIn("Safe content", result)
        mock_session.get.assert_called_once()
        # Verify timeout was added
        args, kwargs = mock_session.get.call_args
        self.assertEqual(kwargs.get('timeout'), 10)
        self.assertEqual(kwargs.get('allow_redirects'), False)


if __name__ == '__main__':
    unittest.main()
