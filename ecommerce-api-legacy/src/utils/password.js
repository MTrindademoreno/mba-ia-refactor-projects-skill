const crypto = require('crypto');

const KEY_LENGTH = 64;

function hashPassword(password) {
    const salt = crypto.randomBytes(16).toString('hex');
    const derivedKey = crypto.scryptSync(password, salt, KEY_LENGTH).toString('hex');
    return `${salt}:${derivedKey}`;
}

module.exports = { hashPassword };
