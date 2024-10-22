import os
import json
import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

class SimpleWebScraper:
    def __init__(self, urls, storage_path="scraped_data", keyword=None):
        self.urls = urls
        self.storage_path = storage_path
        self.keyword = keyword  # Store the keyword for searching
        os.makedirs(self.storage_path, exist_ok=True)
        self.setup_logging()
        self.driver = self.initialize_webdriver()

    def setup_logging(self):
        logging.basicConfig(
            filename='simple_scraper.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        logging.info("Logging initialized.")

    def initialize_webdriver(self):
        options = Options()
        options.add_argument('--headless')  # Run Chrome in headless mode
        options.add_argument('--disable-gpu')
        try:
            driver = webdriver.Chrome(options=options)
            logging.info("WebDriver initialized successfully.")
            return driver
        except Exception as e:
            logging.error(f"Failed to initialize WebDriver: {e}")
            raise

    def fetch_page(self, url):
        try:
            logging.info(f"Fetching URL: {url}")
            self.driver.get(url)
            time.sleep(2)  # Wait for the page to load; adjust as necessary
            page_source = self.driver.page_source
            logging.info(f"Successfully fetched: {url}")
            return page_source
        except Exception as e:
            logging.error(f"Error fetching {url}: {e}")
            return None

    def parse_content(self, html_content):
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extracting different elements and their attributes
            data = {
                "paragraphs": [p.get_text(strip=True) for p in soup.find_all('p')],
                "images": [{"src": img.get('src'), "alt": img.get('alt', '')} for img in soup.find_all('img')],
                "links": [{"text": a.get_text(strip=True), "href": a.get('href')} for a in soup.find_all('a', href=True)],
                "headings": {
                    "h1": [h1.get_text(strip=True) for h1 in soup.find_all('h1')],
                    "h2": [h2.get_text(strip=True) for h2 in soup.find_all('h2')],
                    "h3": [h3.get_text(strip=True) for h3 in soup.find_all('h3')]
                }
            }

            logging.info("Content parsed successfully.")
            return data
        except Exception as e:
            logging.error(f"Error parsing content: {e}")
            return {}

    def save_data(self, url, data):
        try:
            # Create a safe filename from the URL
            filename = url.replace("http://", "").replace("https://", "").replace("/", "_") + ".json"
            file_path = os.path.join(self.storage_path, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            logging.info(f"Data saved to {file_path}")
        except Exception as e:
            logging.error(f"Error saving data for {url}: {e}")

    def search_keyword(self, data):
        if self.keyword:
            # Filter paragraphs and headings for the keyword
            filtered_data = {
                "paragraphs": [p for p in data["paragraphs"] if self.keyword.lower() in p.lower()],
                "headings": {
                    "h1": [h1 for h1 in data["headings"]["h1"] if self.keyword.lower() in h1.lower()],
                    "h2": [h2 for h2 in data["headings"]["h2"] if self.keyword.lower() in h2.lower()],
                    "h3": [h3 for h3 in data["headings"]["h3"] if self.keyword.lower() in h3.lower()]
                }
            }
            return filtered_data
        return data  # Return original data if no keyword is set

    def run(self):
        for url in self.urls:
            html_content = self.fetch_page(url)
            if html_content:
                parsed_data = self.parse_content(html_content)
                filtered_data = self.search_keyword(parsed_data)  # Search for the keyword
                self.save_data(url, filtered_data)
        self.shutdown()

    def shutdown(self):
        if self.driver:
            self.driver.quit()
            logging.info("WebDriver shut down.")
        logging.info("Scraper finished running.")

if __name__ == "__main__":
    # Example usage
    urls_to_scrape = [
        "https://en.wikipedia.org/wiki/Grumman_F-14_Tomcat",
        "https://www.wikipedia.org",
        # Add more URLs as needed
    ]
    
    # Prompt the user for a keyword to search for
    keyword_to_search = input("Enter a keyword to search for: ")  # User input for keyword

    scraper = SimpleWebScraper(urls=urls_to_scrape, keyword=keyword_to_search)
    scraper.run()
