class FinancialReportService {
    constructor({ reportRepository }) {
        this.reportRepository = reportRepository;
    }

    async buildReport() {
        const rows = await this.reportRepository.fetchCourseEnrollmentRows();

        const coursesById = new Map();
        for (const row of rows) {
            if (!coursesById.has(row.course_id)) {
                coursesById.set(row.course_id, { course: row.course_title, revenue: 0, students: [] });
            }
            const courseData = coursesById.get(row.course_id);

            if (row.enrollment_id === null) {
                continue;
            }

            if (row.payment_status === 'PAID') {
                courseData.revenue += row.payment_amount;
            }

            courseData.students.push({
                student: row.student_name || 'Unknown',
                paid: row.payment_amount != null ? row.payment_amount : 0,
            });
        }

        return Array.from(coursesById.values());
    }
}

module.exports = FinancialReportService;
