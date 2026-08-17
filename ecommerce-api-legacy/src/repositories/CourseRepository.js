const { get } = require('../db/connection');
const { toCourse } = require('../models/Course');

class CourseRepository {
    constructor(db) {
        this.db = db;
    }

    async findActiveById(id) {
        const row = await get(this.db, 'SELECT * FROM courses WHERE id = ? AND active = 1', [id]);
        return toCourse(row);
    }
}

module.exports = CourseRepository;
