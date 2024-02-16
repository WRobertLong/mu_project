from nordvpn_connect import initialize_vpn, rotate_VPN, close_vpn_connection, get_current_ip
import sys
import subprocess
import re

def get_vpn_status():
    """
    Check the current VPN connection status by verifying running nordvpn status and capturing the result.

    Returns:
        The resuls of nordvpn status
    """

    # Run the nordvpn status command
    result = subprocess.run(["nordvpn", "status"], capture_output=True, text=True)
    output = result.stdout

    # Check if connected or disconnected
    if "Disconnected" in output:
        return {"status": "Disconnected"}
    elif "Connected" in output:
        # Parse the output for details
        details = {}
        details["status"] = "Connected"
        details["hostname"] = re.search("Hostname: (.*)", output).group(1)
        details["ip"] = re.search("IP: (.*)", output).group(1)
        details["country"] = re.search("Country: (.*)", output).group(1)
        details["city"] = re.search("City: (.*)", output).group(1)
        
        return details

def check_vpn_status():
    """
    Check the current VPN connection status by verifying the IP address.

    Returns:
        bool: True if the VPN is likely connected (IP not in the normal range), False otherwise.
    """

    try:
        current_ip = get_current_ip()
        if not current_ip.startswith("176.27"):
            print(f"VPN is very likely connected. Current IP: {current_ip}")
            return True
        else:
            print("VPN is not connected or Current IP is in the normal range.")
            return False
    except Exception as e:
        print(f"Error checking VPN status: {e}")
        return False

def connect_vpn(selected_browser,browsers):
    """
    Establish a VPN connection using the selected browser's VPN settings.

    Attempts to connect to the VPN server associated with the selected browser.
    Retries up to 5 times if the initial connection attempt fails.

    Args:
        selected_browser (str): The browser name as selected by the user.
        browsers()

    Exits:
        The program exits if the VPN connection fails after multiple attempts.
    """

    server_code = browsers[selected_browser]["vpn"]
    settings = initialize_vpn(server_code)
    rotate_VPN(settings)
    
    if check_vpn_status():
        print(f"Successfully connected to VPN server {server_code}.")
    else:
        print(f"Attempting to connect to VPN server {server_code}...")
        for _ in range(5):
            rotate_VPN(settings)
            if check_vpn_status():
                print(f"Successfully connected to VPN server {server_code}.")
                return
            print("Retrying...")
        print("Failed to connect to VPN after multiple attempts. Exiting.")
        close_vpn_connection(settings)
        sys.exit(1)