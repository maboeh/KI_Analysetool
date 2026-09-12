import ipaddress
import os
import re
import socket
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from urllib.parse import urlparse, urlsplit, unquote

import requests

_DNS_TIMEOUT_SECONDS = 5


class SecurityException(Exception):
    """Exception raised for security violations."""
    pass


# Hostnames that should never be resolved/requested.
_BLOCKED_HOSTNAMES = {
    "localhost",
    "0.0.0.0",
    "127.0.0.1",
    "::1",
    "metadata.google.internal",
    "169.254.169.254",
}


def _is_restricted_ip(ip_str: str) -> bool:
    """Return True if the IP belongs to a restricted/private range."""
    try:
        ip_addr = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    return (
        ip_addr.is_private
        or ip_addr.is_loopback
        or ip_addr.is_link_local
        or ip_addr.is_multicast
        or ip_addr.is_reserved
        or ip_addr.is_unspecified
    )


def validate_url(url: str) -> None:
    """
    Validates a URL to prevent SSRF attacks.
    Raises SecurityException if the URL is invalid or points to a private/restricted network.
    Checks IPv4 and IPv6 addresses.
    Blocks:
    - Private networks (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, fc00::/7)
    - Loopback addresses (127.0.0.0/8, ::1)
    - Link-local addresses (169.254.0.0/16, fe80::/10) - Prevents Cloud Metadata attacks
    - Multicast addresses
    - Reserved addresses
    - Common internal hostnames (localhost, metadata.google.internal)
    """
    if not isinstance(url, str) or not url.strip():
        raise SecurityException("Invalid URL: empty.")

    try:
        parsed = urlparse(url)
    except Exception as e:
        raise SecurityException(f"Invalid URL: {e}")

    scheme = parsed.scheme.lower()
    if scheme not in ('http', 'https'):
        raise SecurityException(f"Invalid URL scheme '{scheme}'. Only http and https are allowed.")

    hostname = parsed.hostname
    if not hostname:
        raise SecurityException("Invalid URL: No hostname found.")

    # Reject URL-encoded host bypasses (e.g. http://%31%32%37%2e%30%2e%30%2e%31/)
    decoded_hostname = unquote(hostname).lower()
    if decoded_hostname != hostname.lower():
        hostname = decoded_hostname

    # Block common internal hostnames early.
    if hostname.lower() in _BLOCKED_HOSTNAMES:
        raise SecurityException(f"URL points to a blocked hostname: {hostname}")

    # If the hostname is already an IP literal, check it directly.
    try:
        if _is_restricted_ip(hostname):
            raise SecurityException(f"URL points to a restricted IP address: {hostname}")
    except ValueError:
        pass

    # Resolve hostname and check every returned IP with a timeout.
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(socket.getaddrinfo, hostname, None)
            addr_infos = future.result(timeout=_DNS_TIMEOUT_SECONDS)
    except FutureTimeoutError:
        raise SecurityException(f"DNS resolution for '{hostname}' timed out")
    except socket.error as e:
        raise SecurityException(f"Could not resolve hostname: {e}")

    for addr_info in addr_infos:
        ip = addr_info[4][0]
        try:
            if _is_restricted_ip(ip):
                raise SecurityException(f"URL points to a restricted IP address: {ip}")
        except ValueError:
            continue


def safe_requests_get(url: str, timeout: int = 15, **kwargs):
    """
    Wrapper around requests.get that validates the URL and follows redirects
    manually, validating every intermediate URL for SSRF protection before
    the request is actually sent.

    Returns the response object on success. Raises SecurityException or requests
    exceptions on failure.
    """
    validate_url(url)

    # Do not allow the caller to override safety-related settings.
    safe_kwargs = dict(kwargs)
    safe_kwargs.setdefault("headers", {"User-Agent": "KI-Analysetool/1.0"})
    safe_kwargs["timeout"] = timeout
    safe_kwargs["allow_redirects"] = False
    safe_kwargs.setdefault("stream", False)
    safe_kwargs.pop("max_redirects", None)

    # Reject TLS verification bypass attempts.
    if safe_kwargs.get("verify") is False:
        raise SecurityException("TLS verification cannot be disabled.")
    safe_kwargs.pop("verify", None)

    max_redirects = 10
    current_url = url
    session = requests.Session()

    for _ in range(max_redirects + 1):
        validate_url(current_url)
        response = session.get(current_url, **safe_kwargs)

        if response.is_redirect:
            next_url = response.headers.get("Location")
            if not next_url:
                raise SecurityException("Redirect without Location header")
            current_url = requests.compat.urljoin(current_url, next_url)
            continue

        response.raise_for_status()
        return response

    raise SecurityException("Too many redirects")


def validate_file_path(file_path: str, allowed_base_dir: str = None) -> str:
    """
    Validates that a file path is safe to read/write.

    - Must be an absolute path.
    - Must not contain parent directory traversal ('..').
    - If allowed_base_dir is given, the path must be inside it (symlinks resolved).

    Returns the real absolute path on success.
    Raises SecurityException on violation.
    """
    if not isinstance(file_path, str) or not file_path:
        raise SecurityException("Invalid file path: empty.")

    if not os.path.isabs(file_path):
        raise SecurityException(f"File path must be absolute: {file_path}")

    # Reject literal traversal components before normpath collapses them.
    if ".." in file_path.replace("\\", "/").split("/"):
        raise SecurityException(f"File path contains directory traversal: {file_path}")

    # Resolve symlinks so that a path inside allowed_base_dir cannot escape via a link.
    real_path = os.path.realpath(file_path)

    if allowed_base_dir:
        base_real = os.path.realpath(allowed_base_dir)
        # Ensure the real path is either the base directory itself or inside it.
        if not (
            real_path == base_real or
            real_path.startswith(base_real + os.sep)
        ):
            raise SecurityException(
                f"File path is outside the allowed directory: {file_path}"
            )

    return real_path


def is_allowed_extension(file_path: str, allowed_extensions: set) -> bool:
    """Checks whether a file path ends with one of the allowed extensions."""
    if not file_path:
        return False
    _, ext = os.path.splitext(file_path)
    return ext.lower() in {e.lower() for e in allowed_extensions}
