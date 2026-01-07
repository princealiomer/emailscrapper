const puppeteer = require('puppeteer');
const { extractEmails, extractPhones } = require('./utils');

class Scraper {
    constructor() {
        this.browser = null;
    }

    async init() {
        this.browser = await puppeteer.launch({
            headless: "new", // Use new headless mode
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        });
    }

    async close() {
        if (this.browser) {
            await this.browser.close();
        }
    }

    async scrape(url) {
        if (!this.browser) {
            await this.init();
        }

        const result = {
            url: url,
            emails: new Set(),
            phones: new Set(),
            pagesScraped: []
        };

        const page = await this.browser.newPage();
        // Set a realistic user agent
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36');

        try {
            console.log(`Navigating to ${url}...`);
            await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });
            result.pagesScraped.push(url);

            // 1. Scrape Home Page
            await this.autoScroll(page);
            await this.extractData(page, result);

            // 2. Find and Navigate to Contact Page
            const contactLink = await this.findContactLink(page);
            if (contactLink) {
                console.log(`Found contact link: ${contactLink}. Navigating...`);
                // Normalize URL
                const contactUrl = new URL(contactLink, url).href;
                
                // Avoid re-scraping if it's somehow the same page
                if (!result.pagesScraped.includes(contactUrl)) {
                    await page.goto(contactUrl, { waitUntil: 'networkidle2', timeout: 30000 });
                    result.pagesScraped.push(contactUrl);
                    await this.autoScroll(page);
                    await this.extractData(page, result);
                }
            } else {
                console.log('No obvious contact page found.');
            }

        } catch (error) {
            console.error(`Error scraping ${url}:`, error.message);
        } finally {
            await page.close();
        }

        return {
            url: result.url,
            emails: Array.from(result.emails),
            phones: Array.from(result.phones),
            pagesScraped: result.pagesScraped
        };
    }

    async extractData(page, result) {
        try {
            // Get full text content
            // We use standard 'innerText' or 'textContent' from the body
            const text = await page.evaluate(() => document.body.innerText);
            
            // Also looking into hrefs for mailto: or tel: links is a good idea
            const hrefs = await page.evaluate(() => {
                const anchors = Array.from(document.querySelectorAll('a[href]'));
                return anchors.map(a => a.href);
            });

            // Extract from text
            const textEmails = extractEmails(text);
            const textPhones = extractPhones(text);

            textEmails.forEach(e => result.emails.add(e));
            textPhones.forEach(p => result.phones.add(p));

            // Extract from hrefs (mailto: and tel:)
            hrefs.forEach(href => {
                if (href.startsWith('mailto:')) {
                    const email = href.replace('mailto:', '').split('?')[0]; // clean params
                    if (email) result.emails.add(decodeURIComponent(email));
                }
                if (href.startsWith('tel:')) {
                    const phone = href.replace('tel:', '');
                    if (phone) result.phones.add(decodeURIComponent(phone));
                }
            });

        } catch (err) {
            console.error('Error extracting data from page:', err.message);
        }
    }

    async findContactLink(page) {
        // Evaluate page to find a link that looks like a contact page
        return await page.evaluate(() => {
            const anchors = Array.from(document.querySelectorAll('a'));
            
            // Heuristics: Link text or href contains keywords
            const keywords = ['contact', 'contact us', 'contact-us', 'get in touch', 'about us', 'about', 'reach', 'touch', 'support', 'help'];
            
            for (const a of anchors) {
                const text = a.innerText.toLowerCase().trim();
                const href = a.getAttribute('href');
                
                if (!href) continue;

                // Check text exactish match
                if (keywords.some(k => text.includes(k))) {
                     return href;
                }
                
                // Check href if text is ambiguous (but be careful not to just match random things)
                if (keywords.some(k => href.toLowerCase().includes(k))) {
                    return href;
                }
            }
            return null;
        });
    }

    async autoScroll(page) {
        await page.evaluate(async () => {
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
        });
    }
}

module.exports = Scraper;
