import requests
from bs4 import BeautifulSoup
import mysql.connector
import time
import logging
from urllib.parse import urljoin, urlparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Database Connection Configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "knowledge_db"
}

START_URL = "https://www.mnu.ac.ke/"
MAX_PAGES = 50  # Safety limit to prevent infinite run during testing
DOMAIN = "mnu.ac.ke"

def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        logging.error(f"Error connecting to database: {err}")
        return None

def create_qa_table_if_not_exists(cursor):
    """Creates the qa_pairs table if it doesn't exist."""
    table_query = """
    CREATE TABLE IF NOT EXISTS qa_pairs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        question VARCHAR(255) UNIQUE,
        answer TEXT,
        source_url VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    );
    """
    try:
        cursor.execute(table_query)
        logging.info("Ensured 'qa_pairs' table exists.")
    except mysql.connector.Error as err:
        logging.error(f"Error creating table: {err}")

def generate_question_from_url(url, title):
    """Generates a representative question based on the URL or page title."""
    # Heuristics for common pages
    if "contact" in url:
        return "How can I contact the university?"
    elif "admission" in url:
        return f"Information about admissions: {title}"
    elif "school" in url or "facult" in url:
        return f"Information about schools and faculties: {title}"
    else:
        # Generic fallback
        clean_title = title.replace(" - MNU", "").strip()
        return f"What is {clean_title}?"

def is_valid_internal_link(url):
    """Checks if the URL is a valid internal HTML link."""
    parsed = urlparse(url)
    # Must be same domain
    if DOMAIN not in parsed.netloc:
        return False
    # Ignore non-text resources
    ignored_extensions = ('.pdf', '.jpg', '.jpeg', '.png', '.gif', '.css', '.js', '.zip', '.rar')
    path = parsed.path.lower()
    if path.endswith(ignored_extensions):
        return False
    # Ignore anchors/fragments only if they are the only difference (handled by visited set logic usually, but good to be safe)
    return True

def crawl_and_store():
    conn = get_db_connection()
    if not conn:
        return

    cursor = conn.cursor()
    create_qa_table_if_not_exists(cursor)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    queue = [START_URL]
    visited = set()
    pages_crawled = 0

    while queue and pages_crawled < MAX_PAGES:
        url = queue.pop(0)
        
        # Normalize URL (remove fragment/query if needed, strictly we keep query if relevant but for now stick to simple)
        # For simplicity, we'll just strip trailing slash for comparison
        normalized_url = url.rstrip('/')
        if normalized_url in visited:
            continue
            
        visited.add(normalized_url)
        logging.info(f"Crawling ({pages_crawled + 1}/{MAX_PAGES}): {url}")

        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                logging.warning(f"Failed to retrieve {url}. Status: {response.status_code}")
                continue
            
            # Content Type check
            if 'text/html' not in response.headers.get('Content-Type', ''):
                logging.info(f"Skipping non-HTML content: {url}")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # --- EXTRACT CONTENT ---
            content_area = soup.find('main') or soup.find('article') or soup.find('body')
            
            if content_area:
                # Remove script and style elements
                for script in content_area(["script", "style", "nav", "footer", "header"]):
                    script.decompose()
                
                # Extract formatted text
                raw_text = content_area.get_text(separator='\n')
                
                # Clean text
                lines = raw_text.split('\n')
                cleaned_lines = []
                for line in lines:
                    line = line.strip()
                    if line and len(line) > 3 and "Read More" not in line and "Skip to content" not in line:
                         cleaned_lines.append(line)
                
                cleaned_text = "\n\n".join(cleaned_lines)

                if cleaned_text:
                    page_title = soup.title.string if soup.title else "University Page"
                    question = generate_question_from_url(url, page_title)
                    
                    # UPSERT
                    sql = """
                    INSERT INTO qa_pairs (question, answer, source_url)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE answer = VALUES(answer), source_url = VALUES(source_url)
                    """
                    # We use 'question' as unique key, but generated question might duplicate.
                    # To allow multiple pages to have similar titles, we might need a better unique key or just accept overwrite of "generic" titles.
                    # Ideally, source_url should be unique? 
                    # The current schema has `question VARCHAR(255) UNIQUE`. This is a limitation for a crawler.
                    # Constraint: If two pages generate "What is Home?", one overwrites the other.
                    # Fix: Append URL hash or ID to question if needed, or make question specific. 
                    # For now, we'll just try to make the question unique by appending part of the URL path if it's generic.
                    
                    if "What is" in question and question.count(' ') < 3:
                         question += f" ({url})"

                    try:
                        cursor.execute(sql, (question, cleaned_text, url))
                        conn.commit()
                        pages_crawled += 1
                    except mysql.connector.IntegrityError:
                        # Collision on question title, maybe append something and retry?
                        # Or just log and skip
                        logging.warning(f"Duplicate question generated for {url}, skipping insert.")

            # --- DISCOVER LINKS ---
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(url, href)
                
                # Clean URL (remove fragment)
                parsed_href = urlparse(full_url)
                clean_href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
                if parsed_href.query:
                    clean_href += "?" + parsed_href.query
                
                clean_href = clean_href.rstrip('/')

                if is_valid_internal_link(clean_href) and clean_href not in visited and clean_href not in queue:
                    queue.append(clean_href)

            time.sleep(1) # Politeness delay

        except Exception as e:
            logging.error(f"Error crawling {url}: {e}")

    cursor.close()
    conn.close()
    logging.info(f"Crawling completed. Processed {pages_crawled} pages.")

if __name__ == "__main__":
    crawl_and_store()
