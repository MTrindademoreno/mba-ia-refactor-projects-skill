function toEnrollment(row) {
    if (!row) return null;
    return { id: row.id, userId: row.user_id, courseId: row.course_id };
}

module.exports = { toEnrollment };
