# gui.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, PhotoImage
from tkinter.scrolledtext import ScrolledText
import csv
import db
import re
import random
import vpn_manager as vpn
import threading
import logging
import mysql.connector as mysql
import gui_open_history_popup
from functools import partial
from typing import List, Tuple, Union, Dict
#import time
#import subprocess
from utils import open_urls

class URLManagerGUI(tk.Tk):

    def __init__(self, db_config=None, gui_config=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_config = db_config if db_config is not None else {}
        self.gui_config = gui_config if gui_config is not None else {}

        config = db.load_config()
        
        # Set up logging
        log_filename = config.get('main_config', {}).get('log_filename', 'default.log')
        log_path = config.get('main_config', {}).get('main_path', './') + log_filename

        # Setup logging with dynamic configuration
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            filename=log_path)


        self.db_config = config['db_config']
        gui_config = config['gui_config']
        self.sleep_params = config['main_config']['sleep_params']

        icon_file = config['main_config']['main_path'] + config['gui_config']['mu_icon']

        icon = PhotoImage(file = icon_file)
        self.iconphoto(True, icon) 

        # Load browser configurations from the database
        self.browsers = db.get_browsers(self.db_config)

        # Initialize ttk styles
        self.style = ttk.Style(self)
        self.style.theme_use('default')

        # Select a default browser
        self.selected_browser = next(
            iter(self.browsers)) if self.browsers else None

        # Load domains from the database
        domain_options, default_domain = db.get_domains(self.db_config)

        # Setup the domain dropdown
        self.domain_var = tk.StringVar(self)
        self.domain_var.set(default_domain)
        self.optionmenu_domain = tk.OptionMenu(
            self, self.domain_var, *domain_options)
        self.optionmenu_domain.pack(pady=(0, 10))

        self.setup_file_selection()
        self.setup_url_entry()
        self.setup_export_to_csv()
        self.setup_vpn_controls()
        self.setup_url_loading()

        # Update the display to show the VPN status and the selected browser
        self.update_vpn_status_display()

    def get_browsers(self) -> list:#
        # getter function for browsers
        return self.browsers
    
    def get_sleep_params(self) -> tuple:
        # getter function for sleep parameters
        return self.sleep_params
    
    def setup_file_selection(self) -> None:
        # File Selection
        self.label_file = tk.Label(self, text="No file selected")
        self.label_file.pack()
        self.button_select_file = tk.Button(
            self, text="Select File", command=self.select_file)
        self.button_select_file.pack()
        self.button_upload = tk.Button(
            self, text="Upload URLs", command=self.bulk_upload)
        self.button_upload.pack(pady=(10, 0))

    def setup_url_entry(self) -> None:
        # Additional URL Entry
        self.label_url = tk.Label(self, text="URL:")
        self.label_url.pack(pady=(10, 0))
        self.entry_url = tk.Entry(self)
        self.entry_url.pack(pady=(0, 10))
        self.button_upload_single = tk.Button(
            self, text="Upload Single URL", command=self.upload_single_url)
        self.button_upload_single.pack(pady=(10, 0))
        self.button_clear = tk.Button(
            self, text="Clear All URLs", command=self.clear_urls)
        self.button_clear.pack(pady=(10, 0))

    def setup_export_to_csv(self) -> None:
        # Filename Entry for export
        self.label_filename = tk.Label(self, text="Filename:")
        self.label_filename.pack(pady=(10, 0))
        self.entry_filename = tk.Entry(self)
        self.entry_filename.pack(pady=(0, 10))
        self.button_export_csv = tk.Button(
            self, text="Export to CSV", command=self.export_to_csv)
        self.button_export_csv.pack(pady=(10, 0))

    def setup_vpn_controls(self) -> None:
        # VPN/Browser-related widgets in a frame
        # This will contain 2 rows, one for the connect and check buttons and the browser dropdown
        # And below it the radio buttons that will control details of the URLs to be fetched.

        vpn_frame = tk.Frame(self)
        vpn_frame.pack(pady=(10, 0))

        # Top frame for the VPN buttons and browser selection
        top_frame = tk.Frame(vpn_frame)
        top_frame.pack(fill=tk.X)

        # Connect VPN Button
        button_connect_vpn = tk.Button(
            top_frame, text="Connect VPN", command=self.connect_vpn)
        button_connect_vpn.pack(side=tk.LEFT, padx=(0, 10))

        # Disconnect VPN Button
        button_disconnect_vpn = tk.Button(
            top_frame, text="Disconnect VPN", command=self.disconnect_vpn)
        button_disconnect_vpn.pack(side=tk.LEFT, padx=(0, 10))

        # Check VPN Status Button
        button_check_vpn = tk.Button(
            top_frame, text="Check VPN Status", command=self.update_vpn_status_display)
        button_check_vpn.pack(side=tk.LEFT, padx=(0, 10))

        # Frame for the Combobox with a border
        # You can adjust borderwidth and relief
        combobox_frame = tk.Frame(top_frame, borderwidth=2, relief="groove")
        combobox_frame.pack(side=tk.LEFT, padx=(0, 10))

        # Browser Selection Combobox within the bordered frame
        self.browser_var = tk.StringVar(self)
        self.browsers_combo = ttk.Combobox(combobox_frame, textvariable=self.browser_var, values=list(
            self.browsers.keys()), state="readonly")
        # Padding inside the combobox frame to simulate a border
        self.browsers_combo.pack(padx=2, pady=2)
        self.browsers_combo.bind(
            "<<ComboboxSelected>>", self.on_browser_selected)
        if self.browsers:
            self.browser_var.set(self.selected_browser)

        # VPN Status Display
        self.text_vpn_status = ScrolledText(
            self, wrap=tk.WORD, width=40, height=10, state='disabled')
        self.text_vpn_status.pack(pady=(5, 10))

        # Add a button to open the query popup
        self.setup_query_popup_button()

    def setup_query_popup_button(self) -> None:
        # Button to open the URL query popup
        popup_command = lambda: gui_open_history_popup.open_query_popup(self)
        self.button_open_query_popup = tk.Button(self, text="URL Query History", command=popup_command)
        self.button_open_query_popup.pack(pady=(10, 0))

    def on_radio_change(self):
        print(
            f"Selected URL Loading Preference: {self.url_loading_preference.get()}")

    def setup_url_loading(self) -> None:
        # Frame for URL loading, including the "Needed number of URLs" and radio buttons
        url_frame = tk.Frame(self)
        url_frame.pack(pady=(10, 0))

        # Part of the frame for "Needed number of URLs"
        url_entry_frame = tk.Frame(url_frame)
        url_entry_frame.pack(side=tk.LEFT, padx=(10, 10))

        tk.Label(url_entry_frame, text="Needed number of URLs:").pack(
            side=tk.LEFT)
        self.entry_needed_urls = tk.Entry(url_entry_frame)
        self.entry_needed_urls.pack(side=tk.LEFT)

        self.url_loading_preference = tk.StringVar(
            value="Most Recent")  # Default to newest

        # Frame for the radio buttons, placed alongside the "Needed number of URLs"
        radio_button_frame = tk.Frame(url_frame)
        radio_button_frame.pack(side=tk.LEFT, padx=(20, 10))

        # Radio buttons for URL loading preference
        ttk.Radiobutton(radio_button_frame, text="Most Recent", variable=self.url_loading_preference,
                        value="Most Recent", command=self.on_radio_change).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Radiobutton(radio_button_frame, text="Oldest", variable=self.url_loading_preference,
                        value="Oldest", command=self.on_radio_change).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Radiobutton(radio_button_frame, text="Random page", variable=self.url_loading_preference,
                        value="Random page", command=self.on_radio_change).pack(side=tk.LEFT, padx=(5, 0))

        # Add "Load URLs" and "Open URLs" Buttons
        button_load_urls = tk.Button(
            url_frame, text="Load URLs", command=self.load_urls)
        button_load_urls.pack(side=tk.LEFT, padx=(10, 10))

        button_open_urls = tk.Button(
            url_frame, text="Open URLs", command=self.execute_open_urls)
        button_open_urls.pack(side=tk.LEFT, padx=(10, 10))

        # Display area for URLs
        self.text_display_urls = ScrolledText(
            self, wrap=tk.WORD, width=100, height=15, state='disabled')
        self.text_display_urls.pack(pady=(10, 0))

    def setup_url_loading_old(self) -> None:
        # Frame for URL loading and browser selection
        url_frame = tk.Frame(self)
        url_frame.pack(pady=(10, 0))
        button_load_urls = tk.Button(
            url_frame, text="Load URLs", command=self.load_urls)
        button_load_urls.pack(side=tk.LEFT, padx=(0, 10))

        # Needed number of URLs Entry
        tk.Label(url_frame, text="Needed number of URLs:").pack(pady=(10, 0))
        self.entry_needed_urls = tk.Entry(url_frame)
        self.entry_needed_urls.pack(pady=(0, 10))

        # Add "Open URLs" Button
        button_open_urls = tk.Button(
            url_frame, text="Open URLs", command=self.execute_open_urls)
        button_open_urls.pack(side=tk.LEFT, padx=(10, 10))

        # Display area for URLs
        self.text_display_urls = ScrolledText(
            self, wrap=tk.WORD, width=100, height=15, state='disabled')
        self.text_display_urls.pack(pady=(10, 0))

    def select_file(self) -> None:
        """
        Open a file dialog to select a file, and update the label to show the selected file's name.
        """
        self.selected_file = filedialog.askopenfilename(
            title="Select a file", filetypes=(("Text files", "*.txt"), ("All files", "*.*")))
        if self.selected_file:
            self.label_file.config(
                text=f"Selected File: {self.selected_file.split('/')[-1]}")

    def bulk_upload(self) -> None:
        """
        Upload multiple URLs from the selected file to the database, under the selected domain.
        """
        domain = self.domain_var.get()
        if self.selected_file and domain:
            count = db.upload_urls_from_file(
                self.db_config, self.selected_file, domain)
            messagebox.showinfo("Upload Complete",
                                f"{count} URLs have been uploaded.")
        else:
            messagebox.showwarning("Missing Information",
                                   "Please select a file and enter a domain.")

    def upload_single_url(self) -> None:
        """
        Upload a single URL, entered in the text entry field, to the database under the selected domain.
        """
        url = self.entry_url.get()
        domain = self.entry_domain.get()
        if not url:
            messagebox.showwarning("Missing Information",
                                   "Please enter a URL.")    
    
    def disconnect_vpn(self) -> None:
        try:
        # Attempt to disconnect from the VPN
            if not vpn.disconnect_vpn():
                logging.critical("Failed to disconnect to VPN.")
                messagebox.showerror(
                    "VPN Disconnection Failed")
                return  # Exit the function, but don't quit the application
            messagebox.showinfo(
                "VPN Connection", "VPN successfully disconnected.")
            self.update_vpn_status_display()
        except Exception as e:
            messagebox.showerror("VPN Disconnection Failed", str(e))
            return
        # Assuming URL validation is desired; simplistic check:
        if not url.startswith('http://') and not url.startswith('https://'):
            messagebox.showwarning(
                "Invalid URL", "URL must start with http:// or https://")
            return
        try:
            db.insert_url(self.db_config, url, domain)
            messagebox.showinfo("Success", "URL has been uploaded.")
            # Clear the URL entry after successful upload
            self.entry_url.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to upload URL: {e}")

    def clear_urls(self) -> None:
        """
        Clear all URLs from the database after confirming with the user, with detailed error handling.
        """
        # Confirm with the user before proceeding
        confirmation = messagebox.askyesno(
            "Confirm Clear", "This will remove all URLs from the database. This cannot be undone. Do you want to proceed?")
        if not confirmation:  # If the user does not confirm, exit the method
            return
        try:
            # Attempt to clear all URLs from the database
            db.clear_all_urls(self.db_config)
            messagebox.showinfo(
                "Clear URLs", "All URLs have been deleted from the database.")
        except mysql.IntegrityError as ie:
            messagebox.showerror(
                "Integrity Error", f"An integrity error occurred: {ie}")
        except mysql.DataError as de:
            messagebox.showerror("Data Error", f"A data error occurred: {de}")
        except mysql.DatabaseError as dbe:
            messagebox.showerror(
                "Database Error", f"A database error occurred: {dbe}")
        except mysql.InterfaceError as ife:
            messagebox.showerror(
                "Interface Error", f"A connection error occurred: {ife}")
        except mysql.Error as e:  # Catch-all for any other MySQL-related errors
            messagebox.showerror(
                "Database Error", f"An error occurred while trying to clear URLs: {e}")
        finally:
            pass 

    def export_to_csv(self) -> None:
        """
        Export URLs from the database, filtered by the selected domain, to a CSV file.
        """
        domain = self.domain_var.get()
        filename = self.entry_filename.get().strip()
        if not filename:
            filename = "urls.csv"  # Default filename
        elif not filename.endswith('.csv'):
            filename += '.csv'

        # Fetch URLs from the database for the selected domain
        urls = db.get_all_urls(self.db_config, domain)

        # Write URLs to a CSV file
        try:
            with open(filename, 'w', newline='') as file:
                writer = csv.writer(file)
                for url in urls:
                    writer.writerow([url])
            messagebox.showinfo("Export Successful",
                                f"URLs exported to {filename}.")
        except Exception as e:
            messagebox.showerror("Export Failed", f"An error occurred: {e}")

    def update_vpn_status_display(self) -> None:
        """
        Fetches and displays the formatted VPN status along with the current default browser.
        """
        status_info = vpn.get_vpn_status()  # Fetches the VPN status as a dictionary

        # Correctly reference the browser's name using self.selected_browser
        browser_info = f"Default Browser: {self.selected_browser}" if self.selected_browser else "No Browser Selected"

        if isinstance(status_info, dict):
            formatted_status = "\n".join(
                f"{key}: {value}" for key, value in status_info.items())
        else:
            formatted_status = "Unable to fetch VPN status."

        combined_status = f"{formatted_status}\n\n{browser_info}"

        self.text_vpn_status.config(state='normal')
        self.text_vpn_status.delete('1.0', tk.END)
        self.text_vpn_status.insert(tk.END, combined_status)
        self.text_vpn_status.config(state='disabled')

    def load_urls(self) -> None:
        """
        Function to load the URLs based on weighted sampling without replacement.
        """
        needed = int(self.entry_needed_urls.get())  # number of URLS required
        domain = self.domain_var.get()  # The current domain

        self.loaded_urls = db.weighted_sample_without_replacement_new(
            self.db_config, needed, domain)

       # Check if the URL loading preference is 'Most Recent'
        if self.url_loading_preference.get() == "Most Recent":
            # Process each URL in the loaded_urls list
            for i in range(len(self.loaded_urls)):
                # Assuming the URL is the second item in each tuple
                url = self.loaded_urls[i][1]
                # Substitute 'page=xxxxx' with 'page=1'
                new_url = re.sub(r'page=\d+', 'page=1', url)
                # Update the tuple with the new URL
                self.loaded_urls[i] = (self.loaded_urls[i][0], new_url)
        elif self.url_loading_preference.get() == "Random page":
            for i in range(len(self.loaded_urls)):
                url = self.loaded_urls[i][1]
                # Find the page number and replace it with a random number between 1 and the found page number

                def randomize_page(match):
                    page_num = int(match.group(1))
                    if page_num > 1:
                        return f"page={random.randint(1, page_num)}"
                    else:
                        # Return the original if page_num is 1 or less
                        return match.group(0)
                new_url = re.sub(r'page=(\d+)', randomize_page, url)
                self.loaded_urls[i] = (self.loaded_urls[i][0], new_url)

        # Update the display area with the selected URLs
        # Enable the widget for updating
        self.text_display_urls.config(state='normal')
        self.text_display_urls.delete('1.0', tk.END)
        # Sort by ID
        for _, url in sorted(self.loaded_urls, key=lambda x: x[0]):
            self.text_display_urls.insert(tk.END, url + '\n')
        self.text_display_urls.config(
            state='disabled')  # Make it read-only again

    def update_browser_dropdown(self) -> None:
        # Assuming this fetches a dict of browsers
        self.browsers = db.get_browsers(self.db_config)

    def on_browser_selected(self, event=None) -> None:  # Event is passed by bind
        # Update the selected browser based on user selection
        self.selected_browser = self.browser_var.get()
        logging.info(f"Selected browser: {self.selected_browser}")
        # Optionally, update VPN status or other elements here
        self.update_vpn_status_display()

    def connect_vpn(self) -> None:
        if self.selected_browser:  # Ensure a browser is selected
            try:
                # Attempt to connect to the VPN
                if not vpn.connect_vpn(self.selected_browser, self.browsers):
                    logging.critical("Failed to connect to VPN.")
                    messagebox.showerror(
                        "VPN Connection Failed", "Failed to establish a VPN connection. Please check your settings and try again.")
                    return  # Exit the function, but don't quit the application
                messagebox.showinfo(
                    "VPN Connection", "VPN successfully connected.")
                # Optionally, update the VPN status display after connecting
                self.update_vpn_status_display()
            except Exception as e:
                messagebox.showerror("VPN Connection Failed", str(e))
        else:
            messagebox.showwarning(
                "No Browser Selected", "Please select a browser before connecting to the VPN.")

    def disconnect_vpn(self) -> None:

        try:
        # Attempt to disconnect from the VPN
            if not vpn.disconnect_vpn():
                logging.critical("Failed to disconnect to VPN.")
                messagebox.showerror(
                    "VPN Disconnection Failed")
                return  # Exit the function, but don't quit the application
            messagebox.showinfo(
                "VPN Connection", "VPN successfully disconnected.")
            self.update_vpn_status_display()
        except Exception as e:
            messagebox.showerror("VPN Disconnection Failed", str(e))

    def execute_open_urls(self) -> None:
        """
        Fetch URLs from the database and open them using the selected browser.
        """
        if not hasattr(self, 'loaded_urls') or not self.loaded_urls:
            messagebox.showwarning(
                "No URLs Loaded", "Please load URLs before opening.")
            return

        selected_browser = self.selected_browser
        if not selected_browser:
            messagebox.showwarning(
                "No Browser Selected", "Please select a browser before opening URLs.")
            return

        logging.info("execute_open_urls: Fetching URLs...")

        # Use the stored list of URLs for opening
        try:
            threading.Thread(target=open_urls, args=(
                self, self.loaded_urls, selected_browser, self.db_config), daemon=True).start()
        except Exception as e:
            messagebox.showerror("Error Opening URLs", str(e))

    
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


    
    