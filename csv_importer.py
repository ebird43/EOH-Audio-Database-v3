import sqlite3
import os

def import_from_csv(csv_file, database_file='adidam_recordings.db'):
    """Import recordings data from a CSV file into the SQLite database"""
    
    if not os.path.exists(csv_file):
        print(f"Error: CSV file '{csv_file}' not found.")
        return False
    
    # Check if database exists, if not, initialize it
    db_exists = os.path.exists(database_file)
    if not db_exists:
        if not os.path.exists('schema.sql'):
            print("Error: schema.sql file not found.")
            return False
        
        print(f"Creating new database '{database_file}'...")
        conn = sqlite3.connect(database_file)
        with open('schema.sql', 'r') as f:
            sql_script = f.read()
            conn.executescript(sql_script)
        conn.commit()
        conn.close()
        print("Database initialized.")
    
    # Connect to database
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    
    try:
        # Read CSV file
        with open(csv_file, 'r', encoding='utf-8') as f:
            csv_reader = csv.DictReader(f)
            fieldnames = csv_reader.fieldnames
            
            print(f"Found fields in CSV: {', '.join(fieldnames)}")
            
            # Map CSV fields to database fields
            # Adjust the mappings based on your actual CSV structure
            field_mappings = {
                'Title': 'title',
                'Description': 'description',
                'Date': 'date_recorded',
                'Duration': 'duration',
                'File': 'file_path',
                'Speaker': 'speaker',
                'Categories': 'categories'
                # Add more mappings as needed
            }
            
            # Process each row
            records_processed = 0
            for row in csv_reader:
                # Extract main recording data
                recording_data = {}
                for csv_field, db_field in field_mappings.items():
                    if csv_field in row:
                        recording_data[db_field] = row[csv_field]
                
                # Insert recording
                cursor.execute(
                    """
                    INSERT INTO recordings 
                    (title, description, date_recorded, duration, file_path, date_added)
                    VALUES (?, ?, ?, ?, ?, CURRENT_DATE)
                    """,
                    (
                        recording_data.get('title', 'Unknown Title'),
                        recording_data.get('description', ''),
                        recording_data.get('date_recorded', None),
                        recording_data.get('duration', None),
                        recording_data.get('file_path', None)
                    )
                )
                
                recording_id = cursor.lastrowid
                
                # Process speaker
                if 'speaker' in recording_data and recording_data['speaker']:
                    speaker_name = recording_data['speaker']
                    # Check if speaker exists
                    cursor.execute("SELECT id FROM speakers WHERE name = ?", (speaker_name,))
                    speaker = cursor.fetchone()
                    
                    if not speaker:
                        # Create new speaker
                        cursor.execute("INSERT INTO speakers (name) VALUES (?)", (speaker_name,))
                        speaker_id = cursor.lastrowid
                    else:
                        speaker_id = speaker[0]
                    
                    # Link recording to speaker
                    cursor.execute(
                        "INSERT INTO recording_speakers (recording_id, speaker_id) VALUES (?, ?)",
                        (recording_id, speaker_id)
                    )
                
                # Process categories
                if 'categories' in recording_data and recording_data['categories']:
                    categories = [cat.strip() for cat in recording_data['categories'].split(',')]
                    for category_name in categories:
                        if category_name:
                            # Check if category exists
                            cursor.execute("SELECT id FROM categories WHERE name = ?", (category_name,))
                            category = cursor.fetchone()
                            
                            if not category:
                                # Create new category
                                cursor.execute("INSERT INTO categories (name) VALUES (?)", (category_name,))
                                category_id = cursor.lastrowid
                            else:
                                category_id = category[0]
                            
                            # Link recording to category
                            cursor.execute(
                                "INSERT INTO recording_categories (recording_id, category_id) VALUES (?, ?)",
                                (recording_id, category_id)
                            )
                
                records_processed += 1
            
            conn.commit()
            print(f"Successfully imported {records_processed} recordings.")
            return True
            
    except Exception as e:
        conn.rollback()
        print(f"Error importing data: {str(e)}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    csv_file = input("Enter CSV file path: ")
    import_from_csv(csv_file)