const { get, run } = require('../db/connection');
const { toUser } = require('../models/User');

class UserRepository {
    constructor(db) {
        this.db = db;
    }

    async findByEmail(email) {
        const row = await get(this.db, 'SELECT * FROM users WHERE email = ?', [email]);
        return toUser(row);
    }

    async create({ name, email, passwordHash }) {
        const result = await run(this.db, 'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [name, email, passwordHash]);
        return result.lastID;
    }

    delete(id) {
        return run(this.db, 'DELETE FROM users WHERE id = ?', [id]);
    }
}

module.exports = UserRepository;
