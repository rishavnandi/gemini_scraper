# AI Web Scraper & Chat

An AI-powered web scraper and chat application built using Streamlit. It allows users to scrape content from any public webpage and interact with the scraped content through a chat interface powered by Google's Gemini API.

## Features

- 🌐 **Web Scraping** - Scrape content from any public URL using Playwright
- 🤖 **AI-Powered Analysis** - Query scraped content using Google's Gemini AI
- 💬 **Chat Interface** - Interactive chat with conversation history
- 🔒 **Security** - SSRF protection and URL validation
- ⚡ **Rate Limiting** - Automatic rate limiting per domain
- 🎨 **Modern UI** - Clean Streamlit interface with native chat components

## Project Structure

```
gemini_scraper/
├── app/
│   ├── __init__.py      # Package initialization
│   ├── config.py        # Configuration management
│   ├── scraper.py       # Web scraper and AI analyzer
│   ├── ui.py            # Streamlit UI components
│   └── utils.py         # Utility functions
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (not in repo)
└── README.md            # This file
```

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/rishavnandi/gemini_scraper.git
    cd gemini_scraper
    ```

2. Create a virtual environment and activate it:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

4. Install Playwright browsers:
    ```sh
    playwright install chromium
    ```

5. Create a `.env` file and add your Gemini API key:
    ```env
    GEMINI_API_KEY=your_gemini_api_key
    ```

## Configuration

You can customize the application by setting environment variables in your `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key (required) | - |
| `GEMINI_MODEL` | Gemini model to use | `gemini-1.5-pro` |
| `RATE_LIMIT_DELAY` | Delay between requests (seconds) | `1.0` |
| `PAGE_WAIT_TIMEOUT` | Page load wait time (ms) | `2000` |

## Usage

1. Run the Streamlit application:
    ```sh
    streamlit run main.py
    ```

2. Open your web browser and go to `http://localhost:8501`.

3. Enter the URL you want to scrape in the "Enter New URL" section and click "Scrape URL".

4. Once the content is scraped, you can ask questions about the content in the chat input at the bottom of the page.

## Security Features

- **URL Validation** - Validates URL format and scheme (http/https only)
- **SSRF Protection** - Blocks access to internal/private IP addresses
- **XSS Prevention** - Uses Streamlit's native components for safe rendering
- **Rate Limiting** - Prevents excessive requests to the same domain

## Architecture

The application follows a modular architecture:

- **`config.py`** - Centralized configuration using dataclasses
- **`scraper.py`** - WebScraper class with separate components:
  - `RateLimiter` - Handles request rate limiting
  - `ContentAnalyzer` - Interfaces with Gemini API
- **`ui.py`** - All Streamlit UI components and handlers
- **`utils.py`** - URL validation, SSRF checks, and helpers

## License

MIT License
