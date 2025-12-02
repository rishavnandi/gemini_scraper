"""
Utility functions for the AI Web Scraper application.

Contains helper functions for URL validation, security checks,
and other common operations.
"""

import logging
import socket
import ipaddress
from urllib.parse import urlparse
from typing import Tuple, Optional

from app.config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class URLValidationError(Exception):
    """Raised when URL validation fails."""
    pass


class SSRFProtectionError(Exception):
    """Raised when SSRF protection blocks a request."""
    pass


def validate_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a URL for format and security.

    Args:
        url: The URL to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url:
        return False, "URL cannot be empty"

    if len(url) > config.security.max_url_length:
        return False, f"URL exceeds maximum length of {config.security.max_url_length} characters"

    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, f"Invalid URL format: {str(e)}"

    # Check scheme
    if parsed.scheme not in config.security.allowed_schemes:
        return False, f"URL scheme must be one of: {', '.join(config.security.allowed_schemes)}"

    # Check for host
    if not parsed.netloc:
        return False, "URL must include a host"

    # Check for blocked hosts
    hostname = parsed.hostname or ""
    for blocked in config.security.blocked_hosts:
        if blocked in hostname.lower():
            return False, f"Access to '{hostname}' is not allowed"

    return True, None


def check_ssrf_protection(url: str) -> Tuple[bool, Optional[str]]:
    """
    Check if a URL passes SSRF protection.

    Resolves the hostname and checks against blocked IP ranges.

    Args:
        url: The URL to check

    Returns:
        Tuple of (is_safe, error_message)
    """
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname

        if not hostname:
            return False, "Cannot resolve hostname from URL"

        # Resolve hostname to IP addresses
        try:
            ip_addresses = socket.getaddrinfo(hostname, None)
        except socket.gaierror as e:
            logger.warning(f"DNS resolution failed for {hostname}: {e}")
            return False, f"Cannot resolve hostname: {hostname}"

        for family, _, _, _, sockaddr in ip_addresses:
            ip = sockaddr[0]

            # Check against blocked prefixes
            for prefix in config.security.blocked_ip_prefixes:
                if ip.startswith(prefix):
                    logger.warning(
                        f"SSRF protection: Blocked access to {ip} for {url}")
                    return False, f"Access to internal network addresses is not allowed"

            # Additional check using ipaddress module
            try:
                ip_obj = ipaddress.ip_address(ip)
                if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved:
                    logger.warning(
                        f"SSRF protection: Blocked private IP {ip} for {url}")
                    return False, "Access to private network addresses is not allowed"
            except ValueError:
                pass  # Not a valid IP format, skip this check

        return True, None

    except Exception as e:
        logger.error(f"SSRF check failed for {url}: {e}")
        return False, f"Security check failed: {str(e)}"


def validate_query(query: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a user query.

    Args:
        query: The query to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not query or not query.strip():
        return False, "Query cannot be empty"

    if len(query) > config.security.max_query_length:
        return False, f"Query exceeds maximum length of {config.security.max_query_length} characters"

    return True, None


def sanitize_content(content: str) -> str:
    """
    Sanitize content for safe display.

    Args:
        content: The content to sanitize

    Returns:
        Sanitized content string
    """
    import html
    return html.escape(content)


def format_scrape_summary(content: dict) -> str:
    """
    Format a summary of scraped content.

    Args:
        content: The scraped content dictionary

    Returns:
        Formatted summary string
    """
    title = content.get('title', 'Unknown')
    text_length = len(content.get('text', ''))
    links_count = len(content.get('links', []))
    tables_count = len(content.get('tables', []))

    return (
        f"**Successfully scraped:** {title}\n\n"
        f"- Content length: {text_length:,} characters\n"
        f"- Links found: {links_count}\n"
        f"- Tables found: {tables_count}"
    )
