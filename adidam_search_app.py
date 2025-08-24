import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import subprocess  # For cross-platform file opening
import sys

class AdidamSearchApp:
    def __init__(self, root, db_path='adidam_recordings_demo.db'):
        self.root = root
        self.db_path = db_path
        
        # Check if database exists
        if not os.path.exists(db_path):
            messagebox.showwarning("Database Not Found", 
                                 f"Database file '{db_path}' not found. Please place the database file in the same directory as this application.")
        
        # Setup UI
        self.setup_ui()
        
        # Load initial data
        self.load_books()
    
    def setup_ui(self):
        self.root.title("Adidam Audio Database")
        self.root.geometry("1200x700")
        
        # Create main frame
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True)
        
        # Create tabs
        self.books_tab = ttk.Frame(notebook)
        self.search_tab = ttk.Frame(notebook)
        
        notebook.add(self.books_tab, text="Browse by Book")
        notebook.add(self.search_tab, text="Search")
        
        # Setup Books tab
        self.setup_books_tab()
        
        # Setup Search tab
        self.setup_search_tab()
    
    def setup_books_tab(self):
        # Left frame for books list
        left_frame = ttk.Frame(self.books_tab)
        left_frame.pack(side="left", fill="y", padx=5, pady=5)
        
        # Books list
        ttk.Label(left_frame, text="Books").pack(anchor="w")
        self.books_listbox = tk.Listbox(left_frame, width=40, height=30)
        self.books_listbox.pack(fill="both", expand=True)
        self.books_listbox.bind("<<ListboxSelect>>", self.on_book_select)
        
        # Right frame for essays list
        right_frame = ttk.Frame(self.books_tab)
        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        # Book info frame
        book_info_frame = ttk.Frame(right_frame)
        book_info_frame.pack(fill="x", pady=5)
        
        self.book_title_var = tk.StringVar()
        ttk.Label(book_info_frame, textvariable=self.book_title_var, font=("Arial", 12, "bold")).pack(anchor="w")
        
        # Essays list
        ttk.Label(right_frame, text="Essays").pack(anchor="w")
        
        # Create treeview for essays with modified columns for hierarchy
        columns = ("number", "title_or_reciter", "duration")
        self.essays_tree = ttk.Treeview(right_frame, columns=columns, show="tree headings")
        
        # Configure columns
        self.essays_tree.heading("#0", text="")  # Tree column
        self.essays_tree.heading("number", text="#")
        self.essays_tree.heading("title_or_reciter", text="Title / Reciter")
        self.essays_tree.heading("duration", text="Duration")
        
        self.essays_tree.column("#0", width=30)  # Width for expand/collapse arrows
        self.essays_tree.column("number", width=70, anchor="center")
        self.essays_tree.column("title_or_reciter", width=450)
        self.essays_tree.column("duration", width=80, anchor="center")
        
        # Add a scrollbar
        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=self.essays_tree.yview)
        self.essays_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the tree and scrollbar
        self.essays_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Double-click to play recording or expand/collapse
        self.essays_tree.bind("<Double-1>", self.on_essay_double_click)
    
    def setup_search_tab(self):
        # Search frame
        search_frame = ttk.Frame(self.search_tab, padding=5)
        search_frame.pack(fill="x", pady=10)
        
        # Search entry
        ttk.Label(search_frame, text="Search:").pack(side="left", padx=5)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        search_entry.pack(side="left", padx=5)
        search_entry.bind("<Return>", lambda e: self.perform_search())
        
        # Search button
        search_button = ttk.Button(search_frame, text="Search", command=self.perform_search)
        search_button.pack(side="left", padx=5)
        
        # Search options
        ttk.Label(search_frame, text="Search in:").pack(side="left", padx=(20, 5))
        
        self.search_titles_var = tk.BooleanVar(value=True)
        self.search_numbers_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(search_frame, text="Titles", variable=self.search_titles_var).pack(side="left")
        ttk.Checkbutton(search_frame, text="Numbers", variable=self.search_numbers_var).pack(side="left")
        
        # Results frame
        results_frame = ttk.Frame(self.search_tab)
        results_frame.pack(fill="both", expand=True, pady=10)
        
        # Create treeview for search results with hierarchy
        columns = ("book", "number", "title_or_reciter", "duration")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="tree headings")
        
        # Configure columns
        self.results_tree.heading("#0", text="")  # Tree column
        self.results_tree.heading("book", text="Book")
        self.results_tree.heading("number", text="#")
        self.results_tree.heading("title_or_reciter", text="Title / Reciter")
        self.results_tree.heading("duration", text="Duration")
        
        self.results_tree.column("#0", width=30)  # Width for expand/collapse arrows
        self.results_tree.column("book", width=200)
        self.results_tree.column("number", width=70, anchor="center")
        self.results_tree.column("title_or_reciter", width=350)
        self.results_tree.column("duration", width=80, anchor="center")
        
        # Add a scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the tree and scrollbar
        self.results_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Double-click to play recording or expand/collapse
        self.results_tree.bind("<Double-1>", self.on_result_double_click)
    
    def load_books(self):
        """Load all books into the books listbox"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, title FROM books ORDER BY display_order, title")
            books = cursor.fetchall()
            
            self.books_listbox.delete(0, tk.END)
            self.books_data = {}
            
            for book_id, title in books:
                self.books_listbox.insert(tk.END, title)
                self.books_data[title] = book_id
                
            conn.close()
            
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load books: {str(e)}")
    
    def on_book_select(self, event):
        """Handle book selection"""
        selection = self.books_listbox.curselection()
        if not selection:
            return
            
        # Get selected book
        index = selection[0]
        book_title = self.books_listbox.get(index)
        book_id = self.books_data[book_title]
        
        # Update book title display
        self.book_title_var.set(book_title)
        
        # Load essays for this book
        self.load_essays(book_id)
    
    def load_essays(self, book_id):
        """Load essays for the selected book with multiple recordings"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clear existing items
            for item in self.essays_tree.get_children():
                self.essays_tree.delete(item)
            
            # Get essays for this book
            cursor.execute("""
                SELECT e.id, e.essay_number, e.title
                FROM essays e
                WHERE e.book_id = ?
                ORDER BY 
                    CASE 
                        WHEN e.essay_number GLOB '[0-9]*' THEN CAST(e.essay_number AS INTEGER)
                        ELSE 999999
                    END,
                    e.display_order, 
                    e.title
            """, (book_id,))
            
            essays = cursor.fetchall()
            
            # Add each essay as a parent node
            for essay_id, essay_number, title in essays:
                # Clean up title
                clean_title = ' '.join(title.strip().replace('\n', ' ').split())
                
                # Create essay parent item
                essay_item = self.essays_tree.insert("", "end", 
                                                   text="",
                                                   values=(essay_number, clean_title, ""),
                                                   open=False)  # Collapsed by default
                
                # Get recordings for this essay
                cursor.execute("""
                    SELECT r.id, r.title, r.reciter, r.recorded_date, r.duration 
                    FROM recordings r
                    WHERE r.essay_id = ?
                    ORDER BY r.reciter, r.recorded_date
                """, (essay_id,))
                
                recordings = cursor.fetchall()
                
                # Add recordings as child items
                for rec_id, rec_title, reciter, rec_date, duration in recordings:
                    if not duration:
                        duration = "--:--"
                    
                    rec_display_title = rec_title or clean_title
                    rec_date_str = rec_date if rec_date else ""
                    
                    # Display recording info
                    recording_text = f"{reciter or 'Unknown'}"
                    if rec_date_str:
                        recording_text += f" ({rec_date_str})"
                    
                    self.essays_tree.insert(essay_item, "end", 
                                          text="",
                                          values=("", recording_text, duration),
                                          tags=(str(rec_id),))
                
                # If no recordings exist, add a placeholder
                if not recordings:
                    self.essays_tree.insert(essay_item, "end", 
                                          text="",
                                          values=("", "No recordings available", ""),
                                          tags=())
            
            conn.close()
            
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load essays: {str(e)}")
    
    def on_essay_double_click(self, event):
        """Handle double-click on essays tree item"""
        # Get selected item
        item_id = self.essays_tree.focus()
        if not item_id:
            return
            
        # Get item info
        item_info = self.essays_tree.item(item_id)
        
        # Check if it's a recording (has tags with recording ID)
        tags = item_info.get('tags', ())
        if tags and tags[0]:
            # It's a recording, play it
            recording_id = tags[0]
            self.play_recording(recording_id)
        else:
            # It's an essay or placeholder, toggle expand/collapse
            if self.essays_tree.item(item_id, 'open'):
                self.essays_tree.item(item_id, open=False)
            else:
                self.essays_tree.item(item_id, open=True)
    
    def on_result_double_click(self, event):
        """Handle double-click on search results item"""
        # Get selected item
        item_id = self.results_tree.focus()
        if not item_id:
            return
            
        # Get item info
        item_info = self.results_tree.item(item_id)
        
        # Check if it's a recording (has tags with recording ID)
        tags = item_info.get('tags', ())
        if tags and tags[0]:
            # It's a recording, play it
            recording_id = tags[0]
            self.play_recording(recording_id)
        else:
            # It's an essay or placeholder, toggle expand/collapse
            if self.results_tree.item(item_id, 'open'):
                self.results_tree.item(item_id, open=False)
            else:
                self.results_tree.item(item_id, open=True)
    
    def play_recording(self, recording_id):
        """Play a recording"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get recording details
            cursor.execute("""
                SELECT r.file_path, r.title, b.title as book_title, e.title as essay_title, e.essay_number, r.reciter
                FROM recordings r
                JOIN essays e ON r.essay_id = e.id
                JOIN books b ON e.book_id = b.id
                WHERE r.id = ?
            """, (recording_id,))
            
            recording = cursor.fetchone()
            if not recording:
                messagebox.showerror("Play Error", "Recording not found")
                return
                
            file_path, rec_title, book_title, essay_title, essay_number, reciter = recording
            
            if not file_path:
                messagebox.showerror("Play Error", "No file path specified for this recording")
                return
                
            # Check if file exists
            if not os.path.exists(file_path):
                messagebox.showerror("Play Error", f"File not found: {file_path}")
                return
                
            # Use system default player to play the audio file in a cross-platform way
            if os.name == 'nt':  # Windows
                os.startfile(file_path)
            elif os.name == 'posix':  # macOS and Linux
                if os.path.exists('/usr/bin/open'):  # macOS
                    subprocess.call(('open', file_path))
                else:  # Linux
                    subprocess.call(('xdg-open', file_path))
            
            # Update window title with what's playing
            self.root.title(f"Playing: {book_title} - {essay_number} - {essay_title} - {reciter}")
            
            conn.close()
            
        except Exception as e:
            messagebox.showerror("Play Error", f"Failed to play recording: {str(e)}")
    
    def perform_search(self):
        """Perform search based on criteria with support for multiple recordings"""
        search_text = self.search_var.get().strip()
        if not search_text:
            messagebox.showinfo("Search", "Please enter search text")
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # This helps with column names
            cursor = conn.cursor()
            
            # Clear existing results
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
                
            # Reset title
            self.root.title("Adidam Audio Database")
            
            # Get essays matching the search criteria
            query = """
                SELECT 
                    b.title as book_title, 
                    e.id as essay_id,
                    e.essay_number, 
                    e.title as essay_title
                FROM essays e
                JOIN books b ON e.book_id = b.id
                WHERE 
            """
            
            conditions = []
            params = []
            
            # Add title search if enabled
            if self.search_titles_var.get():
                conditions.append("LOWER(e.title) LIKE LOWER(?)")
                params.append(f"%{search_text}%")
                
            # Add number search if enabled
            if self.search_numbers_var.get():
                conditions.append("e.essay_number LIKE ?")
                params.append(f"%{search_text}%")
            
            if not conditions:
                conditions.append("1 = 0")  # No conditions means no results
                
            query += "(" + " OR ".join(conditions) + ")"
            query += " ORDER BY b.title, CAST(CASE WHEN e.essay_number GLOB '*[0-9]*' THEN e.essay_number ELSE '999999' END AS INTEGER)"
            
            cursor.execute(query, params)
            essays = cursor.fetchall()
            
            # Display results as a tree
            for essay in essays:
                book_title = essay['book_title']
                essay_id = essay['essay_id']
                essay_number = essay['essay_number']
                essay_title = essay['essay_title']
                
                # Clean up title
                clean_title = ' '.join(essay_title.strip().replace('\n', ' ').split())
                
                # Add essay as parent node
                essay_item = self.results_tree.insert("", "end", 
                                                    text="",
                                                    values=(book_title, essay_number, clean_title, ""),
                                                    open=False)
                
                # Get recordings for this essay
                cursor.execute("""
                    SELECT r.id, r.title, r.reciter, r.recorded_date, r.duration 
                    FROM recordings r
                    WHERE r.essay_id = ?
                    ORDER BY r.reciter, r.recorded_date
                """, (essay_id,))
                
                recordings = cursor.fetchall()
                
                # Add recordings as child items
                for rec in recordings:
                    rec_id = rec['id']
                    reciter = rec['reciter'] or "Unknown"
                    duration = rec['duration'] or "--:--"
                    rec_date = rec['recorded_date']
                    
                    rec_info = reciter
                    if rec_date:
                        rec_info += f" ({rec_date})"
                    
                    self.results_tree.insert(essay_item, "end", 
                                           text="",
                                           values=(book_title, "", rec_info, duration),
                                           tags=(str(rec_id),))
                
                # If no recordings exist, add a placeholder
                if not recordings:
                    self.results_tree.insert(essay_item, "end", 
                                           text="",
                                           values=(book_title, "", "No recordings available", ""),
                                           tags=())
            
            # Show count in title
            self.root.title(f"Adidam Audio Database - {len(essays)} results for '{search_text}'")
            
            # Show message if no results
            if len(essays) == 0:
                messagebox.showinfo("Search Results", "No results found for your search")
            
            conn.close()
            
        except Exception as e:
            messagebox.showerror("Search Error", f"Error during search: {str(e)}")

# Main execution block
if __name__ == "__main__":
    root = tk.Tk()
    
    # Set app icon if available
    try:
        if os.path.exists("adidam_icon.ico"):
            root.iconbitmap("adidam_icon.ico")
    except:
        pass  # Ignore if icon setting fails
        
    # Create main application
    app = AdidamSearchApp(root)
    
    # Configure window minimum size
    root.minsize(800, 600)
    
    # Start the main loop
    root.mainloop()