#!/usr/bin/env python3
"""
Main program for managing VPN connections and opening URLs.

"""
import sys
from typing import List, Tuple, Union, Dict

if __name__ == "__main__":

    print("Script path:", sys.argv[0])
    print("Arguments:", sys.argv[1:])

    from gui import URLManagerGUI

    if len(sys.argv) == 2 and sys.argv[1].lower() == "gui":
        print("Running GUI mode")
        app = URLManagerGUI()
        print("hello")
        app.mainloop()
    else:
        print("Running non-GUI mode")
        print("hello world")
        app = URLManagerGUI()
        app.mainloop()
