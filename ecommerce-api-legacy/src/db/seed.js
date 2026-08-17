const { run } = require('./connection');

async function seed(db) {
    await run(db, "INSERT INTO users (name, email, pass) VALUES ('Leonan', 'leonan@fullcycle.com.br', '123')");
    await run(db, "INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1), ('Docker', 497.00, 1)");
    await run(db, 'INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
    await run(db, "INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID')");
}

module.exports = { seed };
