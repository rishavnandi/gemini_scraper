"""
AI Web Scraper & Chat Application

A Streamlit-based web application that uses Playwright for web scraping
and Google's Gemini API for content analysis.
"""

from app.scraper import WebScraper
from app.config import Config

__all__ = ["WebScraper", "Config"]
