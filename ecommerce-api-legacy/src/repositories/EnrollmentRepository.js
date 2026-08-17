const { run, all } = require('../db/connection');
const { toEnrollment } = require('../models/Enrollment');

class EnrollmentRepository {
    constructor(db) {
        this.db = db;
    }

    async create(userId, courseId) {
        const result = await run(this.db, 'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [userId, courseId]);
        return result.lastID;
    }

    async findByUserId(userId) {
        const rows = await all(this.db, 'SELECT * FROM enrollments WHERE user_id = ?', [userId]);
        return rows.map(toEnrollment);
    }

    deleteByUserId(userId) {
        return run(this.db, 'DELETE FROM enrollments WHERE user_id = ?', [userId]);
    }
}

module.exports = EnrollmentRepository;
