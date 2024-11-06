import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from typing import Dict, Any
from urllib.parse import urlparse
import time
from collections import defaultdict
import robotexclusionrulesparser
import os
from dotenv import load_dotenv
import asyncio
from playwright.sync_api import sync_playwright
import nest_asyncio

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Load environment variables
load_dotenv()


class WebScraper:
    # [Previous WebScraper class implementation remains the same]
    def __init__(self):
        # Get API key from environment variable
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found in environment variables")

        # Initialize Gemini API
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')

        # Initialize rate limiting
        self.rate_limits = defaultdict(lambda: {
            'last_request': 0,
            'delay': 1
        })

        # Initialize robots.txt parser
        self.robot_parser = robotexclusionrulesparser.RobotExclusionRulesParser()

    def _check_robots_txt(self, url: str) -> bool:
        parsed_url = urlparse(url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        try:
            robots_content = requests.get(robots_url, timeout=5)
            self.robot_parser.parse(robots_content.text)
            return self.robot_parser.is_allowed("*", url)
        except:
            return True

    def _respect_rate_limits(self, domain: str):
        current_time = time.time()
        time_since_last = current_time - \
            self.rate_limits[domain]['last_request']
        if time_since_last < self.rate_limits[domain]['delay']:
            time.sleep(self.rate_limits[domain]['delay'] - time_since_last)
        self.rate_limits[domain]['last_request'] = time.time()

    def scrape_url(self, url: str) -> Dict[str, Any]:
        if not self._check_robots_txt(url):
            raise Exception("Scraping not allowed according to robots.txt")

        domain = urlparse(url).netloc
        self._respect_rate_limits(domain)

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                page.set_extra_http_headers({
                    'User-Agent': 'Custom Web Scraper (contact@example.com)',
                    'Accept': 'text/html,application/xhtml+xml'
                })

                page.goto(url, wait_until='networkidle')
                page.wait_for_timeout(2000)
                html_content = page.content()
                browser.close()

                soup = BeautifulSoup(html_content, 'html.parser')

                content = {
                    'title': soup.title.string if soup.title else '',
                    'text': ' '.join([p.get_text(strip=True) for p in soup.find_all(['p', 'div', 'span', 'td', 'th', 'tr'])]),
                    'links': [a.get('href') for a in soup.find_all('a', href=True)],
                    'metadata': {
                        'description': soup.find('meta', attrs={'name': 'description'})['content'] if soup.find('meta', attrs={'name': 'description'}) else '',
                        'keywords': soup.find('meta', attrs={'name': 'keywords'})['content'] if soup.find('meta', attrs={'name': 'keywords'}) else ''
                    },
                    'tables': [table.get_text(strip=True) for table in soup.find_all('table')]
                }

                return content

        except Exception as e:
            raise Exception(f"Failed to fetch URL: {str(e)}")

    def analyze_content(self, content: Dict[str, Any], query: str) -> str:
        context = f"""
        Title: {content['title']}
        
        Content Summary: {content['text'][:2000]}...
        
        Table Data: {' '.join(content['tables'][:3]) if content['tables'] else 'No tables found'}
        
        Metadata:
        - Description: {content['metadata']['description']}
        - Keywords: {content['metadata']['keywords']}
        
        Query: {query}
        """

        response = self.model.generate_content(context)
        return response.text

# Custom CSS for chat interface


def local_css():
    st.markdown("""
        <style>
        .stChatFloatingInputContainer {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background-color: transparent;  /* Changed from white to transparent */
            padding: 1rem;
            z-index: 100;
        }
        .chat-message {
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            display: flex;
            flex-direction: column;
            color: #000000;
        }
        .user-message {
            background-color: #007bff;
            color: white;
            margin-left: 2rem;
        }
        .assistant-message {
            background-color: #2f2f2f;
            color: white;
            margin-right: 2rem;
        }
        .message-content {
            margin-top: 0.5rem;
        }
        .main-content {
            margin-bottom: 100px;
        }
        /* Remove white bar at bottom */
        [data-testid="stChatInput"] {
            background-color: transparent !important;
        }
        </style>
    """, unsafe_allow_html=True)


def initialize_session_state():
    if 'scraper' not in st.session_state:
        st.session_state.scraper = None
    if 'content' not in st.session_state:
        st.session_state.content = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'current_url' not in st.session_state:
        st.session_state.current_url = ""


def display_chat_message(message, is_user=True):
    message_class = "user-message" if is_user else "assistant-message"
    st.markdown(f"""
        <div class="chat-message {message_class}">
            <div><strong>{'You' if is_user else '🤖 Assistant'}</strong></div>
            <div class="message-content">{message}</div>
        </div>
    """, unsafe_allow_html=True)


def process_query(query: str):
    if st.session_state.content:
        with st.spinner('Thinking...'):
            response = st.session_state.scraper.analyze_content(
                st.session_state.content, query)
            st.session_state.chat_history.append(
                {"query": query, "response": response})
            st.rerun()  # Updated from experimental_rerun()
    else:
        st.error("Please scrape a URL first!")


def main():
    st.set_page_config(
        page_title="AI Web Scraper & Chat",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    local_css()
    initialize_session_state()

    # Header section
    st.title("🌐 AI Web Scraper & Chat")

    # URL input section (collapsible)
    with st.expander("Enter New URL", expanded=not st.session_state.content):
        url = st.text_input("URL to scrape",
                            value=st.session_state.current_url,
                            placeholder="https://example.com")

        if st.button("Scrape URL", type="primary"):
            try:
                with st.spinner('Scraping content...'):
                    st.session_state.scraper = WebScraper()
                    st.session_state.content = st.session_state.scraper.scrape_url(
                        url)
                    st.session_state.current_url = url
                    st.success("Content scraped successfully!")
                    st.session_state.chat_history = []  # Clear chat history for new URL

                    # Add system message about scraped content
                    system_msg = f"Successfully scraped: {st.session_state.content['title']}\n\n" + \
                        f"Content length: {len(st.session_state.content['text'])} characters\n" + \
                        f"Links found: {len(st.session_state.content['links'])}\n" + \
                        f"Tables found: {len(st.session_state.content['tables'])}"
                    st.session_state.chat_history.append(
                        {"query": "System", "response": system_msg})
                    st.rerun()  # Updated from experimental_rerun()

            except Exception as e:
                st.error(f"Error: {str(e)}")

    # Main chat area
    st.markdown('<div class="main-content">', unsafe_allow_html=True)

    # Display chat history
    for item in st.session_state.chat_history:
        if item["query"] == "System":
            st.info(item["response"])
        else:
            display_chat_message(item["query"], is_user=True)
            display_chat_message(item["response"], is_user=False)

    # Fixed chat input at bottom
    st.markdown('<div class="stChatFloatingInputContainer">',
                unsafe_allow_html=True)
    if st.session_state.content:
        query = st.chat_input("Ask a question about the content...")
        if query:
            process_query(query)
    else:
        st.chat_input("Please scrape a URL first...", disabled=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
