import requests
from bs4 import BeautifulSoup
import re

url = "https://ouremirates.com/contact/"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

try:
    print(f"Fetching {url}...")
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    soup = BeautifulSoup(response.content, 'html.parser')
    text = soup.get_text(separator=' ')
    
    print("\n--- Extracted Text Preview (First 500 chars) ---")
    print(text[:500])
    
    # Try finding emails
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    print(f"\nEmails found: {list(set(emails))}")
    
    # Check for mailto
    mailto = [a['href'] for a in soup.find_all('a', href=True) if a['href'].startswith('mailto:')]
    print(f"Mailto links: {mailto}")

except Exception as e:
    print(f"Error: {e}")
