const express = require('express');

function createRoutes({ checkoutController, financialReportController, userController }) {
    const router = express.Router();

    router.post('/api/checkout', checkoutController.handle);
    router.get('/api/admin/financial-report', financialReportController.handle);
    router.delete('/api/users/:id', userController.deleteUser);

    return router;
}

module.exports = createRoutes;
