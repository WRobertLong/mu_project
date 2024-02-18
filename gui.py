# gui.py
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText  # For a scrollable read-only text box
import csv
from db import load_database_config, upload_urls_from_file, clear_all_urls, insert_url, get_all_urls, get_domains
from vpn_manager import get_vpn_status

class URLManagerGUI(tk.Tk):
    """
    A graphical user interface for managing URLs and domain data.
    Allows for the selection of files, uploading of URLs from a file,
    insertion of individual URLs, and exporting URLs to a CSV file.
    """
    def __init__(self):
        super().__init__()
        self.title("URL Manager")
        self.geometry("500x1100")

        self.db_config = load_database_config()
        domain_options, default_domain = get_domains(self.db_config)

        # Load domains from the database
        domain_options, default_domain = get_domains(self.db_config)

        # Setup the domain dropdown
        self.domain_var = tk.StringVar(self)
        self.domain_var.set(default_domain)  # Set default domain
        self.optionmenu_domain = tk.OptionMenu(self, self.domain_var, *domain_options)
        self.optionmenu_domain.pack(pady=(0, 10))

        # File Selection
        self.label_file = tk.Label(self, text="No file selected")
        self.label_file.pack()

        self.button_select_file = tk.Button(self, text="Select File", command=self.select_file)
        self.button_select_file.pack()

        # Bulk Insertion Button
        self.button_upload = tk.Button(self, text="Upload URLs", command=self.bulk_upload)
        self.button_upload.pack(pady=(10,0))

        # Additional URL Entry
        self.label_url = tk.Label(self, text="URL:")
        self.label_url.pack(pady=(10,0))

        self.entry_url = tk.Entry(self)
        self.entry_url.pack(pady=(0,10))
        
        # Upload Single URL Button
        self.button_upload_single = tk.Button(self, text="Upload Single URL", command=self.upload_single_url)
        self.button_upload_single.pack(pady=(10,0))

        # Clear URLs Button
        self.button_clear = tk.Button(self, text="Clear All URLs", command=self.clear_urls)
        self.button_clear.pack(pady=(10,0))

         # Filename Entry for export
        self.label_filename = tk.Label(self, text="Filename:")
        self.label_filename.pack(pady=(10, 0))

        self.entry_filename = tk.Entry(self)
        self.entry_filename.pack(pady=(0, 10))

        # Export to CSV Button
        self.button_export_csv = tk.Button(self, text="Export to CSV", command=self.export_to_csv)
        self.button_export_csv.pack(pady=(10, 0))

        self.selected_file = ''

        # Button for checking VPN status
        self.button_check_vpn = tk.Button(self, text="Check VPN Status", command=self.update_vpn_status_display)
        self.button_check_vpn.pack(pady=(10, 5))
        
        # Read-Only Text Box for displaying VPN status
        self.text_vpn_status = ScrolledText(self, wrap=tk.WORD, width=40, height=10, state='disabled')
        self.text_vpn_status.pack(pady=(5, 10))

        # Needed number of URLs Entry
        tk.Label(self, text="Needed number of URLs:").pack(pady=(10, 0))
        self.entry_needed_urls = tk.Entry(self)
        self.entry_needed_urls.pack(pady=(0, 10))

        # Display Selected URLs
        self.text_display_urls = ScrolledText(self, wrap=tk.WORD, width=50, height=15, state='disabled')
        self.text_display_urls.pack(pady=(10, 0))

        # Load URLs Button
        tk.Button(self, text="Load URLs", command=self.load_urls).pack(pady=(10, 0))

    def select_file(self):
        """
        Open a file dialog to select a file, and update the label to show the selected file's name.
        """
        self.selected_file = filedialog.askopenfilename(title="Select a file", filetypes=(("Text files", "*.txt"), ("All files", "*.*")))
        if self.selected_file:
            self.label_file.config(text=f"Selected File: {self.selected_file.split('/')[-1]}")

    def bulk_upload(self):
        """
        Upload multiple URLs from the selected file to the database, under the selected domain.
        """
        domain = self.domain_var.get()
        if self.selected_file and domain:
            count = upload_urls_from_file(self.db_config, self.selected_file, domain)
            messagebox.showinfo("Upload Complete", f"{count} URLs have been uploaded.")
        else:
            messagebox.showwarning("Missing Information", "Please select a file and enter a domain.")

    def upload_single_url(self):
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
            insert_url(self.db_config, url, domain)
            messagebox.showinfo("Success", "URL has been uploaded.")
            self.entry_url.delete(0, tk.END)  # Clear the URL entry after successful upload
        except Exception as e:
            messagebox.showerror("Error", f"Failed to upload URL: {e}")

    def clear_urls(self):
        """
        Clear all URLs from the database.
        """
        clear_all_urls(self.db_config)
        messagebox.showinfo("Clear URLs", "All URLs have been deleted from the database.")

    def export_to_csv(self):
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
        urls = get_all_urls(self.db_config, domain)

        # Write URLs to a CSV file
        try:
            with open(filename, 'w', newline='') as file:
                writer = csv.writer(file)
                for url in urls:
                    writer.writerow([url])
            messagebox.showinfo("Export Successful", f"URLs exported to {filename}.")
        except Exception as e:
            messagebox.showerror("Export Failed", f"An error occurred: {e}")

    def update_vpn_status_display(self):
        """
        Fetches and displays the formatted VPN status.
        """
        status_info = get_vpn_status()  # Fetches the VPN status as a dictionary
        # Format the dictionary into a readable string
        if isinstance(status_info, dict):
            formatted_status = "\n".join(f"{key}: {value}" for key, value in status_info.items())
        else:
            formatted_status = "Unable to fetch VPN status."
        self.text_vpn_status.config(state='normal')  # Enable the widget for updating
        self.text_vpn_status.delete('1.0', tk.END)  # Clear current content
        self.text_vpn_status.insert(tk.END, formatted_status)  # Insert the formatted status
        self.text_vpn_status.config(state='disabled')  # Make it read-only again
        
    def load_urls(self):
        """
        Function to load the URLs
        """
        urls = get_all_urls(self.db_config)
        self.text_display_urls.config(state='normal')  # Enable the widget for updating
        self.text_display_urls.delete('1.0', tk.END)  # Clear current content
        for url in urls:
            self.text_display_urls.insert(tk.END, url + '\n')  # Insert URLs

        self.text_display_urls.config(state='disabled')  # Make it read-only again



