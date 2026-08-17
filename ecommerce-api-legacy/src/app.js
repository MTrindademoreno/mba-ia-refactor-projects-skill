const express = require('express');
const config = require('./config');
const { createConnection } = require('./db/connection');
const { createSchema } = require('./db/schema');
const { seed } = require('./db/seed');

const UserRepository = require('./repositories/UserRepository');
const CourseRepository = require('./repositories/CourseRepository');
const EnrollmentRepository = require('./repositories/EnrollmentRepository');
const PaymentRepository = require('./repositories/PaymentRepository');
const AuditLogRepository = require('./repositories/AuditLogRepository');
const ReportRepository = require('./repositories/ReportRepository');

const CheckoutService = require('./services/CheckoutService');
const FinancialReportService = require('./services/FinancialReportService');
const UserService = require('./services/UserService');

const CheckoutController = require('./controllers/CheckoutController');
const FinancialReportController = require('./controllers/FinancialReportController');
const UserController = require('./controllers/UserController');

const Cache = require('./utils/Cache');
const createRoutes = require('./routes');
const errorHandler = require('./middleware/errorHandler');

async function createApp() {
    const db = createConnection();
    await createSchema(db);
    await seed(db);

    const userRepository = new UserRepository(db);
    const courseRepository = new CourseRepository(db);
    const enrollmentRepository = new EnrollmentRepository(db);
    const paymentRepository = new PaymentRepository(db);
    const auditLogRepository = new AuditLogRepository(db);
    const reportRepository = new ReportRepository(db);
    const cache = new Cache();

    const checkoutService = new CheckoutService({
        db,
        config,
        courseRepository,
        userRepository,
        enrollmentRepository,
        paymentRepository,
        auditLogRepository,
        cache,
    });
    const financialReportService = new FinancialReportService({ reportRepository });
    const userService = new UserService({ db, userRepository, enrollmentRepository, paymentRepository });

    const checkoutController = new CheckoutController(checkoutService);
    const financialReportController = new FinancialReportController(financialReportService);
    const userController = new UserController(userService);

    const app = express();
    app.use(express.json());
    app.use(createRoutes({ checkoutController, financialReportController, userController }));
    app.use(errorHandler);

    return app;
}

if (require.main === module) {
    createApp()
        .then(app => {
            app.listen(config.port, () => {
                console.log(`Frankenstein LMS rodando na porta ${config.port}...`);
            });
        })
        .catch(err => {
            console.error('Falha ao iniciar aplicação:', err);
            process.exit(1);
        });
}

module.exports = createApp;
