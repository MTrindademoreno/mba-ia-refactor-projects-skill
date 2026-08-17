function toUser(row) {
    if (!row) return null;
    return { id: row.id, name: row.name, email: row.email, passwordHash: row.pass };
}

module.exports = { toUser };
