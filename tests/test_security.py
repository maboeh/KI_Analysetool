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

if __name__ == '__main__':
    unittest.main()
