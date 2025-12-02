"""
AI Web Scraper & Chat Application

A Streamlit-based web application that uses Playwright for web scraping
and Google's Gemini API for content analysis.
"""

from app.ui import (
    setup_page_config,
    apply_custom_css,
    initialize_session_state,
    render_url_input_section,
    render_chat_interface,
    render_sidebar,
)
import nest_asyncio

# Apply nest_asyncio to allow nested event loops (required for Playwright in Streamlit)
nest_asyncio.apply()


def main():
    """Main application entry point."""
    # Configure page (must be first Streamlit command)
    setup_page_config()

    # Apply custom styling
    apply_custom_css()

    # Initialize session state
    initialize_session_state()

    # Render header
    import streamlit as st
    st.title("🌐 AI Web Scraper & Chat")

    # Render URL input section
    render_url_input_section()

    # Render main chat interface
    render_chat_interface()

    # Render sidebar
    render_sidebar()


if __name__ == "__main__":
    main()
