const fs = require('fs');
const path = require('path');

function loadEnvFile(filePath) {
    if (!fs.existsSync(filePath)) return;

    const content = fs.readFileSync(filePath, 'utf8');
    content.split('\n').forEach(line => {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith('#')) return;

        const eqIndex = trimmed.indexOf('=');
        if (eqIndex === -1) return;

        const key = trimmed.slice(0, eqIndex).trim();
        let value = trimmed.slice(eqIndex + 1).trim();
        const isQuoted = (value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"));
        if (isQuoted) value = value.slice(1, -1);

        if (process.env[key] === undefined) {
            process.env[key] = value;
        }
    });
}

loadEnvFile(path.resolve(__dirname, '..', '..', '.env'));

module.exports = { loadEnvFile };
