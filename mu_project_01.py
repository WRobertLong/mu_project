#!/usr/bin/env python3
"""
Main program for managing VPN connections and opening URLs.

"""
import sys
from typing import List, Tuple, Union, Dict

if __name__ == "__main__":

    from gui import URLManagerGUI

    if len(sys.argv) == 2 and sys.argv[1].lower() == "gui":
        app = URLManagerGUI()
        app.mainloop()

