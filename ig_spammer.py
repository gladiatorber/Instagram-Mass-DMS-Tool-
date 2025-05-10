import os
import random
import time
from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired, ChallengeRequired, 
    ClientError, ClientConnectionError
)
import requests
from bs4 import BeautifulSoup

# Configuration
ACCOUNTS_FILE = "accounts.txt"
MESSAGE_FILE = "message.txt"
TARGETS_FILE = "targets.txt"
PROXY_FILE = "proxies.txt"
SLEEP_BETWEEN_ACCOUNTS = 60  # seconds
MAX_ATTEMPTS = 3

def scrape_proxies():
    """Scrape proxies from free proxy websites"""
    print("Scraping proxies...")
    proxy_urls = [
        "https://www.sslproxies.org/",
        "https://free-proxy-list.net/",
        "https://hidemy.name/en/proxy-list/"
    ]
    
    proxies = []
    
    for url in proxy_urls:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Parse proxy list (adjust selectors based on website)
            table = soup.find('table')
            if table:
                rows = table.find_all('tr')[1:11]  # Get first 10 proxies
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        ip = cols[0].text.strip()
                        port = cols[1].text.strip()
                        proxies.append(f"{ip}:{port}")
        except Exception as e:
            print(f"Error scraping proxies from {url}: {e}")
    
    # Save proxies to file
    with open(PROXY_FILE, 'w') as f:
        f.write('\n'.join(proxies))
    
    return proxies

def load_proxies():
    """Load proxies from file or scrape new ones if file doesn't exist"""
    if os.path.exists(PROXY_FILE):
        with open(PROXY_FILE, 'r') as f:
            proxies = [line.strip() for line in f.readlines() if line.strip()]
    else:
        proxies = scrape_proxies()
    return proxies

def load_accounts():
    """Load Instagram accounts from file"""
    if not os.path.exists(ACCOUNTS_FILE):
        raise FileNotFoundError(f"{ACCOUNTS_FILE} not found")
    
    with open(ACCOUNTS_FILE, 'r') as f:
        accounts = [line.strip().split(':') for line in f.readlines() if line.strip()]
    return accounts

def load_message():
    """Load message from file"""
    if not os.path.exists(MESSAGE_FILE):
        raise FileNotFoundError(f"{MESSAGE_FILE} not found")
    
    with open(MESSAGE_FILE, 'r') as f:
        message = f.read().strip()
    return message

def load_targets():
    """Load target users from file"""
    if not os.path.exists(TARGETS_FILE):
        raise FileNotFoundError(f"{TARGETS_FILE} not found")
    
    with open(TARGETS_FILE, 'r') as f:
        targets = [line.strip() for line in f.readlines() if line.strip()]
    return targets

def init_client(username, password, proxy=None):
    """Initialize Instagram client with optional proxy"""
    client = Client()
    
    # Set proxy if provided
    if proxy:
        client.set_proxy(proxy)
    
    # Try to load session if exists
    session_file = f"{username}.json"
    try:
        if os.path.exists(session_file):
            client.load_settings(session_file)
        client.login(username, password)
        return client
    except (LoginRequired, ChallengeRequired) as e:
        print(f"Login failed for {username}: {e}")
        # Try to relogin
        try:
            client.relogin()
            return client
        except Exception as e:
            print(f"Relogin failed for {username}: {e}")
            return None
    except Exception as e:
        print(f"Error initializing client for {username}: {e}")
        return None

def send_message(client, target_username, message):
    """Send message to target user"""
    try:
        user_id = client.user_id_from_username(target_username)
        client.direct_send(message, user_ids=[user_id])
        print(f"Message sent to {target_username}")
        return True
    except Exception as e:
        print(f"Failed to send message to {target_username}: {e}")
        return False

def main():
    # Load data
    accounts = load_accounts()
    message = load_message()
    targets = load_targets()
    proxies = load_proxies()
    
    if not accounts:
        print("No accounts found")
        return
    
    if not targets:
        print("No targets found")
        return
    
    if not message:
        print("No message found")
        return
    
    # Process each account
    for i, (username, password) in enumerate(accounts):
        print(f"\nProcessing account {i+1}/{len(accounts)}: {username}")
        
        # Select proxy (if available)
        proxy = None
        if proxies:
            proxy = f"http://{random.choice(proxies)}"
            print(f"Using proxy: {proxy}")
        
        # Initialize client
        client = init_client(username, password, proxy)
        if not client:
            print(f"Failed to initialize client for {username}")
            continue
        
        # Process targets
        successful_sends = 0
        for target in targets:
            attempts = 0
            while attempts < MAX_ATTEMPTS:
                if send_message(client, target, message):
                    successful_sends += 1
                    break
                attempts += 1
                time.sleep(5)  # Wait before retry
        
        # Save session
        client.dump_settings(f"{username}.json")
        
        print(f"Account {username} sent {successful_sends}/{len(targets)} messages successfully")
        
        # Sleep between accounts if not last account
        if i < len(accounts) - 1:
            print(f"Waiting {SLEEP_BETWEEN_ACCOUNTS} seconds before next account...")
            time.sleep(SLEEP_BETWEEN_ACCOUNTS)

if __name__ == "__main__":
    main()