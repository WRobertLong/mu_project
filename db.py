#db.py
import mysql.connector
import yaml

def load_database_config(config_file='config.yml'):
    """
    Load database configuration from a YAML file.

    Args:
        config_file (str): Path to the configuration file.

    Returns:
        dict: Database configuration parameters.
    """
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config['db_config']

def get_browsers(db_config):
    """
    Fetch browser configurations from the database.

    Args:
        db_config (dict): Database configuration parameters.

    Returns:
        dict: Dictionary of browser configurations keyed by browser name.
    """
    browsers_dict = {}
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT name, vpn_code, command FROM browsers")
        for (name, vpn_code, command) in cursor:
            browsers_dict[name] = {"vpn": vpn_code, "command": command}
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    return browsers_dict

def get_all_urls(db_config, domain=None):
    """
    Retrieve all URLs from the database, optionally filtered by domain.

    Args:
        db_config (dict): Database configuration parameters.
        domain (str, optional): Domain to filter URLs by. Defaults to None.

    Returns:
        list: List of URLs.
    """
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    query = "SELECT url FROM urls"
    params = ()
    if domain:
        query += " WHERE domain = %s"
        params = (domain,)
    cursor.execute(query, params)
    urls = [item[0] for item in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    return urls

def insert_url(db_config, url, domain):
    """
    Insert a new URL into the database.

    Args:
        db_config (dict): Database configuration parameters.
        url (str): The URL to insert.
        domain (str): The domain associated with the URL.

    """
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        query = "INSERT INTO urls (url, domain) VALUES (%s, %s) ON DUPLICATE KEY UPDATE url=url;"
        cursor.execute(query, (url, domain))
        conn.commit()
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def upload_urls_from_file(db_config, filename, domain):
    """
    Upload multiple URLs from a file to the database.

    Args:
        db_config (dict): Database configuration parameters.
        filename (str): Path to the file containing URLs.
        domain (str): The domain associated with URLs.

    Returns:
        int: The number of URLs uploaded.
    """
    count = 0
    with open(filename, 'r') as file:
        urls = [line.strip() for line in file if line.strip()]
        for url in urls:
            insert_url(db_config, url, domain)
            count += 1
    return count  # Return the number of URLs uploaded

def clear_all_urls(db_config):
    """
    Delete all URLs from the database.

    Args:
        db_config (dict): Database configuration parameters.
    """
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM urls")
        conn.commit()
        print("All URLs have been deleted.")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def get_domains(db_config):
    """
    Retrieve all domains from the database, identifying the default one.

    Args:
        db_config (dict): Database configuration parameters.

    Returns:
        tuple: A tuple containing a list of domains and the default domain.
    """
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SELECT domain, `default` FROM domains")
    domains = cursor.fetchall()
    
    default_domain = None
    domain_list = []
    for domain, is_default in domains:
        domain_list.append(domain)
        if is_default:
            default_domain = domain
            
    cursor.close()
    conn.close()
    
    return domain_list, default_domain