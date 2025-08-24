import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import os

class AdidamSearchApp:
    def __init__(self, root, db_path='adidam_recordings.db'):
        self.root = root
        self.db_path = db_path
        
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
        
        # Create treeview for essays
        self.essays_tree.heading("#0", text="")  # Tree column
        self.essays_tree.heading("number", text="#")
        self.essays_tree.heading("title_or_reciter", text="Title / Reciter")
        self.essays_tree.heading("duration", text="Duration")
    
        self.essays_tree.column("#0", width=30)  # Width for expand/collapse arrows
        self.essays_tree.column("number", width=70, anchor="center")
        self.essays_tree.column("title_or_reciter", width=450)
        self.essays_tree.column("duration", width=80, anchor="center")
        
        # Configure columns
        self.essays_tree.heading("number", text="#")
        self.essays_tree.heading("title", text="Title")
        self.essays_tree.heading("duration", text="Duration")
        
        self.essays_tree.column("number", width=70, anchor="center")
        self.essays_tree.column("title", width=500)
        self.essays_tree.column("duration", width=80, anchor="center")
        
        # Add a scrollbar
        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=self.essays_tree.yview)
        self.essays_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the tree and scrollbar
        self.essays_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Double-click to play recording
        self.essays_tree.bind("<Double-1>", self.on_essay_double_click)
    
    def setup_search_tab(self):
        # Search frame
        search_frame = ttk.Frame(self.search_tab, padding=5)
        search_frame.pack(fill="x", pady=10)
    
    def setup_search_tab(self):
        # [Existing code...]
    
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
        
        # Create treeview for search results with modified columns
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
    
    # [Rest of existing code...]
        
        # Add a scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the tree and scrollbar
        self.results_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Double-click to play recording
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
    """Load essays for the selected book"""
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear existing items
        for item in self.essays_tree.get_children():
            self.essays_tree.delete(item)
        
        # Get essays for this book
        cursor.execute("""
            SELECT e.id, e.essay_number, e.title, r.duration, r.id as recording_id
            FROM essays e
            LEFT JOIN recordings r ON e.id = r.essay_id
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
        
        for essay_id, essay_number, title, duration, recording_id in essays:
            if not duration:
                duration = "--:--"
            
            # Clean up title - replace multiple spaces and line breaks with single space
            clean_title = ' '.join(title.strip().replace('\n', ' ').split())
            
            self.essays_tree.insert("", "end", values=(essay_number, clean_title, duration),
                                  tags=(str(recording_id),))
        
        conn.close()
        
    except Exception as e:
        messagebox.showerror("Database Error", f"Failed to load essays: {str(e)}")

            cursor.execute("""
                SELECT e.id, e.essay_number, e.title, r.duration, r.id as recording_id
                FROM essays e
                LEFT JOIN recordings r ON e.id = r.essay_id
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
            
            for essay_id, essay_number, title, duration, recording_id in essays:
                if not duration:
                    duration = "--:--"
                
                # Clean up title - replace multiple spaces and line breaks with single space
                clean_title = ' '.join(title.strip().replace('\n', ' ').split())
                
                self.essays_tree.insert("", "end", values=(essay_number, clean_title, duration),
                                      tags=(str(recording_id),))
            
            conn.close()
            
        except Exception as e:
        messagebox.showerror("Database Error", f"Failed to load essays: {str(e)}")
    
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
        
        # Configure results tree for hierarchy
        self.results_tree['show'] = 'tree headings'
        
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
        
        # Update status
        status_text = f"Found {len(essays)} matching essays"
        if len(essays) > 0:
            self.root.title(f"Adidam Audio Database - {len(essays)} results for '{search_text}'")
        else:
            messagebox.showinfo("Search Results", "No results found for your search")
        
        conn.close()
        
    except Exception as e:
        messagebox.showerror("Search Error", f"Failed to search: {str(e)}")
    
    def on_result_double_click(self, event):
        """Handle double-clicking on a search result"""
    selection = self.results_tree.selection()
    if not selection:
        return
    
    item = selection[0]
    tags = self.results_tree.item(item, "tags")
    
    # Check if this is a recording (has a tag) or an essay (parent item)
    if tags and tags[0]:
        # It's a recording, play it
        recording_id = tags[0]
        self.play_recording(recording_id)
    else:
        # It's an essay parent, toggle expand/collapse
        if self.results_tree.item(item, "open"):
            self.results_tree.item(item, open=False)
        else:
            self.results_tree.item(item, open=Tr
    
    def on_result_double_click(self, event):
        """Handle double-clicking on a search result"""
        selection = self.results_tree.selection()
        if not selection:
            return
            
        item = selection[0]
        recording_id = self.results_tree.item(item, "tags")[0]
        
        self.play_recording(recording_id)
    
    def play_recording(self, recording_id):
        """Play the selected recording"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT r.title, r.file_path, b.title as book_title, e.title as essay_title
                FROM recordings r
                JOIN essays e ON r.essay_id = e.id
                JOIN books b ON e.book_id = b.id
                WHERE r.id = ?
            """, (recording_id,))
            
            recording = cursor.fetchone()
            conn.close()
            
            if not recording:
                messagebox.showinfo("Play", "Recording not found")
                return
                
            title, file_path, book_title, essay_title = recording
            
            # For now, just show a message - in a real app, you'd play the file
            message = f"Playing: {title or essay_title}\n"
            message += f"From: {book_title}\n"
            
            if file_path and os.path.exists(file_path):
                message += f"File: {file_path}"
                # Here you would add code to actually play the audio file
            else:
                message += "No audio file available yet"
            
            messagebox.showinfo("Play Recording", message)
            
        except Exception as e:
            messagebox.showerror("Playback Error", f"Failed to play recording: {str(e)}")


def main():
    root = tk.Tk()
    app = AdidamSearchApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()