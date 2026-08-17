class Cache {
    constructor() {
        this.store = new Map();
    }

    set(key, value) {
        console.log(`[LOG] Salvando no cache: ${key}`);
        this.store.set(key, value);
    }

    get(key) {
        return this.store.get(key);
    }
}

module.exports = Cache;
