function toCourse(row) {
    if (!row) return null;
    return { id: row.id, title: row.title, price: row.price, active: !!row.active };
}

module.exports = { toCourse };
