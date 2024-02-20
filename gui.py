# gui.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, PhotoImage
from tkinter.scrolledtext import ScrolledText
from mu_project_01 import open_urls
import csv
import db
import vpn_manager as vpn
import threading
import logging

class URLManagerGUI(tk.Tk):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.title("URL/VPN Management Console")
        self.geometry("1000x1100")
        icon = PhotoImage(file='/home/long/google-drive/Documents/Python_things/mu_project/TP_icon.png')
        self.iconphoto(True, icon)

        self.db_config = db.load_database_config()

        # Load browser configurations from the database
        self.browsers = db.get_browsers(self.db_config)

        # Initialize ttk styles
        self.style = ttk.Style(self)
        self.style.theme_use('default')

        # Select a default browser
        self.selected_browser = next(iter(self.browsers)) if self.browsers else None

        # Load domains from the database
        domain_options, default_domain = db.get_domains(self.db_config)

        # Setup the domain dropdown
        self.domain_var = tk.StringVar(self)
        self.domain_var.set(default_domain)
        self.optionmenu_domain = tk.OptionMenu(self, self.domain_var, *domain_options)
        self.optionmenu_domain.pack(pady=(0, 10))

        self.setup_file_selection()
        self.setup_url_entry()
        self.setup_export_to_csv()
        self.setup_vpn_controls()
        self.setup_url_loading()

        # Update the display to show the VPN status and the selected browser
        self.update_vpn_status_display()

    def setup_file_selection(self) -> None:
        # File Selection
        self.label_file = tk.Label(self, text="No file selected")
        self.label_file.pack()
        self.button_select_file = tk.Button(self, text="Select File", command=self.select_file)
        self.button_select_file.pack()
        self.button_upload = tk.Button(self, text="Upload URLs", command=self.bulk_upload)
        self.button_upload.pack(pady=(10, 0))

    def setup_url_entry(self) -> None:
        # Additional URL Entry
        self.label_url = tk.Label(self, text="URL:")
        self.label_url.pack(pady=(10, 0))
        self.entry_url = tk.Entry(self)
        self.entry_url.pack(pady=(0, 10))
        self.button_upload_single = tk.Button(self, text="Upload Single URL", command=self.upload_single_url)
        self.button_upload_single.pack(pady=(10, 0))
        self.button_clear = tk.Button(self, text="Clear All URLs", command=self.clear_urls)
        self.button_clear.pack(pady=(10, 0))

    def setup_export_to_csv(self)-> None:
        # Filename Entry for export
        self.label_filename = tk.Label(self, text="Filename:")
        self.label_filename.pack(pady=(10, 0))
        self.entry_filename = tk.Entry(self)
        self.entry_filename.pack(pady=(0, 10))
        self.button_export_csv = tk.Button(self, text="Export to CSV", command=self.export_to_csv)
        self.button_export_csv.pack(pady=(10, 0))

    def setup_vpn_controls(self)-> None:
        # VPN/Browser-related widgets in a frame
        vpn_frame = tk.Frame(self)
        vpn_frame.pack(pady=(10, 0))
        button_connect_vpn = tk.Button(vpn_frame, text="Connect VPN", command=self.connect_vpn)
        button_connect_vpn.pack(side=tk.LEFT, padx=(0, 10))
        button_check_vpn = tk.Button(vpn_frame, text="Check VPN Status", command=self.update_vpn_status_display)
        button_check_vpn.pack(side=tk.LEFT, padx=(0, 10))
        self.text_vpn_status = ScrolledText(self, wrap=tk.WORD, width=40, height=10, state='disabled')
        self.text_vpn_status.pack(pady=(5, 10))

        # Browser Selection Combobox
        self.browser_var = tk.StringVar(self)
        self.browsers_combo = ttk.Combobox(vpn_frame, textvariable=self.browser_var, values=list(self.browsers.keys()), state="readonly")
        self.browsers_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.browsers_combo.bind("<<ComboboxSelected>>", self.on_browser_selected)
        if self.browsers:
            self.browser_var.set(self.selected_browser)

    def setup_url_loading(self)-> None:
        # Frame for URL loading and browser selection
        url_frame = tk.Frame(self)
        url_frame.pack(pady=(10, 0))
        button_load_urls = tk.Button(url_frame, text="Load URLs", command=self.load_urls)
        button_load_urls.pack(side=tk.LEFT, padx=(0, 10))

        # Needed number of URLs Entry
        tk.Label(url_frame, text="Needed number of URLs:").pack(pady=(10, 0))
        self.entry_needed_urls = tk.Entry(url_frame)
        self.entry_needed_urls.pack(pady=(0, 10))

        # Add "Open URLs" Button
        button_open_urls = tk.Button(url_frame, text="Open URLs", command=self.execute_open_urls)
        button_open_urls.pack(side=tk.LEFT, padx=(10, 10))


        # Display area for URLs
        self.text_display_urls = ScrolledText(self, wrap=tk.WORD, width=100, height=15, state='disabled')
        self.text_display_urls.pack(pady=(10, 0))

    def select_file(self)-> None:
        """
        Open a file dialog to select a file, and update the label to show the selected file's name.
        """
        self.selected_file = filedialog.askopenfilename(title="Select a file", filetypes=(("Text files", "*.txt"), ("All files", "*.*")))
        if self.selected_file:
            self.label_file.config(text=f"Selected File: {self.selected_file.split('/')[-1]}")

    def bulk_upload(self)-> None:
        """
        Upload multiple URLs from the selected file to the database, under the selected domain.
        """
        domain = self.domain_var.get()
        if self.selected_file and domain:
            count = db.upload_urls_from_file(self.db_config, self.selected_file, domain)
            messagebox.showinfo("Upload Complete", f"{count} URLs have been uploaded.")
        else:
            messagebox.showwarning("Missing Information", "Please select a file and enter a domain.")

    def upload_single_url(self)-> None:
        """
        Upload a single URL, entered in the text entry field, to the database under the selected domain.
        """
        url = self.entry_url.get()
        domain = self.entry_domain.get()
        if not url:
            messagebox.showwarning("Missing Information", "Please enter a URL.")
            return
        # Assuming URL validation is desired; simplistic check:
        if not url.startswith('http://') and not url.startswith('https://'):
            messagebox.showwarning("Invalid URL", "URL must start with http:// or https://")
            return
        try:
            db.insert_url(self.db_config, url, domain)
            messagebox.showinfo("Success", "URL has been uploaded.")
            self.entry_url.delete(0, tk.END)  # Clear the URL entry after successful upload
        except Exception as e:
            messagebox.showerror("Error", f"Failed to upload URL: {e}")

    def clear_urls(self)-> None:
        """
        Clear all URLs from the database.
        """
        db.clear_all_urls(self.db_config)
        messagebox.showinfo("Clear URLs", "All URLs have been deleted from the database.")

    def export_to_csv(self)-> None:
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
            messagebox.showinfo("Export Successful", f"URLs exported to {filename}.")
        except Exception as e:
            messagebox.showerror("Export Failed", f"An error occurred: {e}")

    def update_vpn_status_display(self)-> None:
        """
        Fetches and displays the formatted VPN status along with the current default browser.
        """
        status_info = vpn.get_vpn_status()  # Fetches the VPN status as a dictionary
    
        # Correctly reference the browser's name using self.selected_browser
        browser_info = f"Default Browser: {self.selected_browser}" if self.selected_browser else "No Browser Selected"

        if isinstance(status_info, dict):
            formatted_status = "\n".join(f"{key}: {value}" for key, value in status_info.items())
        else:
            formatted_status = "Unable to fetch VPN status."
    
        combined_status = f"{formatted_status}\n\n{browser_info}"

        self.text_vpn_status.config(state='normal')
        self.text_vpn_status.delete('1.0', tk.END)
        self.text_vpn_status.insert(tk.END, combined_status)
        self.text_vpn_status.config(state='disabled')
        
    def load_urls(self)-> None:
        """
        Function to load the URLs based on weighted sampling without replacement.
        """
        needed = int(self.entry_needed_urls.get())  #number of URLS required
        domain = self.domain_var.get() # The current domain

        #urls = db.weighted_sample_without_replacement(self.db_config, needed, domain)
        self.loaded_urls = db.weighted_sample_without_replacement(self.db_config, needed, domain)

        # Update the display area with the selected URLs
        self.text_display_urls.config(state='normal')  # Enable the widget for updating
        self.text_display_urls.delete('1.0', tk.END)  
        for _, url in self.loaded_urls:    # Only display the URL part
            self.text_display_urls.insert(tk.END, url + '\n')
        self.text_display_urls.config(state='disabled')  # Make it read-only again

    def load_urls_old(self)-> None:
        """
        Function to load the URLs based on weighted sampling without replacement.
        """
        needed = int(self.entry_needed_urls.get())  #number of URLS required
        domain = self.domain_var.get() # The current domain

        #urls = db.weighted_sample_without_replacement(self.db_config, needed, domain)
        self.loaded_urls = db.weighted_sample_without_replacement(self.db_config, needed, domain)

        # Update the display area with the selected URLs
        self.text_display_urls.config(state='normal')  # Enable the widget for updating
        self.text_display_urls.delete('1.0', tk.END)  
        for url in self.loaded_urls:
            self.text_display_urls.insert(tk.END, url + '\n')
        self.text_display_urls.config(state='disabled')  # Make it read-only again

    def update_browser_dropdown(self)-> None:
        self.browsers = db.get_browsers(self.db_config)  # Assuming this fetches a dict of browsers

    def on_browser_selected(self, event=None)-> None:  # Event is passed by bind
        # Update the selected browser based on user selection
        self.selected_browser = self.browser_var.get()
        logging.info(f"Selected browser: {self.selected_browser}")
        # Optionally, update VPN status or other elements here
        self.update_vpn_status_display()

    def connect_vpn(self)-> None:
        # This method will be called when the "Connect VPN" button is clicked
        if self.selected_browser:  # Ensure a browser is selected
            try:
                # Assuming connect_vpn function requires the selected browser's name
                # and the browsers dictionary as arguments
                vpn.connect_vpn(self.selected_browser, self.browsers)
                messagebox.showinfo("VPN Connection", "VPN successfully connected.")
                # Optionally, update the VPN status display after connecting
                self.update_vpn_status_display()
            except Exception as e:
                messagebox.showerror("VPN Connection Failed", str(e))
        else:
            messagebox.showwarning("No Browser Selected", "Please select a browser before connecting to the VPN.")

    def execute_open_urls(self) -> None:
        """
        Fetch URLs from the database and open them using the selected browser.
        """
        if not hasattr(self, 'loaded_urls') or not self.loaded_urls:
            messagebox.showwarning("No URLs Loaded", "Please load URLs before opening.")
            return

        selected_browser = self.selected_browser
        if not selected_browser:
            messagebox.showwarning("No Browser Selected", "Please select a browser before opening URLs.")
            return

        logging.info("execute_open_urls: Fetching URLs...")  
        #urls = db.get_all_urls(self.db_config)  # Assuming this is how you get all URLs

        # Use the stored list of URLs for opening
        try:
            threading.Thread(target=open_urls, args=(self.loaded_urls, selected_browser, self.db_config), daemon=True).start()
        except Exception as e:
            messagebox.showerror("Error Opening URLs", str(e))
    