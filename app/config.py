"""
Configuration management for the AI Web Scraper application.

Centralizes all configuration values, constants, and settings.
"""

import os
from dataclasses import dataclass, field
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class ScraperConfig:
    """Configuration for web scraping operations."""

    # Browser settings
    headless: bool = True
    page_wait_timeout: int = 2000  # milliseconds
    request_timeout: int = 30000  # milliseconds

    # Rate limiting
    default_rate_limit_delay: float = 1.0  # seconds

    # HTTP headers
    user_agent: str = "Custom Web Scraper (contact@example.com)"
    accept_header: str = "text/html,application/xhtml+xml"


@dataclass
class GeminiConfig:
    """Configuration for Gemini API."""

    model_name: str = "gemini-2.5-flash"
    max_content_length: int = 2000  # characters for content summary
    max_tables: int = 3  # maximum tables to include in context

    @property
    def api_key(self) -> str:
        """Get API key from environment variable."""
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError(
                "GEMINI_API_KEY not found in environment variables")
        return key


@dataclass
class SecurityConfig:
    """Security-related configuration."""

    # Private IP ranges to block (SSRF protection)
    blocked_ip_prefixes: List[str] = field(default_factory=lambda: [
        "127.",           # Loopback
        "10.",            # Private Class A
        "172.16.", "172.17.", "172.18.", "172.19.",  # Private Class B
        "172.20.", "172.21.", "172.22.", "172.23.",
        "172.24.", "172.25.", "172.26.", "172.27.",
        "172.28.", "172.29.", "172.30.", "172.31.",
        "192.168.",       # Private Class C
        "0.",             # Reserved
        "169.254.",       # Link-local
        "::1",            # IPv6 loopback
        "fc00:",          # IPv6 private
        "fe80:",          # IPv6 link-local
    ])

    blocked_hosts: List[str] = field(default_factory=lambda: [
        "localhost",
        "internal",
        "intranet",
        "corp",
        "local",
    ])

    allowed_schemes: List[str] = field(
        default_factory=lambda: ["http", "https"])

    max_query_length: int = 1000  # characters
    max_url_length: int = 2048  # characters


@dataclass
class UIConfig:
    """UI-related configuration."""

    page_title: str = "AI Web Scraper & Chat"
    page_icon: str = "🌐"
    layout: str = "wide"


class Config:
    """Main configuration class aggregating all settings."""

    def __init__(self):
        self.scraper = ScraperConfig()
        self.gemini = GeminiConfig()
        self.security = SecurityConfig()
        self.ui = UIConfig()

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables with overrides."""
        config = cls()

        # Override from environment if set
        if os.getenv("GEMINI_MODEL"):
            config.gemini.model_name = os.getenv("GEMINI_MODEL")

        if os.getenv("RATE_LIMIT_DELAY"):
            config.scraper.default_rate_limit_delay = float(
                os.getenv("RATE_LIMIT_DELAY"))

        if os.getenv("PAGE_WAIT_TIMEOUT"):
            config.scraper.page_wait_timeout = int(
                os.getenv("PAGE_WAIT_TIMEOUT"))

        return config


# Global configuration instance
config = Config.from_env()
