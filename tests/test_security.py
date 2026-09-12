
import unittest
import logging
import logging.handlers
import os
import tempfile
from unittest.mock import patch, MagicMock
from security import validate_url, SecurityException
from config import SecretFilter
import analysis
import security
import socket

class TestSecurity(unittest.TestCase):
    @patch('socket.getaddrinfo')
    def test_valid_url(self, mock_getaddrinfo):
        # Mock a public IP for google.com
        # family, type, proto, canonname, sockaddr
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('142.250.190.46', 80))
        ]
        try:
            # The new validate_url returns None on success, not the URL
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
        self.assertIn("blocked hostname", str(cm.exception).lower())

    @patch('socket.getaddrinfo')
    def test_private_ip(self, mock_getaddrinfo):
        mock_getaddrinfo.return_value = [
             (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('192.168.1.1', 80))
        ]
        with self.assertRaises(SecurityException) as cm:
            validate_url("http://192.168.1.1")
        self.assertIn("restricted", str(cm.exception).lower())

    @patch('socket.getaddrinfo')
    def test_link_local_ip(self, mock_getaddrinfo):
        # AWS Metadata IP
        mock_getaddrinfo.return_value = [
             (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('169.254.169.254', 80))
        ]
        with self.assertRaises(SecurityException) as cm:
            validate_url("http://169.254.169.254")
        self.assertIn("blocked", str(cm.exception).lower())

    @patch('socket.getaddrinfo')
    def test_ipv6_localhost_ip(self, mock_getaddrinfo):
        mock_getaddrinfo.return_value = [
             (socket.AF_INET6, socket.SOCK_STREAM, 6, '', ('::1', 80, 0, 0))
        ]
        with self.assertRaises(SecurityException) as cm:
            validate_url("http://[::1]")
        self.assertIn("blocked", str(cm.exception).lower())

    def test_no_hostname(self):
        with self.assertRaises(SecurityException) as cm:
            validate_url("https://")
        self.assertIn("No hostname found", str(cm.exception))


class TestSecretFilter(unittest.TestCase):

    def test_printf_style_secret_redacted(self):
        logger = logging.getLogger("test_secret_filter")
        logger.setLevel(logging.INFO)
        handler = logging.handlers.MemoryHandler(100)
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addFilter(SecretFilter())
        logger.addHandler(handler)

        logger.info("Key: %s", "sk-abcdefghijklmnopqrstuvwxyz1234567890")
        output = handler.buffer[-1].getMessage()
        self.assertNotIn("sk-abc", output)
        self.assertIn("***REDACTED***", output)

        logger.removeHandler(handler)


class TestSafeRequestsGet(unittest.TestCase):

    @patch('security.requests.Session')
    @patch('socket.getaddrinfo')
    def test_redirect_to_unsafe_url_blocked(self, mock_getaddrinfo, mock_session_cls):
        """Redirects that end in an unsafe URL must be blocked before the request."""
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 80))
        ]

        mock_safe_response = MagicMock()
        mock_safe_response.is_redirect = True
        mock_safe_response.headers = {"Location": "http://127.0.0.1/secret"}

        mock_unsafe_response = MagicMock()
        mock_unsafe_response.is_redirect = False

        mock_session = mock_session_cls.return_value
        mock_session.get.side_effect = [mock_safe_response, mock_unsafe_response]

        with self.assertRaises(SecurityException):
            security.safe_requests_get("http://example.com")

    @patch('security.requests.Session')
    @patch('socket.getaddrinfo')
    def test_verify_false_rejected(self, mock_getaddrinfo, mock_session_cls):
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 80))
        ]
        with self.assertRaises(SecurityException):
            security.safe_requests_get("http://example.com", verify=False)


class TestFilePathValidation(unittest.TestCase):

    def test_relative_path_rejected(self):
        with self.assertRaises(SecurityException):
            security.validate_file_path("relative/path.txt")

    def test_directory_traversal_rejected(self):
        with self.assertRaises(SecurityException):
            security.validate_file_path("/tmp/../etc/passwd")

    def test_symlink_escape_blocked(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = os.path.join(tmpdir, "base")
            os.makedirs(base)
            secret = os.path.join(tmpdir, "secret.txt")
            with open(secret, "w") as f:
                f.write("secret")
            link = os.path.join(base, "link.txt")
            os.symlink(secret, link)
            with self.assertRaises(SecurityException):
                security.validate_file_path(link, allowed_base_dir=base)


class TestAnalysisSecurity(unittest.TestCase):

    @patch('security.requests.Session')
    @patch('socket.getaddrinfo')
    def test_extract_text_blocks_unsafe(self, mock_getaddrinfo, mock_session_cls):
        # Ensure extract_text_from_website now calls validate_url
        # which raises SecurityException for unsafe URLs
        mock_session = mock_session_cls.return_value
        url = "http://localhost:8080/sensitive"

        mock_getaddrinfo.return_value = [
             (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('127.0.0.1', 8080))
        ]

        # Unsafe URLs now raise SecurityException early instead of returning a string.
        with self.assertRaises(SecurityException):
            analysis.extract_text_from_website(url)

        # requests.get should NOT have been called
        mock_session.get.assert_not_called()

    @patch('security.requests.Session')
    @patch('socket.getaddrinfo')
    def test_extract_text_allows_safe(self, mock_getaddrinfo, mock_session_cls):
        url = "https://example.com"
        mock_session = mock_session_cls.return_value

        mock_response = MagicMock()
        mock_response.text = "<html><body>Safe content</body></html>"
        mock_response.status_code = 200
        mock_response.is_redirect = False
        mock_response.url = url
        mock_session.get.return_value = mock_response

        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 443))
        ]

        result = analysis.extract_text_from_website(url)

        self.assertIn("Safe content", result)
        mock_session.get.assert_called_once()

if __name__ == '__main__':
    unittest.main()
