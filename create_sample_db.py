import sqlite3
import os

def create_sample_database(db_path='adidam_recordings_demo.db'):
    """Create a sample database with the expected schema and sample data"""
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except PermissionError:
            print(f"Warning: Could not remove existing database {db_path}. Using it anyway.")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            display_order INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS essays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            essay_number TEXT,
            title TEXT NOT NULL,
            display_order INTEGER DEFAULT 0,
            FOREIGN KEY (book_id) REFERENCES books (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recordings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            essay_id INTEGER NOT NULL,
            title TEXT,
            reciter TEXT,
            recorded_date TEXT,
            duration TEXT,
            file_path TEXT,
            FOREIGN KEY (essay_id) REFERENCES essays (id)
        )
    ''')
    
    # Clear existing data
    cursor.execute("DELETE FROM recordings")
    cursor.execute("DELETE FROM essays")
    cursor.execute("DELETE FROM books")
    
    # Insert sample data
    
    # Sample books - more descriptive titles
    books = [
        (1, "The Dawn Horse Testament", 1),
        (2, "The Aletheon", 2),
        (3, "The Seventeen Companions of the True Dawn Horse", 3),
        (4, "The Bright Field of Consciousness", 4),
        (5, "My 'Bright' Word of Wisdom", 5),
        (6, "The Ego and the Parental Deity", 6),
        (7, "Not-Two Is Peace", 7),
        (8, "The Ancient Walk-About Way", 8),
        (9, "The Enlightenment of the Whole Body", 9),
        (10, "The Eating Gorilla Comes in Peace", 10),
        (11, "The Dreaded Gom-Boo", 11),
        (12, "Atma Nadi Shakti Yoga", 12)
    ]
    
    cursor.executemany(
        "INSERT INTO books (id, title, display_order) VALUES (?, ?, ?)",
        books
    )
    
    # Create lots of essays for each book
    essay_id = 1
    all_essays = []
    
    for book_id in range(1, 13):  # For each book
        # The number of essays varies by book
        num_essays = 20 if book_id <= 5 else 10  # More essays for first 5 books
        
        for essay_num in range(1, num_essays + 1):
            # Generate essay titles based on book and essay number
            if book_id == 1:  # Dawn Horse Testament
                prefix = "The Way of Divine Communion"
            elif book_id == 2:  # Aletheon
                prefix = "Reality-Teaching"
            elif book_id == 3:  # Seventeen Companions
                prefix = "The Process of Divine Transformation"
            elif book_id == 4:  # Bright Field
                prefix = "Consciousness and Light"
            elif book_id == 5:  # My Bright Word
                prefix = "The Divine Heart-Master"
            else:  # Other books
                prefix = "Essay"
                
            title = f"{prefix} {essay_num}"
            
            # For some essays, add more descriptive titles
            if essay_num <= 5:
                if book_id == 1:
                    special_titles = [
                        "Introduction to the Perfect Practice",
                        "The Divine Self-Confession",
                        "The Spiritual Master",
                        "The Way of the Heart",
                        "The Enlightenment of the Whole Body"
                    ]
                    title = special_titles[essay_num - 1]
                elif book_id == 2:
                    special_titles = [
                        "Reality Itself Is the Only Real God",
                        "The Unique Personality of Reality Itself",
                        "My Final Work of Divine Self-Revelation",
                        "The Perfect Freedom of Non-'Difference'",
                        "The Searchless Raw Presumption of Being"
                    ]
                    title = special_titles[essay_num - 1]
                elif book_id == 3:
                    special_titles = [
                        "The Liberating Word",
                        "Transcending the Mind",
                        "The Transcendental Reality-Way",
                        "The Reality-Practice",
                        "The Becoming of Reality-Teaching"
                    ]
                    title = special_titles[essay_num - 1]
            
            all_essays.append((essay_id, book_id, str(essay_num), title, essay_num))
            essay_id += 1
    
    cursor.executemany(
        "INSERT INTO essays (id, book_id, essay_number, title, display_order) VALUES (?, ?, ?, ?, ?)",
        all_essays
    )
    
    # Sample recordings with file paths adjusted for demo
    # Create multiple recordings for the first 5 essays of each of the first 5 books
    recordings = []
    rec_id = 1
    
    # Possible reciters
    reciters = [
        "John Smith", "Jane Doe", "Mark Johnson", "Sarah Williams", 
        "Michael Brown", "David Wilson", "Susan Miller", "Robert Thompson",
        "Emily Davis", "James Wilson", "Mary Thomas", "Richard Lee"
    ]
    
    # Years for recordings
    years = [2010, 2012, 2015, 2017, 2019, 2021, 2023]
    
    # For the first 5 books, add multiple recordings to first 5 essays
    for book_id in range(1, 6):  # First 5 books
        for essay_num in range(1, 6):  # First 5 essays in each book
            # Find the essay_id for this book and essay number
            for essay in all_essays:
                if essay[1] == book_id and essay[2] == str(essay_num):
                    essay_id = essay[0]
                    essay_title = essay[3]
                    break
            
            # Add 2-4 recordings for this essay
            num_recordings = min(essay_num + 1, 4)  # More recordings for later essays
            
            for i in range(num_recordings):
                reciter = reciters[i % len(reciters)]
                year = years[i % len(years)]
                month = (i * 2) % 12 + 1
                day = (i * 7) % 28 + 1
                duration_mins = 15 + (essay_num * 10) + (i * 5)
                duration_secs = (i * 17) % 60
                duration = f"{duration_mins // 60}:{duration_mins % 60:02d}:{duration_secs:02d}"
                
                recording_title = f"{essay_title}" if i == 0 else None
                recording_date = f"{year}-{month:02d}-{day:02d}"
                
                recordings.append((
                    rec_id, 
                    essay_id, 
                    recording_title,
                    reciter, 
                    recording_date, 
                    duration, 
                    "sample.mp3"
                ))
                rec_id += 1
    
    # Add single recordings for some other essays
    for book_id in range(1, 13):  # All books
        essay_start = 6 if book_id <= 5 else 1  # Skip the first 5 essays of first 5 books
        essay_end = 21 if book_id <= 5 else 11  # Different ranges for different books
        
        for essay_num in range(essay_start, essay_end):
            # Every third essay gets a recording
            if essay_num % 3 == 0:
                # Find the essay_id
                for essay in all_essays:
                    if essay[1] == book_id and essay[2] == str(essay_num):
                        essay_id = essay[0]
                        break
                
                reciter = reciters[essay_num % len(reciters)]
                year = years[essay_num % len(years)]
                duration_mins = 30 + (essay_num % 5) * 15
                duration = f"{duration_mins // 60}:{duration_mins % 60:02d}:00"
                
                recordings.append((
                    rec_id,
                    essay_id,
                    None,  # No special title
                    reciter,
                    f"{year}-06-15",
                    duration,
                    "sample.mp3"
                ))
                rec_id += 1
    
    cursor.executemany(
        "INSERT INTO recordings (id, essay_id, title, reciter, recorded_date, duration, file_path) VALUES (?, ?, ?, ?, ?, ?, ?)",
        recordings
    )
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print(f"Sample database created at {db_path}")
    print(f"Created {len(books)} books, {len(all_essays)} essays, and {len(recordings)} recordings")
    print("For a proper demo, place a sample audio file named 'sample.mp3' in the same directory.")
    
    # Return the database path so it can be used
    return db_path

if __name__ == "__main__":
    db_path = create_sample_database()
    print(f"Database creation complete! Database path: {db_path}")
    
    # Update the main app script to use this database
    main_app_path = "adidam_search_app.py"
    if os.path.exists(main_app_path):
        with open(main_app_path, "r") as f:
            content = f.read()
        
        # Update the database path in the main app
        if "db_path='adidam_recordings.db'" in content:
            content = content.replace("db_path='adidam_recordings.db'", f"db_path='{db_path}'")
            
            try:
                with open(main_app_path, "w") as f:
                    f.write(content)
                print(f"Updated {main_app_path} to use the new database")
            except:
                print(f"Could not update {main_app_path}. Please manually update the database path.")
        else:
            print(f"Could not find database path in {main_app_path}. Please manually update the database path.")