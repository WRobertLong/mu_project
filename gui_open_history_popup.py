# gui code for the popup containing widgets and display area for viewing the url opening history.

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, PhotoImage
from tkinter.scrolledtext import ScrolledText
import db
import mysql.connector as mysql

def open_query_popup(gui_instance):
        # Create a new top-level window
        popup = tk.Toplevel(gui_instance)
        popup.title("Query URLs")
        popup.geometry("1000x800")

        # Domain Entry
        tk.Label(popup, text="Domain:").pack(pady=(10, 0))
        domain_entry = tk.Entry(popup)
        domain_entry.pack(pady=(0, 10))
        domain_entry.insert(0, gui_instance.domain_var.get()) 

        # Number of URLs Entry
        tk.Label(popup, text="Number of URLs to return:").pack(pady=(10, 0))
        num_urls_entry = tk.Entry(popup)
        num_urls_entry.pack(pady=(0, 10))
        num_urls_entry.insert(0, "20") 

        # From Date Entry
        tk.Label(popup, text="From Date (YYYY-MM-DD):").pack(pady=(10, 0))
        from_date_entry = tk.Entry(popup)
        from_date_entry.pack(pady=(0, 10))
        from_date_entry.insert(0, '2023-10-01')

        # Query Button
        query_button = tk.Button(popup, text="Query URLs", command=lambda: gui_instance.execute_query(
            domain_entry.get(),
            num_urls_entry.get(),
            from_date_entry.get(),
            popup  # Passing popup to display results in this window
        ))
        query_button.pack(pady=(10, 0))

        # Results display area with fixed-width font
        text_display = ScrolledText(
            popup, wrap=tk.WORD, width=120, height=20, font=('Courier', 10))
        text_display.pack(pady=(10, 0))
        text_display.config(state='disabled')  # Make it read-only

        # Store for use in execute_query
        gui_instance.query_results_display = text_display


