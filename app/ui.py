"""
UI components for the AI Web Scraper Streamlit application.

Contains functions for rendering the chat interface, styling,
and handling user interactions.
"""

import streamlit as st
from typing import Optional

from app.config import config
from app.scraper import (
    WebScraper,
    URLValidationError,
    SSRFProtectionError,
    ScrapingError,
    ContentAnalysisError,
)
from app.utils import validate_query, format_scrape_summary, logger


def setup_page_config() -> None:
    """Configure the Streamlit page settings."""
    st.set_page_config(
        page_title=config.ui.page_title,
        page_icon=config.ui.page_icon,
        layout=config.ui.layout,
        initial_sidebar_state="collapsed"
    )


def apply_custom_css() -> None:
    """Apply custom CSS styling to the application."""
    st.markdown("""
        <style>
        .main-content {
            margin-bottom: 100px;
        }
        /* Ensure proper spacing for chat messages */
        .stChatMessage {
            margin-bottom: 0.5rem;
        }
        </style>
    """, unsafe_allow_html=True)


def initialize_session_state() -> None:
    """Initialize Streamlit session state variables."""
    if 'scraper' not in st.session_state:
        st.session_state.scraper = None
    if 'content' not in st.session_state:
        st.session_state.content = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'current_url' not in st.session_state:
        st.session_state.current_url = ""
    if 'error_message' not in st.session_state:
        st.session_state.error_message = None


def display_chat_message(message: str, is_user: bool = True) -> None:
    """
    Display a chat message using Streamlit's native chat components.

    This uses st.chat_message which is XSS-safe and provides
    consistent styling with the Streamlit theme.

    Args:
        message: The message content to display
        is_user: True if the message is from the user, False for assistant
    """
    role = "user" if is_user else "assistant"
    with st.chat_message(role):
        st.markdown(message)


def display_chat_history() -> None:
    """Display the chat history from session state."""
    for item in st.session_state.chat_history:
        if item["query"] == "System":
            st.info(item["response"])
        else:
            display_chat_message(item["query"], is_user=True)
            display_chat_message(item["response"], is_user=False)


def process_scrape_request(url: str) -> None:
    """
    Process a URL scrape request.

    Args:
        url: The URL to scrape
    """
    try:
        with st.spinner('🔄 Scraping content... This may take a few seconds.'):
            st.session_state.scraper = WebScraper()
            st.session_state.content = st.session_state.scraper.scrape_url(url)
            st.session_state.current_url = url
            st.session_state.chat_history = []  # Clear chat history for new URL
            st.session_state.error_message = None

            # Add system message about scraped content
            system_msg = format_scrape_summary(st.session_state.content)
            st.session_state.chat_history.append(
                {"query": "System", "response": system_msg}
            )

            logger.info(f"Successfully scraped: {url}")
            st.rerun()

    except URLValidationError as e:
        st.session_state.error_message = f"❌ Invalid URL: {str(e)}"
        logger.warning(f"URL validation failed: {e}")
    except SSRFProtectionError as e:
        st.session_state.error_message = f"🛡️ Security Error: {str(e)}"
        logger.warning(f"SSRF protection triggered: {e}")
    except ScrapingError as e:
        st.session_state.error_message = f"⚠️ Scraping Error: {str(e)}"
        logger.error(f"Scraping failed: {e}")
    except ValueError as e:
        st.session_state.error_message = f"⚠️ Configuration Error: {str(e)}"
        logger.error(f"Configuration error: {e}")
    except Exception as e:
        st.session_state.error_message = f"❌ Unexpected Error: {str(e)}"
        logger.error(f"Unexpected error during scraping: {e}", exc_info=True)


def process_query(query: str) -> None:
    """
    Process a user query about the scraped content.

    Args:
        query: The user's question
    """
    # Validate query
    is_valid, error = validate_query(query)
    if not is_valid:
        st.error(error)
        return

    if not st.session_state.content:
        st.error("Please scrape a URL first!")
        return

    if not st.session_state.scraper:
        st.error("Scraper not initialized. Please scrape a URL first!")
        return

    try:
        with st.spinner('🤔 Thinking...'):
            response = st.session_state.scraper.analyze_content(
                st.session_state.content, query
            )
            st.session_state.chat_history.append(
                {"query": query, "response": response}
            )
            st.rerun()

    except ContentAnalysisError as e:
        st.error(f"Analysis Error: {str(e)}")
        logger.error(f"Content analysis failed: {e}")
    except Exception as e:
        st.error(f"Unexpected Error: {str(e)}")
        logger.error(f"Unexpected error during analysis: {e}", exc_info=True)


def render_url_input_section() -> None:
    """Render the URL input section."""
    with st.expander("📎 Enter New URL", expanded=not st.session_state.content):
        url = st.text_input(
            "URL to scrape",
            value=st.session_state.current_url,
            placeholder="https://example.com",
            help="Enter the full URL including https://"
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🚀 Scrape URL", type="primary", use_container_width=True):
                if url:
                    process_scrape_request(url)
                else:
                    st.warning("Please enter a URL")

        with col2:
            if st.session_state.content and st.button("🗑️ Clear", use_container_width=False):
                st.session_state.content = None
                st.session_state.chat_history = []
                st.session_state.current_url = ""
                st.rerun()

        # Display error message if any
        if st.session_state.error_message:
            st.error(st.session_state.error_message)


def render_chat_interface() -> None:
    """Render the main chat interface."""
    # Main content area
    st.markdown('<div class="main-content">', unsafe_allow_html=True)

    # Display chat history
    display_chat_history()

    # Chat input
    if st.session_state.content:
        query = st.chat_input("💬 Ask a question about the content...")
        if query:
            process_query(query)
    else:
        st.chat_input("Please scrape a URL first...", disabled=True)

    st.markdown('</div>', unsafe_allow_html=True)


def render_sidebar() -> None:
    """Render the sidebar with additional options."""
    with st.sidebar:
        st.header("ℹ️ About")
        st.markdown("""
        This AI-powered web scraper allows you to:
        
        1. **Scrape** content from any public webpage
        2. **Analyze** the content using Google's Gemini AI
        3. **Ask questions** about the scraped content
        
        ---
        
        **Tips:**
        - Make sure the URL is publicly accessible
        - Some websites may block scraping
        - Be patient, scraping may take a few seconds
        """)

        if st.session_state.content:
            st.header("📊 Current Content")
            st.markdown(f"**URL:** {st.session_state.current_url}")
            st.markdown(
                f"**Title:** {st.session_state.content.get('title', 'N/A')}")
            st.markdown(f"**Messages:** {len(st.session_state.chat_history)}")
