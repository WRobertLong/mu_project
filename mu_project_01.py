#!/usr/bin/env python3
"""
Main program for managing VPN connections and opening URLs.

This script allows the user to connect to a VPN using a selected browser,
processes a list of URLs based on given criteria, and opens those URLs.
"""

import subprocess
import sys
import os
import random
import time
import logging
import vpn_manager as vpn
import db

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', filename='mu_project.log')

db_config: dict = db.load_database_config()
browsers: dict = db.get_browsers(db_config)

def select_browser() -> None:
    """
    Present the user with a list of available browsers and allow them to select one.

    The browsers are fetched from the database configuration. The user is prompted
    to enter the number corresponding to their browser of choice.

    Returns:
        str: The key name of the selected browser from the available options.

    Exits:
        The program exits if the user makes an invalid selection.
    """
    
    choice = int(input("Enter the number of the browser you want to set as default: "))
    if 1 <= choice <= len(browsers):
        return list(browsers.keys())[choice - 1]
    else:
        print("Invalid selection.")
        sys.exit(1)

def open_urls(urls_with_ids, selected_browser, db_config) -> None:
    """
    Open a list of URLs using the command associated with the selected browser.

    Each URL is opened in the browser, followed by a random sleep period, in the order of their IDs.

    Args:
        urls_with_ids (list of tuples): A list of tuples (id, URL) to be opened.
        selected_browser (str): The browser name as selected by the user.
        db_config: Database configuration.
    """

    # Ensure the URLs are sorted by ID before opening
    urls_with_ids_sorted = sorted(urls_with_ids, key=lambda x: x[0])

    browser_command = browsers[selected_browser]["command"]

    for url_id, url in urls_with_ids_sorted:
        logging.info(f"About to launch {browser_command} with {url}")
        try:
            subprocess.Popen([browser_command, url])
            logging.info(f"Opened URL: {url} at {time.ctime()}")
            browser_id = browsers[selected_browser]["id"]
            # Assuming `db` is a module or an instance that has a method `insert_url_open_history`
            db.insert_url_open_history(url_id, browser_id, db_config)
        except Exception as e:
            logging.error(f"Failed to open URL: {url}. Error: {e}")
            continue
        
        sleep_time = random.randint(30, 90)
        logging.info(f"Sleeping for {sleep_time} seconds...")
        time.sleep(sleep_time)
        logging.info(f"Resuming at {time.ctime()}")

if __name__ == "__main__":
    # Check if the user wants to launch the GUI

    from gui import URLManagerGUI

    if len(sys.argv) == 2 and sys.argv[1].lower() == "gui":
        app = URLManagerGUI()
        app.mainloop()

