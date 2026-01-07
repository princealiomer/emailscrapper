/**
 * Utility functions for extracting contact information
 */

/**
 * Extracts email addresses from text using regex
 * @param {string} text - The text to search
 * @returns {string[]} - Array of unique email addresses
 */
function extractEmails(text) {
    if (!text) return [];
    
    // Improved email regex pattern
    // \b ensures word boundaries to avoid catching parts of longer strings
    const emailRegex = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g;
    const matches = text.match(emailRegex) || [];
    
    return [...new Set(matches.map(email => email.toLowerCase()))];
}

/**
 * Extracts phone numbers from text using regex
 * @param {string} text - The text to search
 * @returns {string[]} - Array of unique phone numbers
 */
function extractPhones(text) {
    if (!text) return [];

    const phones = new Set();
    
    // Patterns translated from the suggested Python code
    const patterns = [
        /(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}/g, // +1-234-567-8900 or (234) 567-8900
        /\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b/g, // 234-567-8900
        /\b\d{10,}\b/g // 2345678900 (Sequence of 10+ digits)
    ];

    patterns.forEach(regex => {
        const matches = text.match(regex) || [];
        matches.forEach(m => phones.add(m));
    });
    
    // Filter and Validate
    // Ensure 10-15 digits
    const validPhones = Array.from(phones).filter(phone => {
        const digits = phone.replace(/\D/g, '');
        return digits.length >= 10 && digits.length <= 15;
    });
    
    return [...new Set(validPhones.map(p => p.trim()))];
}

module.exports = {
  extractEmails,
  extractPhones,
};
