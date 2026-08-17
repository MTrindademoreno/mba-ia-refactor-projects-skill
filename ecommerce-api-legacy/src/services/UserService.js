const HttpError = require('../errors/HttpError');
const { beginTransaction, commit, rollback } = require('../db/connection');

class UserService {
    constructor({ db, userRepository, enrollmentRepository, paymentRepository }) {
        this.db = db;
        this.userRepository = userRepository;
        this.enrollmentRepository = enrollmentRepository;
        this.paymentRepository = paymentRepository;
    }

    async deleteUser(userId) {
        await beginTransaction(this.db);
        try {
            const enrollments = await this.enrollmentRepository.findByUserId(userId);
            const enrollmentIds = enrollments.map(enrollment => enrollment.id);

            await this.paymentRepository.deleteByEnrollmentIds(enrollmentIds);
            await this.enrollmentRepository.deleteByUserId(userId);
            await this.userRepository.delete(userId);

            await commit(this.db);
        } catch (err) {
            await rollback(this.db);
            throw new HttpError(500, 'Erro ao deletar usuário');
        }
    }
}

module.exports = UserService;
