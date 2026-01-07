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
    
    with open("debug_ouremirates.html", "w", encoding="utf-8") as f:
        f.write(response.text)
        
    print("Saved HTML to debug_ouremirates.html")

except Exception as e:
    print(f"Error: {e}")
