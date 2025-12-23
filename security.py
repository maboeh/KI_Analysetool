import ipaddress
import socket
from urllib.parse import urlparse


def validate_url(url: str) -> str:
    """
    Validates a URL to ensure it does not point to a private or reserved IP address.
    Returns the URL if valid, otherwise raises ValueError.
    """
    parsed = urlparse(url)

    if parsed.scheme not in ('http', 'https'):
        raise ValueError(f"Invalid scheme: {parsed.scheme}")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("Invalid URL: No hostname found")

    try:
        # Resolve hostname to IP
        # Note: This is vulnerable to DNS rebinding, but provides a basic layer of protection.
        # For full protection, one would need to control the resolution at the
        # socket level during connection.
        ip_str = socket.gethostbyname(hostname)
        ip = ipaddress.ip_address(ip_str)
    except socket.gaierror:
        raise ValueError(f"Could not resolve hostname: {hostname}")
    except ValueError:
        raise ValueError(f"Invalid IP address: {ip_str}")

    if (ip.is_loopback or
        ip.is_private or
        ip.is_reserved or
        ip.is_link_local or
            ip.is_multicast):
        raise ValueError(f"URL resolves to a restricted IP address: {ip}")

    return url
