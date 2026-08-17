require('./env');

function readEnv(name, fallback) {
    const value = process.env[name];
    if (value !== undefined && value !== '') return value;
    if (fallback !== undefined) return fallback;
    throw new Error(`Missing required environment variable: ${name}`);
}

const config = {
    port: Number(readEnv('PORT', '3000')),
    dbUser: readEnv('DB_USER'),
    dbPass: readEnv('DB_PASS'),
    paymentGatewayKey: readEnv('PAYMENT_GATEWAY_KEY'),
    smtpUser: readEnv('SMTP_USER'),
};

module.exports = config;
