import ipaddress
import socket
from urllib.parse import urlparse

class SecurityException(Exception):
    """Exception raised for security violations."""
    pass

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
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            raise SecurityException("Invalid URL scheme. Only http and https are allowed.")

        hostname = parsed.hostname
        if not hostname:
             raise SecurityException("Invalid URL: No hostname found.")

        try:
            # getaddrinfo returns a list of (family, type, proto, canonname, sockaddr)
            # sockaddr is a tuple, index 0 is the IP address string
            # We want to check ALL resolved IPs
            addr_infos = socket.getaddrinfo(hostname, None)
        except socket.error:
             raise SecurityException("Could not resolve hostname.")

        for addr_info in addr_infos:
            ip = addr_info[4][0]
            try:
                ip_addr = ipaddress.ip_address(ip)

                # Check for various restricted ranges
                if (ip_addr.is_private or
                    ip_addr.is_loopback or
                    ip_addr.is_link_local or
                    ip_addr.is_multicast or
                    ip_addr.is_reserved):
                    raise SecurityException(f"URL points to a restricted IP address: {ip}")

            except ValueError:
                continue

    except SecurityException:
        raise
    except Exception as e:
         raise SecurityException(f"URL validation failed: {str(e)}")
