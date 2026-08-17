const { run } = require('../db/connection');

class PaymentRepository {
    constructor(db) {
        this.db = db;
    }

    create(enrollmentId, amount, status) {
        return run(this.db, 'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)', [enrollmentId, amount, status]);
    }

    deleteByEnrollmentIds(enrollmentIds) {
        if (enrollmentIds.length === 0) return Promise.resolve();
        const placeholders = enrollmentIds.map(() => '?').join(', ');
        return run(this.db, `DELETE FROM payments WHERE enrollment_id IN (${placeholders})`, enrollmentIds);
    }
}

module.exports = PaymentRepository;
