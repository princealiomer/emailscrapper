import streamlit as st
from playwright.sync_api import sync_playwright
import re
import time
import os
import subprocess
import sys

# Page Config
st.set_page_config(
    page_title="Email & Phone Scraper",
    page_icon="🕵️‍♂️",
    layout="wide"
)

# --- Helper: Install Playwright Browsers on First Run (Streamlit Cloud) ---
def install_playwright():
    # Check if a marker file exists or specific check
    # A simple way is to try launching, if fail, install
    # But running install every time is safe-ish if cached, though slow.
    # Better: explicit check.
    try:
        # Try a quick dry-run or check folder. 
        # For simplicity in Streamlit Cloud, we just run the install command.
        # It handles existing installs gracefully (quick exit).
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    except Exception as e:
        st.error(f"Failed to install Playwright browsers: {e}")

# Call install at startup (once per session/run roughly)
if "playwright_installed" not in st.session_state:
    with st.spinner("Setting up browser engine..."):
        install_playwright()
    st.session_state.playwright_installed = True


# --- Logic ---

def clean_url(url):
    if not url.startswith("http"):
        return "https://" + url
    return url

def extract_emails(text):
    # Robust regex for emails
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = set(re.findall(email_pattern, text))
    # Filter out common false positives (image extensions, etc)
    valid_emails = {e for e in emails if not e.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'))}
    return list(valid_emails)

def extract_phones(text):
    # Robust regex for phone numbers
    phone_pattern = r'''(?:(?:\+?1\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?'''
    
    matches = re.findall(phone_pattern, text)
    valid_phones = []
    
    for match in matches:
        full_num = "".join(match).strip()
        if len(full_num) >= 10:
             # Basic formatting
             valid_phones.append(full_num)
             
    # Also look for international formats like +971...
    intl_pattern = r'\+\d{1,4}\s?\(?\d{1,4}\)?\s?\d{1,4}\s?\d{1,4}\s?\d{1,9}'
    intl_matches = re.findall(intl_pattern, text)
    valid_phones.extend(intl_matches)

    return list(set(valid_phones))


def auto_scroll(page):
    """Scrolls to bottom of page to trigger lazy loading"""
    page.evaluate("""
        async () => {
            await new Promise((resolve) => {
                var totalHeight = 0;
                var distance = 100;
                var timer = setInterval(() => {
                    var scrollHeight = document.body.scrollHeight;
                    window.scrollBy(0, distance);
                    totalHeight += distance;

                    if(totalHeight >= scrollHeight - window.innerHeight){
                        clearInterval(timer);
                        resolve();
                    }
                }, 100);
            });
        }
    """)
    # Wait a moment after scrolling
    time.sleep(2)

def scrape_with_playwright(start_url):
    results = {
        "home_emails": [],
        "home_phones": [],
        "contact_emails": [],
        "contact_phones": [],
        "contact_url": None,
        "errors": []
    }
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Context with user agent to avoid basic blocking
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = context.new_page()
        
        # 1. Scrape Home Page
        try:
            st.info(f"Scanning Home Page: {start_url}")
            page.goto(start_url, timeout=30000, wait_until="domcontentloaded")
            auto_scroll(page)
            
            content = page.inner_text("body")
            html_content = page.content() # for mailto/tel links if needed
            
            results["home_emails"] = extract_emails(content)
            
            # Also searching mailto links specifically
            mailto_emails = page.evaluate("""() => {
                const links = Array.from(document.querySelectorAll('a[href^="mailto:"]'));
                return links.map(a => a.href.replace('mailto:', '').split('?')[0]);
            }""")
            if mailto_emails:
                results["home_emails"].extend(mailto_emails)
            results["home_emails"] = list(set(results["home_emails"]))
            
            results["home_phones"] = extract_phones(content)

        except Exception as e:
            results["errors"].append(f"Home Page Error: {str(e)}")
            return results # Stop if home page fails hard

        # 2. Find Contact Page
        try:
            # Simple heuristic: Look for a link with "contact" text
            # We can use Playwright selector for this
            contact_element = page.query_selector('a:has-text("Contact"), a:has-text("contact"), a[href*="contact"]')
            
            if contact_element:
                contact_href = contact_element.get_attribute("href")
                # Resolve relative URL
                from urllib.parse import urljoin
                contact_url = urljoin(start_url, contact_href)
                results["contact_url"] = contact_url
                
                st.info(f"Found Contact Page: {contact_url}. Scanning...")
                
                page.goto(contact_url, timeout=30000, wait_until="domcontentloaded")
                auto_scroll(page)
                
                contact_content = page.inner_text("body")
                
                results["contact_emails"] = extract_emails(contact_content)
                
                contact_mailto = page.evaluate("""() => {
                    const links = Array.from(document.querySelectorAll('a[href^="mailto:"]'));
                    return links.map(a => a.href.replace('mailto:', '').split('?')[0]);
                }""")
                if contact_mailto:
                    results["contact_emails"].extend(contact_mailto)
                results["contact_emails"] = list(set(results["contact_emails"]))

                results["contact_phones"] = extract_phones(contact_content)
            else:
                st.warning("No 'Contact' link found on home page. Skipping contact page scan.")

        except Exception as e:
            results["errors"].append(f"Contact Page Error: {str(e)}")

        browser.close()
        
    return results


# --- GUI ---

st.title("🕵️‍♂️ Email & Phone Scraper")
st.markdown("Extract emails and phone numbers from websites. Supports **Single URL** or **Bulk Upload**.")

tab1, tab2 = st.tabs(["Single URL", "Bulk Upload 📂"])

# --- TAB 1: Single URL ---
with tab1:
    url_input = st.text_input("Website URL", placeholder="example.com")

    if st.button("Start Scraping", type="primary", key="single_scrape"):
        if not url_input:
            st.error("Please enter a URL.")
        else:
            target_url = clean_url(url_input)
            
            with st.status("Scraping in progress...", expanded=True) as status:
                data = scrape_with_playwright(target_url)
                status.update(label="Scraping Complete!", state="complete", expanded=False)
            
            # Display Results
            if data["errors"]:
                for err in data["errors"]:
                    st.error(err)
            
            # Combine Findings
            all_emails = list(set(data["home_emails"] + data["contact_emails"]))
            all_phones = list(set(data["home_phones"] + data["contact_phones"]))
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📧 Emails Found")
                if all_emails:
                    for email in all_emails:
                        st.code(email, language="text")
                else:
                    st.info("No emails found.")
                    
            with col2:
                st.subheader("📞 Phones Found")
                if all_phones:
                    for phone in all_phones:
                        st.code(phone, language="text")
                else:
                    st.info("No phone numbers found.")

            # Debug Info
            with st.expander("Debug Details"):
                st.json(data)

# --- TAB 2: Bulk Upload ---
with tab2:
    st.write("Upload a list of websites to scrape.")
    uploaded_file = st.file_uploader("Upload CSV, Excel, or Text file", type=["csv", "xlsx", "txt"])
    
    if uploaded_file:
        urls = []
        try:
            if uploaded_file.name.endswith('.csv'):
                df_input = pd.read_csv(uploaded_file)
                # Try to find a column that looks like 'url' or 'website'
                possible_cols = [c for c in df_input.columns if 'url' in c.lower() or 'website' in c.lower()]
                target_col = possible_cols[0] if possible_cols else df_input.columns[0]
                urls = df_input[target_col].dropna().astype(str).tolist()
                
            elif uploaded_file.name.endswith('.xlsx'):
                df_input = pd.read_excel(uploaded_file)
                possible_cols = [c for c in df_input.columns if 'url' in c.lower() or 'website' in c.lower()]
                target_col = possible_cols[0] if possible_cols else df_input.columns[0]
                urls = df_input[target_col].dropna().astype(str).tolist()
                
            elif uploaded_file.name.endswith('.txt'):
                stringio = str(uploaded_file.read(), "utf-8")
                urls = [line.strip() for line in stringio.splitlines() if line.strip()]
        except Exception as e:
            st.error(f"Error reading file: {e}")

        if urls:
            st.success(f"Found {len(urls)} URLs.")
            st.write(f"Preview: {urls[:3]}...")
            
            if st.button("Start Bulk Scraping", type="primary", key="bulk_scrape"):
                results_list = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, url in enumerate(urls):
                    status_text.text(f"Scraping {i+1}/{len(urls)}: {url}")
                    target_url = clean_url(url)
                    
                    try:
                        data = scrape_with_playwright(target_url)
                        
                        all_emails = list(set(data["home_emails"] + data["contact_emails"]))
                        all_phones = list(set(data["home_phones"] + data["contact_phones"]))
                        
                        results_list.append({
                            "Input URL": url,
                            "Scraped URL": target_url,
                            "Emails": ", ".join(all_emails),
                            "Phones": ", ".join(all_phones),
                            "Contact Page Found": data["contact_url"] if data["contact_url"] else "No",
                            "Errors": "; ".join(data["errors"]) if data["errors"] else "None"
                        })
                    except Exception as e:
                        results_list.append({
                            "Input URL": url,
                            "Scraped URL": target_url,
                            "Emails": "",
                            "Phones": "",
                            "Contact Page Found": "Error",
                            "Errors": str(e)
                        })
                    
                    progress_bar.progress((i + 1) / len(urls))
                
                status_text.text("Bulk scraping complete!")
                
                # Create DataFrame
                df_results = pd.DataFrame(results_list)
                
                # Show Table
                st.subheader("Results")
                st.dataframe(df_results)
                
                # CSV Download
                csv = df_results.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Results as CSV",
                    data=csv,
                    file_name="scraped_results.csv",
                    mime="text/csv",
                )
