#db.py
import mysql.connector as mysql
import yaml
import numpy as np
import pandas as pd
from datetime import datetime
import logging

"""
Module containing functions to commuinicate with the database. Currently using mysql.connector

"""



def load_config(config_file='config.yml') -> dict:
    """
    Load configuration from a YAML file.

    Returns:
        dict: Configuration parameters, including database and GUI settings.
    """
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config  # Now returns the entire config, not just db_config

def get_browsers(db_config) -> list:
    """
    Fetch browser configurations from the database.

    Args:
        db_config (dict): Database configuration parameters.

    Returns:
        dict: Dictionary of browser configurations keyed by browser name.
    """
    browsers_dict = {}
    try:
        conn = mysql.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, vpn_code, command FROM browsers")
        for (id, name, vpn_code, command) in cursor:
            browsers_dict[name] = {"id": id, "vpn": vpn_code, "command": command}
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    return browsers_dict

def get_all_urls(db_config, domain=None) -> list:
    """
    Retrieve all URLs from the database, optionally filtered by domain.

    Args:
        db_config (dict): Database configuration parameters.
        domain (str, optional): Domain to filter URLs by. Defaults to None.

    Returns:
        list: List of URLs.
    """
    conn = mysql.connect(**db_config)
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

def insert_url(db_config, url, domain) -> None:
    """
    Insert a new URL into the database.

    Args:
        db_config (dict): Database configuration parameters.
        url (str): The URL to insert.
        domain (str): The domain associated with the URL.

    """
    try:
        conn = mysql.connect(**db_config)
        cursor = conn.cursor()
        query = "INSERT INTO urls (url, domain) VALUES (%s, %s) ON DUPLICATE KEY UPDATE url=url;"
        cursor.execute(query, (url, domain))
        conn.commit()
    except mysql.IntegrityError as e:
        logging.error(f"Integrity error inserting URL: {url}. Error: {e}")
        # Handle data integrity issues, e.g., rollback, notify user
    except mysql.ProgrammingError as e:
        logging.error(f"Programming error with query: {e}")
        # Handle programming errors, e.g., syntax error in the SQL query
    except mysql.Error as e:
        logging.error(f"General MySQL error: {e}")
        # Handle other MySQL errors
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def upload_urls_from_file(db_config, filename, domain) -> int:
    """
    Upload multiple URLs from a file to the database.

    Args:
        db_config (dict): Database configuration parameters.
        filename (str): Path to the file containing URLs.
        domain (str): The domain associated with URLs.

    Returns:
        int: The number of URLs uploaded.
    """
    count: int = 0
    with open(filename, 'r') as file:
        urls: list = [line.strip() for line in file if line.strip()]
        for url in urls:
            insert_url(db_config, url, domain)
            count += 1
    return count  # Return the number of URLs uploaded

def clear_all_urls(db_config) -> None:
    """
    Delete all URLs from the database.

    Args:
        db_config (dict): Database configuration parameters.
    """
    try:
        conn = mysql.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM urls")
        conn.commit()
        print("All URLs have been deleted.")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def get_domains(db_config) -> tuple:
   
    conn = mysql.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SELECT domain, default_domain FROM domains")
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

def insert_into_urls_opened(db_config, url_id) -> bool:
    """
    Insert a row into the urls_opened table.

    Args:
        db_config (dict): Database configuration parameters.
        url_id (int): the URL ID to be inserted.

    Returns:
        boolean: True if the insertion was successful, False if unsuccessful.
    """
    try:
        conn = mysql.connect(**db_config)
        cursor = conn.cursor()
        # Use placeholders for safe query construction
        query = "INSERT INTO urls_opened (url_id, time_opened) VALUES (%s, NOW());"
        cursor.execute(query, (url_id,))
        conn.commit()  # Commit the transaction to save changes
        return True
    except mysql.Error as e:
        logging.error(f"Error inserting URL into urls_opened: {e}")
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def weighted_sample_without_replacement(db_config, needed, domain) -> list:
    """
    Samples URLs from the database without replacement, according to their weights.

    Args:
        db_config (dict): Database configuration parameters.
        needed (int): Number of URLs needed.

    Returns:
        list: List of sampled URLs.
    """
    # Connect to the database and fetch URLs and weights
    try:
        conn = mysql.connect(**db_config)
        cursor = conn.cursor()
        query = "SELECT id, url, weight FROM urls"
        params = ()  # Initialize params as an empty tuple
        if domain:
            query += " WHERE domain = %s"
            params = (domain,)  # Add domain to params

        cursor.execute(query, params)
        urls_data = cursor.fetchall()
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

    if not urls_data:
        return []

    # Separate IDs, URLs, and weights
    ids, urls, weights = zip(*urls_data)
    
    # Convert weights to probabilities, ensuring they sum to 1
    total_weight = sum(weights)
    probabilities = [weight / total_weight for weight in weights]

    # Sample URLs based on their weights without replacement
    sampled_indices = np.random.choice(len(urls), size=needed, replace=False, p=probabilities)
    sampled_urls_with_ids = [(ids[i], urls[i]) for i in sampled_indices]

    return sampled_urls_with_ids

def weighted_sample_without_replacement_new(db_config, needed, domain) -> list:
    try:
        conn = mysql.connect(**db_config)
        cursor = conn.cursor()
        query = "SELECT id, url, weight FROM urls"
        params = ()
        if domain:
            query += " WHERE domain = %s"
            params = (domain,)
        query += " ORDER BY id"
        cursor.execute(query, params)
        urls_data = cursor.fetchall()
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

    if not urls_data:
        return []

    # Create DataFrame from the fetched data
    df = pd.DataFrame(urls_data, columns=['id', 'url', 'weight'])
    df_expanded = expand_df(df)
    random_rows = df_expanded.sample(n=needed, replace=False)

    # Return a list of tuples (id, url)
    return list(zip(random_rows['id'], random_rows['url']))

def expand_df(df):
    # Create an empty list to store each block of replicated rows
    replicated_blocks = []
    
    # Iterate over each row in the DataFrame
    for index, row in df.iterrows():
        replicated_block = pd.DataFrame({
            'id': [row['id']] * row['weight'],  # Replicate the id
            'url': [row['url']] * row['weight']  # Replicate the url
        })
        replicated_blocks.append(replicated_block)
    
    # Concatenate all replicated blocks to a single DataFrame
    expanded_df = pd.concat(replicated_blocks, ignore_index=True)
    return expanded_df

def insert_url_open_history(url_id, browser_id, db_config) -> None:
    """
    Inserts a record into the URL_open_history table.

    Args:
    url_id (int): The ID of the URL that was opened.
    browser_id (int): The ID of the browser used to open the URL.
    db_config (dict): A dictionary containing database connection parameters.
    """
    query = """
    INSERT INTO URL_open_history (URL_id, timestamp, browser_id)
    VALUES (%s, %s, %s)
    """
    timestamp = datetime.now()  # Current date and time

    try:
        # Establish a connection to the database
        conn = mysql.connect(**db_config)

        # Create a cursor object
        cursor = conn.cursor()

        # Execute the INSERT statement
        cursor.execute(query, (url_id, timestamp, browser_id))

        # Commit the transaction
        conn.commit()

        logging.info("URL open history record inserted successfully.")

    except mysql.Error as e:
        logging.error(f"Error while inserting into URL_open_history: {e}")

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def execute_query(db_config, query, params):
    """
    Execute a SQL query and return the results.

    :param db_config: Database configuration dictionary.
    :param query: SQL query string.
    :param params: Tuple of parameters to be used with the query.
    :return: List of tuples containing the query results.
    """
    try:
        # Use the alias 'mysql' directly as imported
        conn = mysql.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        results = cursor.fetchall()

        cursor.close()
        conn.close()

        return results
    except mysql.Error as error:  # Corrected exception handling using the alias
        print(f"Failed to execute query: {error}")
        return None