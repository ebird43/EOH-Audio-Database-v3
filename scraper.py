import requests
from bs4 import BeautifulSoup
import csv
import time
import re
import sqlite3
import os
from datetime import datetime
from getpass import getpass
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='adidam_scraper.log'
)

class AdidamScraper:
    def __init__(self, db_path='adidam_recordings.db'):
        self.base_url = 'https://secure.adidam.org'
        self.login_url = f'{self.base_url}/Account/LogOn'
        self.ear_of_heart_base = f'{self.base_url}/academy/ear-of-heart'
        self.session = requests.Session()
        self.db_path = db_path
        self.init_db_if_needed()
        
    def init_db_if_needed(self):
        """Initialize the database if it doesn't exist"""
        if not os.path.exists(self.db_path):
            logging.info("Creating new database...")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create tables based on our schema
            with open('schema.sql', 'r') as f:
                sql_script = f.read()
                conn.executescript(sql_script)
            
            conn.commit()
            conn.close()
            logging.info("Database initialized successfully")
    
    def login(self, username, password):
        """Log in to the Adidam website"""
        try:
            # First get the login page to extract any CSRF token or other required fields
            response = self.session.get(self.login_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract anti-forgery token
            token = soup.select_one('input[name="__RequestVerificationToken"]')
            token_value = token['value'] if token else None
            
            # Prepare login data
            login_data = {
                'UserName': username,
                'Password': password,
                'RememberMe': 'true'
            }
            
            if token_value:
                login_data['__RequestVerificationToken'] = token_value
            
            # Attempt login
            response = self.session.post(self.login_url, data=login_data)
            
            # Check if login was successful
            if 'Log Off' in response.text or 'Logout' in response.text:
                logging.info("Login successful")
                return True
            else:
                logging.error("Login failed")
                return False
                
        except Exception as e:
            logging.error(f"Login error: {str(e)}")
            return False
    
    def scrape_page(self, page_number):
        """Scrape a single page of audio recordings"""
        url = f"{self.ear_of_heart_base}/{page_number}"
        logging.info(f"Scraping page {page_number}: {url}")
        
        try:
            response = self.session.get(url)
            if response.status_code != 200:
                logging.error(f"Failed to fetch page {page_number}: Status code {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            recordings = []
            
            # Find all recording entries on the page
            # This selector will need to be adjusted based on the actual HTML structure
            recording_elements = soup.select('.recording-item')  # Adjust selector based on actual page structure
            
            for element in recording_elements:
                recording = {}
                
                # Extract title
                title_elem = element.select_one('.recording-title')
                recording['title'] = title_elem.text.strip() if title_elem else 'Unknown Title'
                
                # Extract description
                desc_elem = element.select_one('.recording-description')
                recording['description'] = desc_elem.text.strip() if desc_elem else ''
                
                # Extract date
                date_elem = element.select_one('.recording-date')
                if date_elem:
                    date_text = date_elem.text.strip()
                    # Try to parse the date
                    try:
                        recording['date_recorded'] = self.parse_date(date_text)
                    except:
                        recording['date_recorded'] = None
                else:
                    recording['date_recorded'] = None
                
                # Extract duration
                duration_elem = element.select_one('.recording-duration')
                recording['duration'] = duration_elem.text.strip() if duration_elem else None
                
                # Extract file information
                file_elem = element.select_one('.recording-file-link')
                if file_elem and 'href' in file_elem.attrs:
                    recording['file_path'] = file_elem['href']
                    # If the file path is relative, make it absolute
                    if recording['file_path'].startswith('/'):
                        recording['file_path'] = f"{self.base_url}{recording['file_path']}"
                else:
                    recording['file_path'] = None
                
                # Extract categories/tags
                tags_elem = element.select('.recording-tag')
                recording['categories'] = [tag.text.strip() for tag in tags_elem] if tags_elem else []
                
                # Extract speaker information
                speaker_elem = element.select_one('.recording-speaker')
                recording['speaker'] = speaker_elem.text.strip() if speaker_elem else 'Adi Da Samraj'  # Default speaker
                
                recordings.append(recording)
            
            logging.info(f"Found {len(recordings)} recordings on page {page_number}")
            return recordings
            
        except Exception as e:
            logging.error(f"Error scraping page {page_number}: {str(e)}")
            return []
    
    def parse_date(self, date_string):
        """Try to parse date string into a standardized format"""
        # Try different date formats (adjust based on the website's formats)
        date_formats = [
            '%B %d, %Y',       # January 1, 2023
            '%b %d, %Y',       # Jan 1, 2023
            '%m/%d/%Y',        # 01/01/2023
            '%Y-%m-%d',        # 2023-01-01
            '%d %B %Y',        # 1 January 2023
            '%d %b %Y',        # 1 Jan 2023
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_string, fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # If no format works, try to extract year, month, day using regex
        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', date_string)
        if year_match:
            # Return just the year if that's all we can extract
            return f"{year_match.group(1)}-01-01"
        
        # If all else fails
        return None
    
    def save_to_database(self, recordings):
        """Save scraped recordings to the SQLite database"""
        if not recordings:
            logging.info("No recordings to save")
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Begin transaction
            conn.execute('BEGIN TRANSACTION')
            
            for recording in recordings:
                # First check if this recording already exists (by title and file path)
                cursor.execute(
                    "SELECT id FROM recordings WHERE title = ? OR file_path = ?",
                    (recording.get('title'), recording.get('file_path'))
                )
                existing = cursor.fetchone()
                
                if existing:
                    recording_id = existing[0]
                    logging.info(f"Recording '{recording.get('title')}' already exists, updating")
                    
                    # Update the existing record
                    cursor.execute(
                        """
                        UPDATE recordings 
                        SET description = ?, date_recorded = ?, duration = ?
                        WHERE id = ?
                        """,
                        (
                            recording.get('description', ''),
                            recording.get('date_recorded'),
                            recording.get('duration'),
                            recording_id
                        )
                    )
                else:
                    # Insert new recording
                    cursor.execute(
                        """
                        INSERT INTO recordings 
                        (title, description, date_recorded, duration, file_path, date_added) 
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            recording.get('title', 'Unknown Title'),
                            recording.get('description', ''),
                            recording.get('date_recorded'),
                            recording.get('duration'),
                            recording.get('file_path'),
                            datetime.now().strftime('%Y-%m-%d')
                        )
                    )
                    recording_id = cursor.lastrowid
                    logging.info(f"Added new recording: '{recording.get('title')}'")
                
                # Process categories/tags
                if recording.get('categories'):
                    for category_name in recording['categories']:
                        # Check if category exists
                        cursor.execute("SELECT id FROM categories WHERE name = ?", (category_name,))
                        category = cursor.fetchone()
                        
                        if not category:
                            # Create new category
                            cursor.execute(
                                "INSERT INTO categories (name) VALUES (?)",
                                (category_name,)
                            )
                            category_id = cursor.lastrowid
                        else:
                            category_id = category[0]
                        
                        # Link recording to category
                        cursor.execute(
                            """
                            INSERT OR IGNORE INTO recording_categories 
                            (recording_id, category_id) VALUES (?, ?)
                            """,
                            (recording_id, category_id)
                        )
                
                # Process speaker
                if recording.get('speaker'):
                    cursor.execute("SELECT id FROM speakers WHERE name = ?", (recording['speaker'],))
                    speaker = cursor.fetchone()
                    
                    if not speaker:
                        # Create new speaker
                        cursor.execute(
                            "INSERT INTO speakers (name) VALUES (?)",
                            (recording['speaker'],)
                        )
                        speaker_id = cursor.lastrowid
                    else:
                        speaker_id = speaker[0]
                    
                    # Link recording to speaker
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO recording_speakers
                        (recording_id, speaker_id) VALUES (?, ?)
                        """,
                        (recording_id, speaker_id)
                    )
            
            # Commit the transaction
            conn.commit()
            logging.info(f"Successfully saved {len(recordings)} recordings to database")
            
        except Exception as e:
            conn.rollback()
            logging.error(f"Database error: {str(e)}")
        finally:
            conn.close()
    
    def export_to_csv(self, filename='adidam_recordings.csv'):
        """Export the database contents to a CSV file"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Query to get all recordings with related data
            query = """
            SELECT 
                r.id, r.title, r.description, r.date_recorded, r.duration, r.file_path,
                r.file_size, r.audio_format, r.bitrate, r.sample_rate, r.date_added,
                r.is_public, r.play_count, r.download_count,
                GROUP_CONCAT(DISTINCT c.name) AS categories,
                GROUP_CONCAT(DISTINCT s.name) AS speakers
            FROM recordings r
            LEFT JOIN recording_categories rc ON r.id = rc.recording_id
            LEFT JOIN categories c ON rc.category_id = c.id
            LEFT JOIN recording_speakers rs ON r.id = rs.recording_id
            LEFT JOIN speakers s ON rs.speaker_id = s.id
            GROUP BY r.id
            ORDER BY r.date_recorded DESC
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            if not rows:
                logging.warning("No recordings found in database to export")
                return
            
            # Write to CSV
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                header = [column[0] for column in cursor.description]
                writer.writerow(header)
                
                # Write data rows
                for row in rows:
                    writer.writerow(row)
            
            logging.info(f"Successfully exported {len(rows)} recordings to {filename}")
            
        except Exception as e:
            logging.error(f"Export error: {str(e)}")
        finally:
            conn.close()

    def run(self, start_page=1, end_page=17):
        """Run the scraper for a range of pages"""
        all_recordings = []
        
        for page_num in range(start_page, end_page + 1):
            page_recordings = self.scrape_page(page_num)
            if page_recordings:
                all_recordings.extend(page_recordings)
                # Save after each page to avoid losing data if something fails
                self.save_to_database(page_recordings)
                # Be nice to the server
                time.sleep(2)
        
        logging.info(f"Scraping complete. Found {len(all_recordings)} recordings in total")
        return all_recordings

def main():
    print("Adidam Audio Recordings Scraper")
    print("=" * 30)
    
    # Initialize scraper
    scraper = AdidamScraper()
    
    # Get login credentials
    username = input("Username: ")
    print("Password: ", end="")
    password = input()
    
    # Log in
    if scraper.login(username, password):
        print("Login successful!")
        
        # Ask for page range
        start_page = int(input("Start page (default 1): ") or 1)
        end_page = int(input("End page (default 17): ") or 17)
        
        # Run scraper
        print(f"Scraping pages {start_page} to {end_page}...")
        recordings = scraper.run(start_page, end_page)
        
        # Export to CSV
        scraper.export_to_csv()
        print(f"Scraping complete! Found {len(recordings)} recordings.")
        print(f"Results saved to database and exported to CSV.")
    else:
        print("Login failed. Please check your credentials and try again.")

if __name__ == "__main__":
    main()