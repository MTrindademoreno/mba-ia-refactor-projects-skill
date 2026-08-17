const HttpError = require('../errors/HttpError');

class FinancialReportController {
    constructor(financialReportService) {
        this.financialReportService = financialReportService;
        this.handle = this.handle.bind(this);
    }

    async handle(req, res, next) {
        try {
            const report = await this.financialReportService.buildReport();
            res.json(report);
        } catch (err) {
            next(new HttpError(500, 'Erro DB'));
        }
    }
}

module.exports = FinancialReportController;
