# gui.py
import tkinter as tk
from tkinter import filedialog, messagebox
import csv
from db import load_database_config, upload_urls_from_file, clear_all_urls, insert_url, get_all_urls, get_domains

class URLManagerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("URL Manager")
        self.geometry("500x600")

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

    def select_file(self):
        self.selected_file = filedialog.askopenfilename(title="Select a file", filetypes=(("Text files", "*.txt"), ("All files", "*.*")))
        if self.selected_file:
            self.label_file.config(text=f"Selected File: {self.selected_file.split('/')[-1]}")

    def bulk_upload(self):
        domain = self.entry_domain.get()
        if self.selected_file and domain:
            count = upload_urls_from_file(self.db_config, self.selected_file, domain)
            messagebox.showinfo("Upload Complete", f"{count} URLs have been uploaded.")
        else:
            messagebox.showwarning("Missing Information", "Please select a file and enter a domain.")

    def upload_single_url(self):
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
        clear_all_urls(self.db_config)
        messagebox.showinfo("Clear URLs", "All URLs have been deleted from the database.")

    def export_to_csv(self):
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
