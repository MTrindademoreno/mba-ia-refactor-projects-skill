const sqlite3 = require('sqlite3').verbose();

function createConnection() {
    return new sqlite3.Database(':memory:');
}

function run(db, sql, params = []) {
    return new Promise((resolve, reject) => {
        db.run(sql, params, function callback(err) {
            if (err) return reject(err);
            resolve({ lastID: this.lastID, changes: this.changes });
        });
    });
}

function get(db, sql, params = []) {
    return new Promise((resolve, reject) => {
        db.get(sql, params, (err, row) => {
            if (err) return reject(err);
            resolve(row);
        });
    });
}

function all(db, sql, params = []) {
    return new Promise((resolve, reject) => {
        db.all(sql, params, (err, rows) => {
            if (err) return reject(err);
            resolve(rows);
        });
    });
}

function beginTransaction(db) {
    return run(db, 'BEGIN');
}

function commit(db) {
    return run(db, 'COMMIT');
}

function rollback(db) {
    return run(db, 'ROLLBACK');
}

module.exports = { createConnection, run, get, all, beginTransaction, commit, rollback };
