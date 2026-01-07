from playwright.sync_api import sync_playwright
import time

url = "https://ouremirates.com/contact/"

def extract_emails(text):
    import re
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return list(set(re.findall(email_pattern, text)))

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    print(f"Navigating to {url}...")
    page.goto(url)
    
    print("Scrolling to trigger lazy loading...")
    # Scroll down logic
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
    # Wait a bit for potential animations/network
    time.sleep(3)
    
    content = page.content()
    text = page.inner_text('body')
    
    print("--- Extraction Results ---")
    emails = extract_emails(text)
    print(f"Emails found: {emails}")
    
    browser.close()
