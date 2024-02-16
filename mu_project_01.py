#!/usr/bin/env python3
"""
Main program for managing VPN connections and opening URLs.

This script allows the user to connect to a VPN using a selected browser,
processes a list of URLs based on given criteria, and opens those URLs.
It supports both command-line interface (CLI) and graphical user interface (GUI) modes.
"""

import subprocess
import sys
import os
import random
import time
import vpn_manager
from db import load_database_config,  get_browsers, get_all_urls

db_config = load_database_config()
browsers = get_browsers(db_config)
print("Current working directory:", os.getcwd())

def select_browser():
    """
    Present the user with a list of available browsers and allow them to select one.

    The browsers are fetched from the database configuration. The user is prompted
    to enter the number corresponding to their browser of choice.

    Returns:
        str: The key name of the selected browser from the available options.

    Exits:
        The program exits if the user makes an invalid selection.
    """

    print("Available browsers:")
    for i, browser in enumerate(browsers.keys(), start=1):
        print(f"{i}) {browser} - {browsers[browser]['vpn']}")
    
    choice = int(input("Enter the number of the browser you want to set as default: "))
    if 1 <= choice <= len(browsers):
        return list(browsers.keys())[choice - 1]
    else:
        print("Invalid selection.")
        sys.exit(1)

def process_urls(db_config, modify_line_multiple, output_line_multiple, starting_point=1):
    """
    Process a list of URLs from the database, applying modification and output conditions.

    Args:
        db_config (dict): Database configuration parameters.
        modify_line_multiple (int): Multiple for deciding which URLs to modify.
        output_line_multiple (int): Multiple for deciding which URLs to output.
        starting_point (int, optional): The starting index for processing URLs. Defaults to 1.

    Returns:
        list: A list of final URLs after processing based on the given criteria.
    """

    urls = get_all_urls(db_config)
    print(urls)

    final_urls = []
    for i, url in enumerate(urls, start=1):  # Always start from 1, not starting_point
        print(f"i: {i}, meets output condition: {(i - starting_point) % output_line_multiple == 0}, meets modify condition: {(i - starting_point) % modify_line_multiple == 0}")
        if (i >= starting_point) and ((i - starting_point) % output_line_multiple == 0):
            if ((i - starting_point) % modify_line_multiple) == 0:
                if not url.startswith('http://') and not url.startswith('https://'):
                    url = 'http://' + url
                url = url.replace('compage=', 'com?page=')
            final_urls.append(url)

    return final_urls

def open_urls(urls, selected_browser):
    """
    Open a list of URLs using the command associated with the selected browser.

    Each URL is opened in the browser, followed by a random sleep period.

    Args:
        urls (list): A list of URLs to be opened.
        selected_browser (str): The browser name as selected by the user.
    """
    
    browser_command = browsers[selected_browser]["command"]
    for url in urls:
        subprocess.Popen([browser_command, url])
        print(f"Opened URL: {url}")
        sleep_time = random.randint(30, 90)  # Adjust timing as needed (seconds)
        print(f"Sleeping for {sleep_time} secs")
        time.sleep(sleep_time)

if __name__ == "__main__":
    # Check if the user wants to launch the GUI

    from gui import URLManagerGUI

    if len(sys.argv) == 2 and sys.argv[1].lower() == "gui":
        app = URLManagerGUI()
        app.mainloop()
    # Proceed with the original CLI functionality if the correct number of arguments are provided
    elif len(sys.argv) == 4:
        filename = sys.argv[1]
        modify_line_multiple = int(sys.argv[2])
        output_line_multiple = int(sys.argv[3])

        selected_browser = select_browser()
        vpn_manager.connect_vpn(selected_browser, browsers)  # Use the selected browser's VPN settings

        print("Processing URLs...")
        final_urls = process_urls(db_config, modify_line_multiple, output_line_multiple)

        print("Opening URLs...")
        open_urls(final_urls, selected_browser)

        print("Script completed.")
    else:
        print("Usage for CLI mode: script.py <filename> <modify-line-multiple> <output-line-multiple>")
        print("To launch GUI mode: script.py gui")