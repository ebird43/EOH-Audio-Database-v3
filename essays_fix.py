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
            
            self.essays_tree.insert("", "end", values=(essay_number, title, duration),
                                  tags=(str(recording_id),))
        
        conn.close()
        
    except Exception as e:
        messagebox.showerror("Database Error", f"Failed to load essays: {str(e)}")