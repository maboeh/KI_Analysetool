
import unittest
from unittest.mock import patch, MagicMock
from security import validate_url, SecurityException
import analysis

class TestSSRFProtection(unittest.TestCase):

    def test_validate_url_allow_valid(self):
        """Test that valid public URLs are allowed."""
        # Note: We mock socket.getaddrinfo to avoid real network calls and flaky tests
        with patch('socket.getaddrinfo') as mock_getaddrinfo:
            # Mock returning a public IP (e.g., 8.8.8.8)
            mock_getaddrinfo.return_value = [
                (2, 1, 6, '', ('8.8.8.8', 80))
            ]
            try:
                validate_url("https://www.google.com")
            except SecurityException:
                self.fail("validate_url raised SecurityException for valid URL")

    def test_validate_url_block_private_ipv4(self):
        """Test that private IPv4 addresses are blocked."""
        with patch('socket.getaddrinfo') as mock_getaddrinfo:
            mock_getaddrinfo.return_value = [
                (2, 1, 6, '', ('192.168.1.1', 80))
            ]
            with self.assertRaises(SecurityException):
                validate_url("http://internal-service")

    def test_validate_url_block_localhost(self):
        """Test that localhost is blocked."""
        with patch('socket.getaddrinfo') as mock_getaddrinfo:
            mock_getaddrinfo.return_value = [
                (2, 1, 6, '', ('127.0.0.1', 80))
            ]
            with self.assertRaises(SecurityException):
                validate_url("http://localhost")

    def test_validate_url_block_ipv6_loopback(self):
        """Test that IPv6 loopback is blocked."""
        with patch('socket.getaddrinfo') as mock_getaddrinfo:
             # AF_INET6, SOCK_STREAM, ...
            mock_getaddrinfo.return_value = [
                (10, 1, 6, '', ('::1', 80, 0, 0))
            ]
            with self.assertRaises(SecurityException):
                validate_url("http://[::1]")

    @patch('analysis.requests.Session')
    @patch('analysis.validate_url')
    def test_extract_text_from_website_redirect_loop(self, mock_validate_url, mock_session_cls):
        """Test that redirect loops are handled."""
        mock_session = mock_session_cls.return_value

        # Setup a redirect loop
        response1 = MagicMock()
        response1.is_redirect = True
        response1.headers = {'Location': 'http://example.com/2'}

        response2 = MagicMock()
        response2.is_redirect = True
        response2.headers = {'Location': 'http://example.com/1'}

        mock_session.get.side_effect = [response1, response2, response1, response2, response1, response2]

        # validate_url should pass
        mock_validate_url.return_value = None

        result = analysis.extract_text_from_website("http://example.com/1")
        self.assertEqual(result, "Error: Too many redirects")

    @patch('analysis.requests.Session')
    @patch('analysis.validate_url')
    def test_extract_text_from_website_ssrf_on_redirect(self, mock_validate_url, mock_session_cls):
        """Test that SSRF checks are applied on redirects."""
        mock_session = mock_session_cls.return_value

        # Initial request redirects to internal IP
        response1 = MagicMock()
        response1.is_redirect = True
        response1.headers = {'Location': 'http://192.168.1.1/admin'}

        mock_session.get.side_effect = [response1]

        # First call passes, second call (redirect) fails
        mock_validate_url.side_effect = [None, SecurityException("Blocked IP")]

        result = analysis.extract_text_from_website("http://example.com")

        # Now it catches Exception and returns string
        self.assertIn("Security Error on redirect", result)

        # Verify validate_url was called twice
        self.assertEqual(mock_validate_url.call_count, 2)
        mock_validate_url.assert_called_with('http://192.168.1.1/admin')

if __name__ == '__main__':
    unittest.main()
