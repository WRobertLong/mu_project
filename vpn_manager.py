# vpn.py
#from nordvpn_connect import initialize_vpn, rotate_VPN, close_vpn_connection, get_current_ip
import  nordvpn_connect
from tkinter import messagebox
import sys
import subprocess
import re
import logging

def query_vpn() -> str:
    """
    Run the nordvpn status command and return the result
    """
    try:
        result = subprocess.run(["nordvpn", "status"], capture_output=True, text=True)
        logging.info("Successfully retrieved VPN status.")
        return result.stdout
    except Exception as e:
        logging.error(f"Error running nordvpn status command: {e}")
        return ""

def is_vpn_connected() -> bool:
    """
    Check if the VPN is connected by looking for 'Connected' in the nordvpn status output
    """
    vpn_status = query_vpn()
    if "Connected" in vpn_status:
        logging.info("VPN is very likely connected.")
        return True
    else:
        logging.info("VPN is not connected.")
        return False
        

def get_vpn_status() -> dict :
    """
    Check the current VPN connection status by verifying running nordvpn status and capturing the result.

    Returns:
        The resuls of nordvpn status
    """

    # Run the nordvpn status command
    #result = subprocess.run(["nordvpn", "status"], capture_output=True, text=True)
    #output = result.stdout
    vpn_output = query_vpn()

    # Check if connected or disconnected
    if "Disconnected" in vpn_output:
        return {"status": "Disconnected"}
    elif "Connected" in vpn_output:
        # Parse the output for details
        details = {}
        details["status"] = "Connected"
        details["hostname"] = re.search("Hostname: (.*)", vpn_output).group(1)
        details["ip"] = re.search("IP: (.*)", vpn_output).group(1)
        details["country"] = re.search("Country: (.*)", vpn_output).group(1)
        details["city"] = re.search("City: (.*)", vpn_output).group(1)
        
        return details

def check_vpn_status() -> bool :   # We don't actually need this func
    """
    Check the current VPN connection status. Originally used IP address range,
    but this was not reliable. So now simply parsing the output from "vpn status"
    in  is_vpn_connected()

    Returns:
        bool: True if the VPN is likely connected (IP not in the normal range), False otherwise.
    """
    return is_vpn_connected()
    #try:
    #    current_ip = get_current_ip()
    #    if not current_ip.startswith("176.27"):
    #        logging.info("VPN is very likely connected. Current IP: {current_ip}")
    #        return True
    #    else:
    #        logging.info("VPN is not connected or Current IP is in the normal range.")
    #        return False
    # except Exception as e:
    #    logging.error(f"Error checking VPN status: {e}")
    #    return False

def connect_vpn(selected_browser, browsers) -> bool:
    """
    Establish a VPN connection using the selected browser's VPN settings.

    Args:
        selected_browser (str): The browser name as selected by the user.
        browsers (dict): Dictionary containing browser configuration, including VPN settings.

    Returns:
        bool: True if the VPN connection was successfully established, False otherwise.
    """
    server_code = browsers[selected_browser]["vpn"]
    settings = initialize_vpn(server_code)

    # Attempt to connect to the VPN with retry logic
    if not attempt_vpn_rotation(settings):
        logging.error(f"Failed to connect to VPN server {server_code} after retries.")
        close_vpn_connection(settings)  # Ensure to close any partially established connections
        return False
    else:
        return True
    

def disconnect_vpn() -> bool:
    """
    Disconnect from the VPN

    Returns:
        bool: True if the VPN disconnection was successfully established, False otherwise.
    """

    # Define the parameters dictionary, including the required 'platform' key
    parameters = {
        "platform": "linux",  # Adjust according to your operating system (e.g., "windows" or "macos")
        # Include other required parameters if applicable
    }

    try:
        # Attempt to close the VPN connection
        result = nordvpn_connect.close_vpn_connection(parameters)

        if result is None:
            messagebox.showinfo("VPN Connection", "VPN successfully disconnected.")
        else:
            messagebox.showerror("VPN Disconnection Failed", "Unexpected output during disconnection.")
        
        # Optionally, update the VPN status display or application state
            #self.update_vpn_status_display()

    except KeyError as e:
        logging.error("Missing key in parameters during VPN disconnection", exc_info=e)
        messagebox.showerror("VPN Disconnection Error", f"Missing key in parameters: {e}")

    except Exception as e:
        logging.critical("Unexpected error during VPN disconnection", exc_info=e)
        messagebox.showerror("VPN Disconnection Failed", f"An unexpected error occurred: {str(e)}")


def attempt_vpn_rotation(settings, retries=5) -> bool:
    """
    Attempts to rotate the VPN connection with retry logic.

    Args:
        settings: The VPN settings to use for the connection.
        retries (int): Number of times to retry the connection attempt.

    Returns:
        bool: True if the VPN connection was successfully established, False otherwise.
    """
    print(f"Settings are {settings}")
    for attempt in range(retries + 1):  # Include initial attempt + retries
        try:
            print(f"About to rotate VPN with {settings} parameter")
            rotate_VPN(settings)
            if check_vpn_status():
                print("connected to VPN \n")
                if attempt > 0:
                    print(f"Successfully connected to VPN after {attempt} retries.")
                else:
                    print("Successfully connected to VPN. Whoa !")
                return True
            else:
                print("Not connected to vpn \n")
        except Exception as e:
            print(f"Error rotating VPN on attempt {attempt}: {e}")
        if attempt < retries:
            print("Retrying...")
        else:
            print("Failed to connect to VPN after multiple attempts.")
    return False