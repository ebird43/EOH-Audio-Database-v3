import os
import sys
import sqlite3

def create_directory_structure():
    """Create the basic directory structure"""
    print("Creating directory structure...")
    
    # Create directories
    os.makedirs("images", exist_ok=True)
    os.makedirs("recordings", exist_ok=True)
    
    print("Directories created successfully")

def create_database():
    """Create or update the database"""
    print("Setting up database...")
    
    # Connect to database (will create if doesn't exist)
    conn = sqlite3.connect("adidam_recordings.db")
    cursor = conn.cursor()
    
    # Check if tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='books'")
    table_exists = cursor.fetchone()
    
    if not table_exists:
        print("Creating tables...")
        # Create basic tables
        cursor.executescript('''
            -- Table for books
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                cover_image_path VARCHAR(255),
                description TEXT,
                display_order INTEGER DEFAULT 0
            );

            -- Table for essays (talks)
            CREATE TABLE IF NOT EXISTS essays (
                id INTEGER PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                book_id INTEGER REFERENCES books(id),
                essay_number VARCHAR(50),
                pages VARCHAR(50),
                description TEXT,
                display_order INTEGER DEFAULT 0
            );

            -- Main table for recordings
            CREATE TABLE IF NOT EXISTS recordings (
                id INTEGER PRIMARY KEY,
                essay_id INTEGER REFERENCES essays(id),
                title VARCHAR(255) NOT NULL,
                reciter VARCHAR(100),
                recorded_date DATE,
                duration TIME,
                file_path VARCHAR(255),
                file_size INTEGER,
                audio_format VARCHAR(50),
                bitrate INTEGER,
                sample_rate INTEGER,
                date_added DATE,
                play_count INTEGER DEFAULT 0,
                download_count INTEGER DEFAULT 0,
                display_order INTEGER DEFAULT 0
            );
        ''')
        
        # Add some sample data
        print("Adding sample data...")
        cursor.execute("INSERT INTO books (title, display_order) VALUES (?, ?)", 
                      ("The Aletheon", 1))
        
        book_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO essays (title, book_id, essay_number, display_order) 
            VALUES (?, ?, ?, ?)
        """, ("Acausal Adidam", book_id, "349", 1))
        
        essay_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO recordings (essay_id, title, reciter, duration) 
            VALUES (?, ?, ?, ?)
        """, (essay_id, "Recording of Acausal Adidam", "Will Shea", "45:20"))
        
        print("Sample data added")
    else:
        print("Database tables already exist")
        
        # Count existing records
        cursor.execute("SELECT COUNT(*) FROM books")
        book_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM essays")
        essay_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM recordings")
        recording_count = cursor.fetchone()[0]
        
        print(f"Current database contains: {book_count} books, {essay_count} essays, {recording_count} recordings")
    
    # Commit and close
    conn.commit()
    conn.close()
    
    print("Database setup complete")

def main():
    print("Adidam Audio Database Setup")
    print("==========================")
    
    create_directory_structure()
    create_database()
    
    print("\nSetup completed successfully!")
    print("Next steps:")
    print("1. Import your EOH Index.docx file (write your own import script)")
    print("2. Add real audio files to the recordings folder")
    print("3. Create a simple UI to browse and search recordings")
    
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()