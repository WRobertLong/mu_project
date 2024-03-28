#!/usr/bin/env python3
"""
Main program for managing VPN connections and opening URLs.

"""

from __future__ import annotations
import subprocess
import sys
import random
import time
import logging
import db
import vpn_manager as vpn
from typing import List, Tuple, Union, Dict


def open_urls(app: 'URLManagerGUI', urls_with_ids: List[Tuple[Union[int, str], str]], selected_browser: str, db_config: Dict[str, Union[str, int, float, bool]]) -> None:
    # Use forward declaration for app type to avoid circular dependencies
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

    browsers = app.get_browsers()

    browser_command = browsers[selected_browser]["command"]

    sleep_min, sleep_max = app.get_sleep_params()

    for url_id, url in urls_with_ids_sorted:
        logging.info(f"About to launch {browser_command} with {url}")
        if vpn.is_vpn_connected:
            try:
                subprocess.Popen([browser_command, url])
                logging.info(f"Opened URL: {url} at {time.ctime()}")
                browser_id = browsers[selected_browser]["id"]
                db.insert_url_open_history(url_id, browser_id, db_config)
            except Exception as e:
                logging.error(f"Failed to open URL: {url}. Error: {e}")
        else:
            logging.error("VPN is not connected.")
            continue  
        
        sleep_time = random.randint(sleep_min, sleep_max)
        logging.info(f"Sleeping for {sleep_time} seconds...")
        time.sleep(sleep_time)
        logging.info(f"Resuming at {time.ctime()}")

if __name__ == "__main__":

    from gui import URLManagerGUI

    if len(sys.argv) == 2 and sys.argv[1].lower() == "gui":
        app = URLManagerGUI()
        app.mainloop()

