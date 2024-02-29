# gui code for the popup containing widgets and display area for viewing the url opening history.

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, PhotoImage
from tkinter.scrolledtext import ScrolledText
from mu_project_01 import open_urls
import csv
import db
import re
import random
import vpn_manager as vpn
import threading
import logging
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

def execute_query(gui_instance, domain, num_urls, from_date, popup):
    """
    Form the query for url opening history and pass 
    the details into db.execute_query()
    """
    try:
        num_urls_int = int(num_urls)  # Convert num_urls to integer
    except ValueError:
        messagebox.showerror(
            "Error", "Number of URLs must be an integer", parent=popup)
        return

    query = """
    SELECT  
        urls.url, 
        COUNT(URL_open_history.URL_id) AS occurrences
    FROM 
        URL_open_history 
    JOIN 
        urls 
    ON 
        URL_open_history.URL_id = urls.id
    JOIN 
        users_urls 
    ON 
        urls.id = users_urls.url_id
    WHERE 
        urls.domain = %s AND URL_open_history.timestamp >= %s
    GROUP BY 
        URL_open_history.URL_id, users_urls.page
    HAVING 
        COUNT(URL_open_history.URL_id) > 1
    ORDER BY 
        users_urls.page ASC, occurrences DESC
    LIMIT %s
    """
    # Execute the query with your database connection
    results = db.execute_query(
        gui_instance.db_config, query, (domain, from_date, num_urls_int))

    #print(query)
    #print(results)

    # Display the results in the query_results_display Text widget
    gui_instance.query_results_display.config(
        state='normal')  # Enable widget for update
    gui_instance.query_results_display.delete(
        '1.0', tk.END)  # Clear existing content
    
    if results:
        # Calculate the max URL length for formatting, with a minimum width, e.g., 70 characters
        max_url_length = max(len(url) for url, occurrences in results)
        max_url_length = max(max_url_length, 70)
         # Header for the columns
        header = f"{'URL'.ljust(max_url_length)}  Count\n"
        divider = f"{'-' * max_url_length}  {'-' * 5}\n"
        gui_instance.query_results_display.insert(tk.END, header)
        gui_instance.query_results_display.insert(tk.END, divider)

        for url, occurrences in results:
            # Left-align the URL and right-align the count, with padding for alignment
            line = f"{url.ljust(max_url_length)}  {str(occurrences).rjust(5)}\n"
            gui_instance.query_results_display.insert(tk.END, line)
        else:
            gui_instance.query_results_display.insert(tk.END, "No results found.")

        gui_instance.query_results_display.config(
        state='disabled')  # Make it read-only again

