def main():
    """Main function to run the setup script"""
    print("Adidam Audio Library - Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        print("Error: Python 3.6 or higher is required")
        input("Press Enter to exit...")
        return
    
    # Check and install dependencies
    print("Checking and installing required packages...")
    try:
        import_success, missing_packages = check_dependencies()
        
        if not import_success:
            print(f"Missing required packages: {missing_packages}")
            print("Installing packages...")
            
            install_success, error = install_dependencies()
            if not install_success:
                print(f"Error installing packages: {error}")
                input("Press Enter to exit...")
                return
            
            print("Packages installed successfully")
        else:
            print("All required packages are already installed")
    except Exception as e:
        print(f"Error checking dependencies: {str(e)}")
        input("Press Enter to exit...")
        return
    
    # Set up working directory
    setup_result = setup_working_directory()
    
    if setup_result:
        print("Setup completed successfully")
    else:
        print("Setup was not completed")
    
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()#!/usr/bin/env python
"""
Adidam Audio Library - Setup Script
This script guides you through setting up the entire Adidam Audio Library system.
"""

import os
import sys
import subprocess
import shutil
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog

def check_python_version():
    """Check if Python version is 3.6 or higher"""
    return sys.version_info >= (3, 6)

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import sqlite3
        import PIL
        import docx
        import pygame
        return True
    except ImportError as e:
        return False, str(e)

def install_dependencies():
    """Install required Python packages"""
    packages = [
        "pillow",  # For image processing
        "python-docx",  # For reading Word documents
        "pygame",  # For audio playback
    ]
    
    try:
        for package in packages:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError as e:
        return False, str(e)

def copy_schema_file(working_dir):
    """Create schema.sql in the working directory"""
    schema_content = """-- Database Schema for Adidam Audio Recordings

-- Table for books
CREATE TABLE books (
    id INTEGER PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    cover_image_path VARCHAR(255),
    description TEXT,
    display_order INTEGER DEFAULT 0
);

-- Table for essays (talks)
CREATE TABLE essays (
    id INTEGER PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    book_id INTEGER REFERENCES books(id),
    essay_number VARCHAR(50),
    pages VARCHAR(50),
    description TEXT,
    display_order INTEGER DEFAULT 0
);

-- Main table for recordings
CREATE TABLE recordings (
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

-- Table for categories/tags
CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

-- Junction table for many-to-many relationship between essays and categories
CREATE TABLE essay_categories (
    essay_id INTEGER REFERENCES essays(id),
    category_id INTEGER REFERENCES categories(id),
    PRIMARY KEY (essay_id, category_id)
);

-- Table for reciters/speakers
CREATE TABLE reciters (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    bio TEXT
);

-- Table for user accounts
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT false,
    date_registered DATE NOT NULL
);

-- Table for playlists
CREATE TABLE playlists (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT false,
    date_created DATE NOT NULL
);

-- Table for playlist items
CREATE TABLE playlist_recordings (
    playlist_id INTEGER REFERENCES playlists(id),
    recording_id INTEGER REFERENCES recordings(id),
    position INTEGER NOT NULL,
    date_added DATE NOT NULL,
    PRIMARY KEY (playlist_id, recording_id)
);

-- Table for user favorites
CREATE TABLE user_favorites (
    user_id INTEGER REFERENCES users(id),
    recording_id INTEGER REFERENCES recordings(id),
    date_added DATE NOT NULL,
    PRIMARY KEY (user_id, recording_id)
);

-- Table for user notes on recordings
CREATE TABLE user_notes (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    recording_id INTEGER REFERENCES recordings(id),
    note TEXT NOT NULL,
    date_added DATE NOT NULL
);

-- Table for search keywords
CREATE TABLE keywords (
    id INTEGER PRIMARY KEY,
    essay_id INTEGER REFERENCES essays(id),
    keyword VARCHAR(100) NOT NULL
);

-- Table for transcripts
CREATE TABLE transcripts (
    id INTEGER PRIMARY KEY,
    recording_id INTEGER REFERENCES recordings(id),
    text TEXT,
    is_complete BOOLEAN DEFAULT false
);

-- Indexes for faster searches
CREATE INDEX idx_essays_title ON essays(title);
CREATE INDEX idx_essays_book_id ON essays(book_id);
CREATE INDEX idx_recordings_essay_id ON recordings(essay_id);
CREATE INDEX idx_recordings_title ON recordings(title);
CREATE INDEX idx_recordings_date ON recordings(recorded_date);
CREATE INDEX idx_categories_name ON categories(name);
CREATE INDEX idx_reciters_name ON reciters(name);
CREATE INDEX idx_keywords_keyword ON keywords(keyword);
"""
    
    schema_path = os.path.join(working_dir, "schema.sql")
    with open(schema_path, "w") as f:
        f.write(schema_content)
    
    return schema_path

def create_importer_file(working_dir):
    """Create the importer.py file in the working directory"""
    importer_code = """import sqlite3
import re
import os
import docx
import datetime
import random

class EohIndexImporter:
    def __init__(self, db_path='adidam_recordings.db'):
        self.db_path = db_path
        self.init_db_if_needed()
        
    def init_db_if_needed(self):
        """Initialize the database if it doesn\'t exist"""
        if not os.path.exists(self.db_path):
            print("Creating new database...")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create tables based on our schema
            with open('schema.sql', 'r') as f:
                sql_script = f.read()
                conn.executescript(sql_script)
            
            conn.commit()
            conn.close()
            print("Database initialized successfully")
    
    def import_index_from_docx(self, docx_path):
        """Import data from the EOH Index Word document"""
        if not os.path.exists(docx_path):
            print(f"Error: File not found: {docx_path}")
            return False
            
        try:
            # Open the Word document
            doc = docx.Document(docx_path)
            
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Start a transaction
            conn.execute('BEGIN TRANSACTION')
            
            current_book = None
            book_id = None
            essay_display_order = 0
            
            # Process each paragraph
            for para in doc.paragraphs:
                text = para.text.strip()
                if not text:
                    continue
                
                # Check if this is a book title (in small caps in the original document)
                if text.startswith("*[") and text.endswith("]*"):
                    # Extract book title
                    book_title = text.replace("*[", "").replace("]*", "").replace("{.smallcaps}", "").strip()
                    
                    # Check if this book already exists
                    cursor.execute("SELECT id FROM books WHERE title = ?", (book_title,))
                    existing_book = cursor.fetchone()
                    
                    if existing_book:
                        book_id = existing_book[0]
                        current_book = book_title
                        print(f"Found existing book: {book_title} (ID: {book_id})")
                    else:
                        # Insert new book
                        cursor.execute(
                            "INSERT INTO books (title, display_order) VALUES (?, ?)",
                            (book_title, len(book_title))
                        )
                        book_id = cursor.lastrowid
                        current_book = book_title
                        essay_display_order = 0
                        print(f"Added new book: {book_title} (ID: {book_id})")
                
                # Check if this is an essay entry (has a recording number and title)
                elif current_book and "**" in text:
                    # Parse the essay entry
                    match = re.match(r'\\s*\\*\\*([^*]+)\\*\\*\\s+(.*)', text)
                    if match:
                        essay_number = match.group(1).strip()
                        essay_title = match.group(2).strip()
                        
                        # Clean up the title (remove formatting)
                        essay_title = re.sub(r'\\[([^\\]]+)\\]\\.[\w]+', r'\\1', essay_title)
                        essay_title = re.sub(r'\\{\\.[\w]+\\}', '', essay_title)
                        essay_title = essay_title.replace("[", "").replace("]", "").replace("{.underline}", "")
                        
                        # Handle multiple recording numbers for the same essay
                        essay_numbers = [num.strip() for num in essay_number.split(',')]
                        
                        for num in essay_numbers:
                            # Check if this essay already exists
                            cursor.execute(
                                "SELECT id FROM essays WHERE title = ? AND book_id = ? AND essay_number = ?", 
                                (essay_title, book_id, num)
                            )
                            existing_essay = cursor.fetchone()
                            
                            if existing_essay:
                                essay_id = existing_essay[0]
                                print(f"  Found existing essay: {essay_title} (ID: {essay_id}, Number: {num})")
                            else:
                                # Insert new essay
                                essay_display_order += 1
                                cursor.execute(
                                    """
                                    INSERT INTO essays 
                                    (title, book_id, essay_number, display_order) 
                                    VALUES (?, ?, ?, ?)
                                    """,
                                    (essay_title, book_id, num, essay_display_order)
                                )
                                essay_id = cursor.lastrowid
                                print(f"  Added new essay: {essay_title} (ID: {essay_id}, Number: {num})")
                                
                                # For each essay, create a placeholder recording
                                cursor.execute(
                                    """
                                    INSERT INTO recordings 
                                    (essay_id, title, date_added) 
                                    VALUES (?, ?, ?)
                                    """,
                                    (essay_id, f"Recording of {essay_title}", datetime.date.today().isoformat())
                                )
            
            # Commit the transaction
            conn.commit()
            print("Import completed successfully")
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Error during import: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def import_reciters(self, reciters_list):
        """Import a list of reciters"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Start a transaction
            conn.execute('BEGIN TRANSACTION')
            
            for reciter in reciters_list:
                # Check if reciter already exists
                cursor.execute("SELECT id FROM reciters WHERE name = ?", (reciter,))
                existing = cursor.fetchone()
                
                if not existing:
                    cursor.execute("INSERT INTO reciters (name) VALUES (?)", (reciter,))
                    print(f"Added reciter: {reciter}")
            
            conn.commit()
            print("Reciters import completed")
            return True
            
        except Exception as e:
            conn.rollback()
            print(f"Error importing reciters: {str(e)}")
            return False
        finally:
            conn.close()
    
    def generate_sample_data(self):
        """Generate sample data for demonstration purposes"""
        # List of sample reciters
        sample_reciters = [
            "Will Shea", "Dean Malone", "Abel Slater", "Carolyn Lee", 
            "Ruchiradama Quandra Sukhapur", "Graham Sunderland"
        ]
        
        # Import reciters
        self.import_reciters(sample_reciters)
        
        # Connect to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get all essays
            cursor.execute("SELECT id, title, essay_number FROM essays")
            essays = cursor.fetchall()
            
            # For each essay, update its recording with sample data
            for essay_id, title, essay_number in essays:
                # Generate a sample duration (between 15 and 90 minutes)
                minutes = random.randint(15, 90)
                seconds = random.randint(0, 59)
                duration = f"{minutes:02d}:{seconds:02d}:00"
                
                # Pick a random reciter
                reciter = random.choice(sample_reciters)
                
                # Generate a sample file path
                file_path = f"/recordings/{essay_number}_{title.replace(' ', '_')}.mp3"
                
                # Update the recording
                cursor.execute(
                    """
                    UPDATE recordings
                    SET reciter = ?, duration = ?, file_path = ?, 
                        audio_format = 'MP3', bitrate = 128, sample_rate = 44100
                    WHERE essay_id = ?
                    """,
                    (reciter, duration, file_path, essay_id)
                )
            
            # Add some categories
            categories = [
                "Devotion", "Meditation", "Reality-Practice", "Teaching", 
                "Transcendental Spirituality", "Right Life", "Seventh Stage"
            ]
            
            for category in categories:
                cursor.execute("INSERT INTO categories (name) VALUES (?)", (category,))
            
            # Assign random categories to essays
            for essay_id, _, _ in essays:
                # Assign 1-3 random categories to each essay
                num_categories = random.randint(1, 3)
                cat_ids = random.sample(range(1, len(categories) + 1), num_categories)
                
                for cat_id in cat_ids:
                    cursor.execute(
                        "INSERT OR IGNORE INTO essay_categories (essay_id, category_id) VALUES (?, ?)",
                        (essay_id, cat_id)
                    )
            
            conn.commit()
            print("Sample data generated successfully")
            return True
            
        except Exception as e:
            conn.rollback()
            print(f"Error generating sample data: {str(e)}")
            return False
        finally:
            conn.close()
"""

    importer_path = os.path.join(working_dir, "importer.py")
    with open(importer_path, "w") as f:
        f.write(importer_code)
    
    return importer_path

def create_app_file(working_dir):
    """Create the app.py file in the working directory"""
    app_code = """import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import sqlite3
import os
from PIL import Image, ImageTk
import io
import threading
import pygame
import time
import re

class AdidamAudioLibrary:
    def __init__(self, root, db_path='adidam_recordings.db'):
        self.root = root
        self.db_path = db_path
        self.current_page = 0
        self.books_per_page = 12
        self.current_recording = None
        self.is_playing = False
        
        # Initialize pygame mixer for audio playback
        pygame.mixer.init()
        
        # Setup UI
        self.setup_ui()
        
        # Load books
        self.load_books()
    
    def setup_ui(self):
        """Set up the main user interface"""
        self.root.title("Adidam Audio Library - Ear of Heart")
        self.root.geometry("1200x800")
        self.root.configure(bg="#4169E1")  # Royal blue background
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(3, weight=1)
        
        # Create header frame (blue background)
        header_frame = tk.Frame(self.root, bg="#4169E1", pady=10)
        header_frame.grid(row=0, column=0, sticky="ew")
        
        # Title and subtitle
        title_label = tk.Label(header_frame, text="Ear of Heart", 
                              font=("Arial", 44, "bold"), fg="yellow", bg="#4169E1")
        title_label.pack()
        
        subtitle_label = tk.Label(header_frame, 
                                 text='My Words Should "Come In" By Ear', 
                                 font=("Arial", 22, "italic"), fg="black", bg="#4169E1")
        subtitle_label.pack()
        
        author_label = tk.Label(header_frame, text="—Avatar Adi Da Samraj", 
                               font=("Arial", 22), fg="yellow", bg="#4169E1")
        author_label.pack()
        
        # Search frame
        search_frame = tk.Frame(self.root, bg="#4169E1", pady=10)
        search_frame.grid(row=1, column=0, sticky="ew")
        
        # Make the search centered
        search_frame.columnconfigure(0, weight=1)
        search_frame.columnconfigure(4, weight=1)
        
        # Search widgets
        tk.Label(search_frame, text="Search:", bg="#4169E1", fg="white", 
               font=("Arial", 12)).grid(row=0, column=1, padx=5)
        
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, 
                               width=40, font=("Arial", 12))
        search_entry.grid(row=0, column=2, padx=5)
        search_entry.bind("<Return>", lambda e: self.search_recordings())
        
        search_button = tk.Button(search_frame, text="Search", 
                                 command=self.search_recordings)
        search_button.grid(row=0, column=3, padx=5)
        
        # Separator
        separator = ttk.Separator(self.root, orient="horizontal")
        separator.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        
        # Create a frame for the books grid
        self.books_frame = tk.Frame(self.root, bg="#4169E1")
        self.books_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=10)
        
        # Configure grid for books (6 columns)
        for i in range(6):
            self.books_frame.columnconfigure(i, weight=1)
        
        # Footer with navigation
        footer_frame = tk.Frame(self.root, bg="black", height=40)
        footer_frame.grid(row=4, column=0, sticky="ew")
        
        prev_btn = tk.Button(footer_frame, text="◀", bg="black", fg="white", 
                            font=("Arial", 16), bd=0, command=self.prev_page)
        prev_btn.pack(side="left", padx=20)
        
        self.page_indicator = tk.Label(footer_frame, text="•", bg="black", fg="white", 
                                     font=("Arial", 16))
        self.page_indicator.pack(side="left", padx=20, expand=True)
        
        next_btn = tk.Button(footer_frame, text="▶", bg="black", fg="white", 
                            font=("Arial", 16), bd=0, command=self.next_page)
        next_btn.pack(side="right", padx=20)
        
        # Create audio player frame (initially hidden)
        self.player_frame = tk.Frame(self.root, bg="#2E4DA7", height=80)
        
        # Configure player widgets
        self.setup_player_ui()
    
    def setup_player_ui(self):
        """Set up the audio player UI"""
        # Title label
        self.player_title = tk.Label(self.player_frame, text="", bg="#2E4DA7", fg="white",
                                    font=("Arial", 12, "bold"), anchor="w")
        self.player_title.pack(side="top", fill="x", padx=10, pady=(10, 0))
        
        # Essay and reciter info
        self.player_info = tk.Label(self.player_frame, text="", bg="#2E4DA7", fg="white",
                                  font=("Arial", 10), anchor="w")
        self.player_info.pack(side="top", fill="x", padx=10)
        
        # Controls frame
        controls_frame = tk.Frame(self.player_frame, bg="#2E4DA7")
        controls_frame.pack(side="top", fill="x", padx=10, pady=5)
        
        # Play/pause button
        self.play_btn = tk.Button(controls_frame, text="▶", width=3, 
                                 command=self.toggle_playback)
        self.play_btn.pack(side="left", padx=5)
        
        # Stop button
        stop_btn = tk.Button(controls_frame, text="■", width=3, command=self.stop_playback)
        stop_btn.pack(side="left", padx=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Scale(controls_frame, variable=self.progress_var, 
                                    from_=0, to=100, orient="horizontal", 
                                    command=self.seek_position)
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=10)
        
        # Time labels
        self.current_time = tk.Label(controls_frame, text="0:00", bg="#2E4DA7", fg="white")
        self.current_time.pack(side="left", padx=5)
        
        tk.Label(controls_frame, text="/", bg="#2E4DA7", fg="white").pack(side="left")
        
        self.total_time = tk.Label(controls_frame, text="0:00", bg="#2E4DA7", fg="white")
        self.total_time.pack(side="left", padx=5)
        
        # Volume control
        tk.Label(controls_frame, text="Volume:", bg="#2E4DA7", fg="white").pack(side="left", padx=(20, 5))
        
        self.volume_var = tk.DoubleVar(value=70)
        volume_scale = ttk.Scale(controls_frame, variable=self.volume_var, 
                               from_=0, to=100, orient="horizontal", length=100,
                               command=self.set_volume)
        volume_scale.pack(side="left", padx=5)
        
        # Close button
        close_btn = tk.Button(controls_frame, text="×", width=3, font=("Arial", 10, "bold"),
                             command=self.hide_player)
        close_btn.pack(side="right", padx=5)
        
        # Set initial volume
        self.set_volume(None)
    
    def load_books(self):
        """Load books from the database and display them"""
        # Clear existing book widgets
        for widget in self.books_frame.winfo_children():
            widget.destroy()
        
        try:
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get total number of books to calculate pages
            cursor.execute("SELECT COUNT(*) FROM books")
            total_books = cursor.fetchone()[0]
            self.total_pages = (total_books + self.books_per_page - 1) // self.books_per_page
            
            # Get books for the current page
            cursor.execute(
                """
                SELECT id, title, cover_image_path 
                FROM books 
                ORDER BY display_order
                LIMIT ? OFFSET ?
                """, 
                (self.books_per_page, self.current_page * self.books_per_page)
            )
            books = cursor.fetchall()
            
            # Update page indicator
            self.page_indicator.config(text=f"Page {self.current_page + 1} of {max(1, self.total_pages)}")
            
            # Display books in a grid
            row = 0
            col = 0
            for book_id, title, cover_path in books:
                self.create_book_widget(book_id, title, cover_path, row, col)
                col += 1
                if col > 5:  # 6 columns per row (0-5)
                    col = 0
                    row += 1
            
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load books: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def create_book_widget(self, book_id, title, cover_path, row, col):
        """Create a widget for a book in the grid"""
        frame = tk.Frame(self.books_frame, bg="#4169E1", padx=5, pady=5)
        frame.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
        
        # Book cover
        if cover_path and os.path.exists(cover_path):
            try:
                # Load and resize image
                img = Image.open(cover_path)
                img = img.resize((150, 200), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                cover = tk.Label(frame, image=photo, bg="#4169E1")
                cover.image = photo  # Keep a reference to prevent garbage collection
                cover.pack(padx=5, pady=5)
            except Exception as e:
                # If image loading fails, create a placeholder
                self.create_placeholder_cover(frame, title)
        else:
            # Create a placeholder for missing covers
            self.create_placeholder_cover(frame, title)
        
        # Book title
        title_label = tk.Label(frame, text=title, bg="#4169E1", fg="white", 
                             wraplength=150, font=("Arial", 10, "bold"))
        title_label.pack(padx=5, pady=5)
        
        # Store book_id for click event
        frame.book_id = book_id
        
        # Bind click event to the entire frame and all its children
        frame.bind("<Button-1>", lambda e, id=book_id: self.show_book_essays(id))
        title_label.bind("<Button-1>", lambda e, id=book_id: self.show_book_essays(id))
        
        # Add hover effect
        frame.bind("<Enter>", lambda e, f=frame: self.on_hover(f, True))
        frame.bind("<Leave>", lambda e, f=frame: self.on_hover(f, False))
    
    def create_placeholder_cover(self, parent, title):
        """Create a placeholder for book covers"""
        # Create a colored canvas instead of an image
        canvas = tk.Canvas(parent, width=150, height=200, bg="white", highlightthickness=2, 
                         highlightbackground="white")
        canvas.pack(padx=5, pady=5)
        
        # Add some text to the canvas
        canvas.create_rectangle(0, 0, 150, 200, fill="#FFFFFF", outline="#CCCCCC")
        
        # Create a simpler title by taking the first few words
        short_title = " ".join(title.split()[:3]) + "..."
        canvas.create_text(75, 100, text=short_title, width=130, fill="#333333", 
                          font=("Arial", 12, "bold"), justify="center")
        
        # Bind the canvas to the parent's click event
        canvas.bind("<Button-1>", lambda e, id=getattr(parent, "book_id", None): 
                   self.show_book_essays(id)             if id else None)
    
    def on_hover(self, frame, is_hover):
        """Handle hover effect for book frames"""
        if is_hover:
            frame.config(bg="#3A5FBF")  # Darker blue on hover
            for child in frame.winfo_children():
                if isinstance(child, tk.Label) and child.cget("bg") == "#4169E1":
                    child.config(bg="#3A5FBF")
        else:
            frame.config(bg="#4169E1")  # Return to normal color
            for child in frame.winfo_children():
                if isinstance(child, tk.Label) and child.cget("bg") == "#3A5FBF":
                    child.config(bg="#4169E1")
    
    def prev_page(self):
        """Go to the previous page of books"""
        if self.current_page > 0:
            self.current_page -= 1
            self.load_books()
    
    def next_page(self):
        """Go to the next page of books"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.load_books()
    
    def show_book_essays(self, book_id):
        """Show all essays for a selected book"""
        try:
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get book information
            cursor.execute("SELECT title FROM books WHERE id = ?", (book_id,))
            book_title = cursor.fetchone()[0]
            
            # Create new window for essays
            essays_window = tk.Toplevel(self.root)
            essays_window.title(f"Essays - {book_title}")
            essays_window.geometry("900x700")
            essays_window.configure(bg="#F0F0F0")
            
            # Header frame
            header_frame = tk.Frame(essays_window, bg="#4169E1", padx=10, pady=10)
            header_frame.pack(fill="x")
            
            title_label = tk.Label(header_frame, text=book_title, font=("Arial", 18, "bold"), 
                                  fg="white", bg="#4169E1")
            title_label.pack(side="left")
            
            # Search frame
            search_frame = tk.Frame(essays_window, bg="#F0F0F0", padx=10, pady=10)
            search_frame.pack(fill="x")
            
            tk.Label(search_frame, text="Filter:", bg="#F0F0F0").pack(side="left", padx=(0, 5))
            
            filter_var = tk.StringVar()
            filter_entry = tk.Entry(search_frame, textvariable=filter_var, width=30)
            filter_entry.pack(side="left", padx=5)
            
            filter_button = tk.Button(search_frame, text="Apply", 
                                    command=lambda: self.filter_essays(essay_tree, filter_var.get(), book_id))
            filter_button.pack(side="left", padx=5)
            
            clear_button = tk.Button(search_frame, text="Clear", 
                                   command=lambda: self.reset_essays(essay_tree, filter_var, book_id))
            clear_button.pack(side="left", padx=5)
            
            # Essays tree view
            tree_frame = tk.Frame(essays_window)
            tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Create the treeview
            columns = ("essay_number", "title", "reciter", "duration")
            essay_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
            
            # Define column headings
            essay_tree.heading("essay_number", text="Number")
            essay_tree.heading("title", text="Title")
            essay_tree.heading("reciter", text="Reciter")
            essay_tree.heading("duration", text="Duration")
            
            # Set column widths
            essay_tree.column("essay_number", width=70, anchor="center")
            essay_tree.column("title", width=400)
            essay_tree.column("reciter", width=150)
            essay_tree.column("duration", width=80, anchor="center")
            
            # Add scrollbars
            v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=essay_tree.yview)
            h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=essay_tree.xview)
            essay_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
            
            # Pack scrollbars and tree
            v_scrollbar.pack(side="right", fill="y")
            h_scrollbar.pack(side="bottom", fill="x")
            essay_tree.pack(fill="both", expand=True)
            
            # Get essays for this book
            cursor.execute("""
                SELECT e.id, e.essay_number, e.title, r.reciter, r.duration, r.id
                FROM essays e
                LEFT JOIN recordings r ON e.id = r.essay_id
                WHERE e.book_id = ?
                ORDER BY e.display_order, e.essay_number
            """, (book_id,))
            
            essays = cursor.fetchall()
            
            # Populate tree with essays
            for essay_id, essay_number, title, reciter, duration, recording_id in essays:
                if not reciter:
                    reciter = "Unknown"
                if not duration:
                    duration = "--:--"
                
                # Insert into tree
                essay_tree.insert("", "end", values=(essay_number, title, reciter, duration), 
                                 tags=(str(recording_id),))
            
            # Bind double-click event to play recording
            essay_tree.bind("<Double-1>", self.play_selected_recording)
            
            # Buttons frame
            buttons_frame = tk.Frame(essays_window, padx=10, pady=10)
            buttons_frame.pack(fill="x")
            
            close_button = tk.Button(buttons_frame, text="Close", command=essays_window.destroy)
            close_button.pack(side="right", padx=5)
            
            # Initial load of essays
            self.filter_essays(essay_tree, "", book_id)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load essays: {str(e)}")
        finally:
            if conn:
                conn.close()

    # More methods would go here...

def main():
    # Check for database file
    db_path = 'adidam_recordings.db'
    if not os.path.exists(db_path):
        # Ask user for database location
        db_path = filedialog.askopenfilename(
            title="Select Adidam Recordings Database",
            filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")]
        )
        if not db_path:  # User canceled
            return
    
    # Create and run the application
    root = tk.Tk()
    app = AdidamAudioLibrary(root, db_path)
    root.mainloop()

if __name__ == "__main__":
    main()"""

    app_path = os.path.join(working_dir, "app.py")
    with open(app_path, "w") as f:
        f.write(app_code)
    
    return app_path
    
    def on_hover(self, frame, is_hover):
        """Handle hover effect for book frames"""
        if is_hover:
            frame.config(bg="#3A5FBF")  # Darker blue on hover
            for child in frame.winfo_children():
                if isinstance(child, tk.Label) and child.cget("bg") == "#4169E1":
                    child.config(bg="#3A5FBF")
        else:
            frame.config(bg="#4169E1")  # Return to normal color
            for child in frame.winfo_children():
                if isinstance(child, tk.Label) and child.cget("bg") == "#3A5FBF":
                    child.config(bg="#4169E1")
    
    def prev_page(self):
        """Go to the previous page of books"""
        if self.current_page > 0:
            self.current_page -= 1
            self.load_books()
    
    def next_page(self):
        """Go to the next page of books"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.load_books()
    
    def show_book_essays(self, book_id):
        """Show all essays for a selected book"""
        try:
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get book information
            cursor.execute("SELECT title FROM books WHERE id = ?", (book_id,))
            book_title = cursor.fetchone()[0]
            
            # Create new window for essays
            essays_window = tk.Toplevel(self.root)
            essays_window.title(f"Essays - {book_title}")
            essays_window.geometry("900x700")
            essays_window.configure(bg="#F0F0F0")
            
            # Header frame
            header_frame = tk.Frame(essays_window, bg="#4169E1", padx=10, pady=10)
            header_frame.pack(fill="x")
            
            title_label = tk.Label(header_frame, text=book_title, font=("Arial", 18, "bold"), 
                                  fg="white", bg="#4169E1")
            title_label.pack(side="left")
            
            # Search frame
            search_frame = tk.Frame(essays_window, bg="#F0F0F0", padx=10, pady=10)
            search_frame.pack(fill="x")
            
            tk.Label(search_frame, text="Filter:", bg="#F0F0F0").pack(side="left", padx=(0, 5))
            
            filter_var = tk.StringVar()
            filter_entry = tk.Entry(search_frame, textvariable=filter_var, width=30)
            filter_entry.pack(side="left", padx=5)
            
            filter_button = tk.Button(search_frame, text="Apply", 
                                    command=lambda: self.filter_essays(essay_tree, filter_var.get(), book_id))
            filter_button.pack(side="left", padx=5)
            
            clear_button = tk.Button(search_frame, text="Clear", 
                                   command=lambda: self.reset_essays(essay_tree, filter_var, book_id))
            clear_button.pack(side="left", padx=5)
            
            # Essays tree view
            tree_frame = tk.Frame(essays_window)
            tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Create the treeview
            columns = ("essay_number", "title", "reciter", "duration")
            essay_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
            
            # Define column headings
            essay_tree.heading("essay_number", text="Number")
            essay_tree.heading("title", text="Title")
            essay_tree.heading("reciter", text="Reciter")
            essay_tree.heading("duration", text="Duration")
            
            # Set column widths
            essay_tree.column("essay_number", width=70, anchor="center")
            essay_tree.column("title", width=400)
            essay_tree.column("reciter", width=150)
            essay_tree.column("duration", width=80, anchor="center")
            
            # Add scrollbars
            v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=essay_tree.yview)
            h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=essay_tree.xview)
            essay_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
            
            # Pack scrollbars and tree
            v_scrollbar.pack(side="right", fill="y")
            h_scrollbar.pack(side="bottom", fill="x")
            essay_tree.pack(fill="both", expand=True)
            
            # Get essays for this book
            cursor.execute("""
                SELECT e.id, e.essay_number, e.title, r.reciter, r.duration, r.id
                FROM essays e
                LEFT JOIN recordings r ON e.id = r.essay_id
                WHERE e.book_id = ?
                ORDER BY e.display_order, e.essay_number
            """, (book_id,))
            
            essays = cursor.fetchall()
            
            # Populate tree with essays
            for essay_id, essay_number, title, reciter, duration, recording_