"""
Web scraper module for the AI Web Scraper application.

Contains the WebScraper class for scraping web content and
analyzing it using Google's Gemini API.
"""

import time
from collections import defaultdict
from typing import Dict, Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup
import google.generativeai as genai
from playwright.sync_api import sync_playwright

from app.config import config
from app.utils import (
    validate_url,
    check_ssrf_protection,
    URLValidationError,
    SSRFProtectionError,
    logger,
)


class ScrapingError(Exception):
    """Raised when scraping fails."""
    pass


class ContentAnalysisError(Exception):
    """Raised when content analysis fails."""
    pass


class RateLimiter:
    """Handles rate limiting for web requests."""

    def __init__(self, default_delay: float = 1.0):
        """
        Initialize the rate limiter.

        Args:
            default_delay: Default delay between requests in seconds
        """
        self.rate_limits: Dict[str, Dict[str, float]] = defaultdict(
            lambda: {'last_request': 0, 'delay': default_delay}
        )

    def wait_if_needed(self, domain: str) -> None:
        """
        Wait if necessary to respect rate limits.

        Args:
            domain: The domain to check rate limits for
        """
        current_time = time.time()
        time_since_last = current_time - \
            self.rate_limits[domain]['last_request']

        if time_since_last < self.rate_limits[domain]['delay']:
            sleep_time = self.rate_limits[domain]['delay'] - time_since_last
            logger.debug(
                f"Rate limiting: sleeping {sleep_time:.2f}s for {domain}")
            time.sleep(sleep_time)

        self.rate_limits[domain]['last_request'] = time.time()


class ContentAnalyzer:
    """Handles content analysis using Gemini API."""

    def __init__(self, api_key: str, model_name: str):
        """
        Initialize the content analyzer.

        Args:
            api_key: Gemini API key
            model_name: Name of the Gemini model to use
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        logger.info(f"Initialized ContentAnalyzer with model: {model_name}")

    def analyze(
        self,
        content: Dict[str, Any],
        query: str,
        max_content_length: int = 2000,
        max_tables: int = 3
    ) -> str:
        """
        Analyze scraped content using Gemini API.

        Args:
            content: The scraped content dictionary
            query: The user's query about the content
            max_content_length: Maximum characters of content to include
            max_tables: Maximum number of tables to include

        Returns:
            The analysis response from Gemini

        Raises:
            ContentAnalysisError: If analysis fails
        """
        # Build context from content
        tables_text = ' '.join(content.get('tables', [])[:max_tables]) if content.get(
            'tables') else 'No tables found'

        context = f"""
        Title: {content.get('title', 'Unknown')}
        
        Content Summary: {content.get('text', '')[:max_content_length]}...
        
        Table Data: {tables_text}
        
        Metadata:
        - Description: {content.get('metadata', {}).get('description', '')}
        - Keywords: {content.get('metadata', {}).get('keywords', '')}
        
        Query: {query}
        
        Please provide a helpful and accurate response based on the content above.
        """

        try:
            response = self.model.generate_content(context)

            # Check for blocked content
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                raise ContentAnalysisError(
                    f"Content was blocked: {response.prompt_feedback.block_reason}"
                )

            if not response.text:
                raise ContentAnalysisError("Empty response from Gemini API")

            return response.text

        except genai.types.BlockedPromptException as e:
            logger.error(f"Prompt was blocked by Gemini: {e}")
            raise ContentAnalysisError(
                "Your query was blocked by content safety filters")
        except genai.types.StopCandidateException as e:
            logger.error(f"Generation stopped: {e}")
            raise ContentAnalysisError(
                "Response generation was stopped due to content safety")
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise ContentAnalysisError(
                f"Failed to analyze content: {str(e)}") from e


class WebScraper:
    """
    Main web scraper class combining scraping and analysis capabilities.

    This class provides methods to scrape web pages using Playwright
    and analyze the content using Google's Gemini API.
    """

    def __init__(self):
        """Initialize the WebScraper with all required components."""
        self.config = config

        # Initialize components
        self.rate_limiter = RateLimiter(
            default_delay=self.config.scraper.default_rate_limit_delay
        )
        self.analyzer = ContentAnalyzer(
            api_key=self.config.gemini.api_key,
            model_name=self.config.gemini.model_name
        )

        logger.info("WebScraper initialized successfully")

    def scrape_url(self, url: str) -> Dict[str, Any]:
        """
        Scrape content from a URL.

        Args:
            url: The URL to scrape

        Returns:
            Dictionary containing scraped content

        Raises:
            URLValidationError: If URL validation fails
            SSRFProtectionError: If SSRF protection blocks the URL
            ScrapingError: If scraping fails
        """
        # Validate URL
        is_valid, error = validate_url(url)
        if not is_valid:
            raise URLValidationError(error)

        # SSRF protection
        is_safe, error = check_ssrf_protection(url)
        if not is_safe:
            raise SSRFProtectionError(error)

        # Respect rate limits
        domain = urlparse(url).netloc
        self.rate_limiter.wait_if_needed(domain)

        # Scrape the page
        try:
            return self._scrape_with_playwright(url)
        except Exception as e:
            logger.error(f"Scraping failed for {url}: {e}")
            raise ScrapingError(f"Failed to scrape URL: {str(e)}") from e

    def _scrape_with_playwright(self, url: str) -> Dict[str, Any]:
        """
        Scrape a URL using Playwright.

        Args:
            url: The URL to scrape

        Returns:
            Dictionary containing scraped content
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.config.scraper.headless)

            try:
                page = browser.new_page()

                # Set headers
                page.set_extra_http_headers({
                    'User-Agent': self.config.scraper.user_agent,
                    'Accept': self.config.scraper.accept_header
                })

                # Navigate to page
                page.goto(url, wait_until='networkidle',
                          timeout=self.config.scraper.request_timeout)
                page.wait_for_timeout(self.config.scraper.page_wait_timeout)

                html_content = page.content()

            finally:
                browser.close()

        # Parse content
        return self._parse_html(html_content)

    def _parse_html(self, html_content: str) -> Dict[str, Any]:
        """
        Parse HTML content into structured data.

        Args:
            html_content: Raw HTML string

        Returns:
            Dictionary containing parsed content
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract text content
        text_elements = soup.find_all(['p', 'div', 'span', 'td', 'th', 'tr'])
        text = ' '.join([el.get_text(strip=True) for el in text_elements])

        # Extract links
        links = [a.get('href') for a in soup.find_all('a', href=True)]

        # Extract metadata
        description_tag = soup.find('meta', attrs={'name': 'description'})
        keywords_tag = soup.find('meta', attrs={'name': 'keywords'})

        # Extract tables
        tables = [table.get_text(strip=True)
                  for table in soup.find_all('table')]

        return {
            'title': soup.title.string if soup.title else '',
            'text': text,
            'links': links,
            'metadata': {
                'description': description_tag['content'] if description_tag else '',
                'keywords': keywords_tag['content'] if keywords_tag else ''
            },
            'tables': tables
        }

    def analyze_content(self, content: Dict[str, Any], query: str) -> str:
        """
        Analyze scraped content with a query.

        Args:
            content: The scraped content dictionary
            query: The user's query

        Returns:
            Analysis response from Gemini

        Raises:
            ContentAnalysisError: If analysis fails
        """
        return self.analyzer.analyze(
            content,
            query,
            max_content_length=self.config.gemini.max_content_length,
            max_tables=self.config.gemini.max_tables
        )
