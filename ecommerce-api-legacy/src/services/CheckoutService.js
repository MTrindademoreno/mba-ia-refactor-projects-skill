const HttpError = require('../errors/HttpError');
const { hashPassword } = require('../utils/password');
const { isApprovedTestCard } = require('../utils/card');
const { beginTransaction, commit, rollback } = require('../db/connection');

class CheckoutService {
    constructor({ db, config, courseRepository, userRepository, enrollmentRepository, paymentRepository, auditLogRepository, cache }) {
        this.db = db;
        this.config = config;
        this.courseRepository = courseRepository;
        this.userRepository = userRepository;
        this.enrollmentRepository = enrollmentRepository;
        this.paymentRepository = paymentRepository;
        this.auditLogRepository = auditLogRepository;
        this.cache = cache;
    }

    async checkout({ username, email, password, courseId, cardNumber }) {
        if (!username || !email || !courseId || !cardNumber) {
            throw new HttpError(400, 'Bad Request');
        }

        let course;
        try {
            course = await this.courseRepository.findActiveById(courseId);
        } catch (err) {
            course = null;
        }
        if (!course) {
            throw new HttpError(404, 'Curso não encontrado');
        }

        let user;
        try {
            user = await this.userRepository.findByEmail(email);
        } catch (err) {
            throw new HttpError(500, 'Erro DB');
        }

        let userId;
        if (!user) {
            if (!password) {
                throw new HttpError(400, 'Senha obrigatória para novo usuário');
            }
            try {
                userId = await this.userRepository.create({ name: username, email, passwordHash: hashPassword(password) });
            } catch (err) {
                throw new HttpError(500, 'Erro ao criar usuário');
            }
        } else {
            userId = user.id;
        }

        console.log(`Processando cartão ${cardNumber} na chave ${this.config.paymentGatewayKey}`);
        const status = isApprovedTestCard(cardNumber) ? 'PAID' : 'DENIED';
        if (status === 'DENIED') {
            throw new HttpError(400, 'Pagamento recusado');
        }

        await beginTransaction(this.db);

        let enrollmentId;
        try {
            enrollmentId = await this.enrollmentRepository.create(userId, courseId);
        } catch (err) {
            await rollback(this.db);
            throw new HttpError(500, 'Erro Matrícula');
        }

        try {
            await this.paymentRepository.create(enrollmentId, course.price, status);
        } catch (err) {
            await rollback(this.db);
            throw new HttpError(500, 'Erro Pagamento');
        }

        try {
            await this.auditLogRepository.create(`Checkout curso ${courseId} por ${userId}`);
        } catch (err) {
            await rollback(this.db);
            throw new HttpError(500, 'Erro ao registrar auditoria');
        }

        await commit(this.db);

        this.cache.set(`last_checkout_${userId}`, course.title);

        return { enrollmentId };
    }
}

module.exports = CheckoutService;
