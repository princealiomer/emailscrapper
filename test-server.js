const http = require('http');

const server = http.createServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    
    if (req.url === '/') {
        res.end(`
            <html>
                <body>
                    <h1>Welcome into the Home Page</h1>
                    <p>We are a great company.</p>
                    <a href="/contact">Contact Us</a>
                </body>
            </html>
        `);
    } else if (req.url === '/contact') {
        res.end(`
            <html>
                <body>
                    <h1>Contact Page</h1>
                    <p>Get in touch with us!</p>
                    <p>Email: support@test-scrapers.com</p>
                    <p>Phone: +1-555-012-3456</p>
                    <p>Another Phone: (123) 456-7890</p>
                </body>
            </html>
        `);
    } else {
        res.end('<h1>404 Not Found</h1>');
    }
});

server.listen(3000, () => {
    console.log('Test server running at http://localhost:3000');
});
