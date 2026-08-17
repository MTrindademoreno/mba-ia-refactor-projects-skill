const HttpError = require('../errors/HttpError');

function errorHandler(err, req, res, next) {
    if (err instanceof HttpError) {
        return res.status(err.statusCode).send(err.message);
    }

    console.error(err);
    res.status(500).send('Erro interno');
}

module.exports = errorHandler;
