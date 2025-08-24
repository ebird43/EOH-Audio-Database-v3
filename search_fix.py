def perform_search(self):
    """Perform search based on criteria"""
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
        
        # Build search query
        query = """
            SELECT 
                b.title as book_title, 
                e.essay_number, 
                e.title, 
                r.duration, 
                r.id as recording_id
            FROM essays e
            JOIN books b ON e.book_id = b.id
            LEFT JOIN recordings r ON e.id = r.essay_id
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
        results = cursor.fetchall()
        
        # Display results
        for row in results:
            book_title = row['book_title']
            essay_number = row['essay_number']
            title = row['title']
            duration = row['duration'] or "--:--"
            recording_id = row['recording_id']
            
            self.results_tree.insert("", "end", 
                                   values=(book_title, essay_number, title, duration),
                                   tags=(str(recording_id),))
        
        status_text = f"Found {len(results)} matching recordings"
        if len(results) > 0:
            self.root.title(f"Adidam Audio Database - {len(results)} results for '{search_text}'")
        else:
            messagebox.showinfo("Search Results", "No results found for your search")
        
        conn.close()
        
    except Exception as e:
        messagebox.showerror("Search Error", f"Failed to search: {str(e)}")