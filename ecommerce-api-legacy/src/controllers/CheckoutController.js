class CheckoutController {
    constructor(checkoutService) {
        this.checkoutService = checkoutService;
        this.handle = this.handle.bind(this);
    }

    async handle(req, res, next) {
        try {
            const { usr, eml, pwd, c_id, card } = req.body;
            const result = await this.checkoutService.checkout({
                username: usr,
                email: eml,
                password: pwd,
                courseId: c_id,
                cardNumber: card,
            });
            res.status(200).json({ msg: 'Sucesso', enrollment_id: result.enrollmentId });
        } catch (err) {
            next(err);
        }
    }
}

module.exports = CheckoutController;
