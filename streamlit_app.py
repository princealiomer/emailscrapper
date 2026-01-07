import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import time

# --- Config & Utils ---

def clean_url(url):
    """Ensure URL has proper scheme"""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return url.rstrip('/')

def extract_emails(text):
    """
    Extract email addresses from text using robust regex.
    excludes common image extensions to avoid false positives.
    """
    if not text:
        return []
    # Regex from our Node.js implementation: word boundary + standard email pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    matches = re.findall(email_pattern, text)
    
    # Filter out image files that might look like emails
    valid_emails = [
        email.lower() for email in matches 
        if not email.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'))
    ]
    return list(set(valid_emails))

def extract_phones(text):
    """Extract phone numbers using multiple patterns."""
    if not text:
        return []
        
    phones = set()
    patterns = [
        r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # +1-234-567-8900
        r'\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b',  # 234-567-8900
        r'\b\d{10,}\b',  # 2345678900
    ]
    
    for pattern in patterns:
        found = re.findall(pattern, text)
        phones.update(found)
        
    # Validation: 10-15 digits
    valid_phones = []
    for phone in phones:
        digits = re.sub(r'\D', '', phone)
        if 10 <= len(digits) <= 15:
            valid_phones.append(phone.strip())
            
    return list(set(valid_phones))

def get_soup(url, session):
    """Helper to fetch page and return BeautifulSoup object"""
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        st.error(f"Error fetching {url}: {e}")
        return None

def find_contact_link(soup, base_url):
    """Finds the most likely contact page URL."""
    if not soup:
        return None
        
    keywords = ['contact', 'contact us', 'contact-us', 'get in touch', 'about us', 'about', 'reach', 'touch', 'support', 'help']
    
    for a in soup.find_all('a', href=True):
        href = a['href']
        text = a.get_text().lower().strip()
        
        # Check text match
        if any(k in text for k in keywords):
            return urljoin(base_url, href)
            
        # Check href match
        if any(k in href.lower() for k in keywords):
             return urljoin(base_url, href)
             
    return None

# --- Main App ---

st.set_page_config(page_title="Email & Phone Scraper", page_icon="🕵️", layout="wide")

st.title("🕵️ Email & Phone Scraper")
st.markdown("""
Enter a website URL below. The tool will:
1. Scan the **Home Page**.
2. Attempt to find and scan a **Contact Page**.
3. Extract **Emails** and **Phone Numbers**.
""")

url_input = st.text_input("Website URL", placeholder="example.com")

if st.button("Start Scraping", type="primary"):
    if not url_input:
        st.warning("Please enter a URL.")
    else:
        target_url = clean_url(url_input)
        
        # UI Containers
        status_container = st.container()
        results_container = st.container()
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        all_emails = set()
        all_phones = set()
        pages_scraped = []
        
        with st.status("Scraping in progress...", expanded=True) as status:
            # 1. Scrape Home
            st.write(f"Taking a look at: `{target_url}`")
            soup_home = get_soup(target_url, session)
            
            if soup_home:
                pages_scraped.append(target_url)
                text_home = soup_home.get_text(separator=' ')
                
                # Extract from text
                e_home = extract_emails(text_home)
                p_home = extract_phones(text_home)
                
                # Extract from mailto/tel links
                for a in soup_home.find_all('a', href=True):
                    href = a['href']
                    if href.startswith('mailto:'):
                        all_emails.add(href.replace('mailto:', '').split('?')[0])
                    if href.startswith('tel:'):
                        all_phones.add(href.replace('tel:', ''))

                all_emails.update(e_home)
                all_phones.update(p_home)
                
                # 2. Find Contact Page
                contact_url = find_contact_link(soup_home, target_url)
                
                if contact_url:
                    # Avoid duplicates
                    if contact_url not in pages_scraped and urlparse(contact_url).netloc == urlparse(target_url).netloc:
                        st.write(f"Found Contact link: `{contact_url}`. Navigating...")
                        soup_contact = get_soup(contact_url, session)
                        if soup_contact:
                            pages_scraped.append(contact_url)
                            text_contact = soup_contact.get_text(separator=' ')
                            
                            all_emails.update(extract_emails(text_contact))
                            all_phones.update(extract_phones(text_contact))
                else:
                    st.write("No obvious Contact page found.")
                    
            status.update(label="Scraping Complete!", state="complete", expanded=False)

        # Display Results
        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📧 Emails Found")
            if all_emails:
                for e in sorted(all_emails):
                    st.code(e, language="text")
            else:
                st.info("No emails found.")
                
        with col2:
            st.subheader("📞 Phones Found")
            if all_phones:
                for p in sorted(all_phones):
                    st.code(p, language="text")
            else:
                st.info("No phone numbers found.")

        with st.expander("Debug Details"):
            st.json({
                "pages_scraped": pages_scraped,
                "total_emails": len(all_emails),
                "total_phones": len(all_phones)
            })
