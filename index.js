const Scraper = require('./scraper');

async function main() {
    const args = process.argv.slice(2);
    if (args.length === 0) {
        console.error('Please provide a URL to scrape.');
        console.error('Usage: node index.js <URL>');
        process.exit(1);
    }

    let url = args[0];
    
    // Ensure URL has proper scheme
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
        url = 'https://' + url;
    }

    const scraper = new Scraper();
    
    try {
        console.log(`Starting scrape for: ${url}`);
        await scraper.init();
        const results = await scraper.scrape(url);
        
        console.log('\n--- Scraping Results ---');
        console.log(JSON.stringify(results, null, 2));
        
    } catch (error) {
        console.error('Fatal error:', error);
    } finally {
        await scraper.close();
    }
}

main();
