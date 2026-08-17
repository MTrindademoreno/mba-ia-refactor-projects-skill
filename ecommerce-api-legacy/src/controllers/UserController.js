class UserController {
    constructor(userService) {
        this.userService = userService;
        this.deleteUser = this.deleteUser.bind(this);
    }

    async deleteUser(req, res, next) {
        try {
            await this.userService.deleteUser(req.params.id);
            res.status(200).send('Usuário deletado com sucesso, incluindo matrículas e pagamentos associados.');
        } catch (err) {
            next(err);
        }
    }
}

module.exports = UserController;
