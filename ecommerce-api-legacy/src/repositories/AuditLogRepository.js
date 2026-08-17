const { run } = require('../db/connection');

class AuditLogRepository {
    constructor(db) {
        this.db = db;
    }

    create(action) {
        return run(this.db, "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [action]);
    }
}

module.exports = AuditLogRepository;
