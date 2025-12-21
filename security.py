import socket
import ipaddress
from urllib.parse import urlparse

def validate_url(url):
    """
    Validates a URL to prevent Server-Side Request Forgery (SSRF).

    Checks:
    - Scheme is http or https.
    - Hostname resolves to a public IP address.

    Raises:
    - ValueError if URL is invalid or unsafe.
    """
    try:
        parsed_url = urlparse(url)
    except Exception as e:
        raise ValueError(f"Invalid URL format: {str(e)}")

    if parsed_url.scheme not in ('http', 'https'):
        raise ValueError("URL scheme must be http or https")

    hostname = parsed_url.hostname
    if not hostname:
        raise ValueError("URL must have a hostname")

    try:
        # Resolve hostname to IP
        # We use getaddrinfo to get IP addresses.
        # Note: This is a synchronous DNS lookup.
        # It's better to verify the IP we are about to connect to,
        # but requests library doesn't easily let us hook into the connection phase
        # to verify the resolved IP before sending data, unless we use a custom adapter.
        # For this level of fix, pre-validation is a good improvement,
        # though susceptible to TOCTOU (Time-of-Check Time-of-Use) DNS rebinding attacks.
        # However, it significantly raises the bar.

        addr_info = socket.getaddrinfo(hostname, None)

        for res in addr_info:
            family, _, _, _, sockaddr = res
            ip_str = sockaddr[0]

            ip_obj = ipaddress.ip_address(ip_str)

            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
                 raise ValueError(f"Access to private IP address {ip_str} is forbidden")

            # Check for multicast or reserved?
            if ip_obj.is_multicast or ip_obj.is_reserved:
                 raise ValueError(f"Access to reserved/multicast IP address {ip_str} is forbidden")

            # Check for specific blocks like 0.0.0.0
            if ip_obj.is_unspecified:
                 raise ValueError(f"Access to unspecified IP address {ip_str} is forbidden")

    except socket.gaierror:
        raise ValueError(f"Could not resolve hostname: {hostname}")
    except ValueError as e:
        # Re-raise our own ValueErrors
        raise e
    except Exception as e:
        raise ValueError(f"Error validating URL: {str(e)}")

    return True
