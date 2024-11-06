# AI Web Scraper & Chat

This project is an AI-powered web scraper and chat application built using Streamlit. It allows users to scrape content from a given URL and interact with the scraped content through a chat interface.

## Features

- Scrape content from a given URL
- Analyze and query the scraped content
- Display chat history
- Respect robots.txt rules
- Rate limiting for web scraping

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

4. Create a `.env` file and add your Gemini API key:
    ```env
    GEMINI_API_KEY=your_gemini_api_key
    ```

## Usage

1. Run the Streamlit application:
    ```sh
    streamlit run main.py
    ```

2. Open your web browser and go to `http://localhost:8501`.

3. Enter the URL you want to scrape in the "Enter New URL" section and click "Scrape URL".

4. Once the content is scraped, you can ask questions about the content in the chat input at the bottom of the page.

## Project Structure

- `main.py`: The main application file containing the web scraper and chat logic.
- `.env`: Environment variables file (not included in the repository).
