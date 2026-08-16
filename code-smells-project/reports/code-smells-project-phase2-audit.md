================================
ARCHITECTURE AUDIT REPORT
================================
Project:  code-smells-project
Stack:    Python 3, Flask 3.1.1, sqlite3 (raw driver), no ORM
Files:    4 source files inspected (app.py, controllers.py, database.py, models.py) | 780 lines total

Summary
CRITICAL: 5 | HIGH: 5 | MEDIUM: 4 | LOW: 3
================================

## Findings

### [CRITICAL] CS-008-1: SQL injection via string concatenation across models.py
File: models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155, 157-161, 163-166, 174, 188, 192, 220, 224, 279-280, 289-297
Evidence: Every data-access function builds SQL by concatenating raw Python values into the query string instead of using parameter binding, e.g. `cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))` (models.py:28) and `"INSERT INTO produtos (...) VALUES ('" + nome + "', ..."` (models.py:47-50). `buscar_produtos` concatenates the unescaped search term directly into a `LIKE` clause (models.py:291). This pattern is used in essentially every function in the module, including the login query (models.py:109-111).
Impact: Any request field that reaches these functions (product id, name, description, category, order items, email, password, search term, status) can be used to alter query structure — read/modify/delete arbitrary data, or bypass authentication in `login_usuario`.
Recommendation: Replace every string-built query with parameterized queries using `?` placeholders and pass values as a tuple to `cursor.execute(query, params)`, matching the pattern already used correctly in `database.py`'s seed inserts (`cursor.executemany(... VALUES (?, ?, ?, ?, ?)", produtos)`).

### [CRITICAL] SEC-01: Unauthenticated arbitrary SQL execution endpoint
File: app.py:59-78
Evidence: `/admin/query` accepts a raw `sql` string from the JSON body and executes it directly via `cursor.execute(query)` (app.py:69), with no authentication, authorization, or query allow-list. Both `SELECT` and mutating statements are accepted.
Impact: Any unauthenticated caller can read, modify, or destroy all data in the database, or use it as a general SQL execution primitive against the server's SQLite connection.
Recommendation: Remove this endpoint from the deployed application, or, if intentionally kept for internal tooling, gate it behind authentication/authorization and restrict it to a fixed set of vetted operations. This is a scope decision — flagging for explicit approval before Phase 3 removes or changes it.

### [CRITICAL] SEC-02: Unauthenticated destructive data-wipe endpoint
File: app.py:47-57
Evidence: `/admin/reset-db` deletes all rows from `itens_pedido`, `pedidos`, `produtos`, and `usuarios` (app.py:51-54) with no authentication check and no confirmation step.
Impact: Any unauthenticated caller can permanently destroy all application data in one request.
Recommendation: Remove or place behind authentication/authorization before any production exposure. Also a scope decision requiring explicit approval, since it changes a currently reachable route's availability.

### [CRITICAL] CS-009: Hardcoded secret key in source
File: app.py:7
Evidence: `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` is a literal committed to source control.
Impact: Anyone with repository access has the production signing key; it cannot be rotated without a code change and redeploy, and it is also returned verbatim in an API response (see HIGH finding below).
Recommendation: Load `SECRET_KEY` from an environment variable (`os.getenv("SECRET_KEY")`) with no committed production value, consistent with the "Environment-based Configuration" pattern.

### [CRITICAL] SEC-03: Passwords stored and compared in plaintext
File: database.py:75-79, models.py:105-120, models.py:122-131
Evidence: Seed users are inserted with plaintext passwords (database.py:76-79, e.g. `("Admin", "admin@loja.com", "admin123", "admin")`). `criar_usuario` stores whatever password string is supplied without hashing (models.py:122-131). `login_usuario` authenticates by matching the plaintext password directly inside the SQL `WHERE` clause (models.py:109-111), and `get_todos_usuarios`/`get_usuario_por_id` return the stored `senha` field verbatim in API responses (models.py:79-87, 95-103).
Impact: A database read (including via the SQL-injection and admin-query findings above) exposes every user's real password; there is no cryptographic protection of credentials at rest or in transit through the API.
Recommendation: Hash passwords at creation time with a standard KDF (e.g. Werkzeug's `generate_password_hash`/`check_password_hash`, already available transitively via Flask) and compare hashes in `login_usuario` instead of embedding the password in SQL. Note: existing seeded/plaintext rows would need a migration strategy — flagging for approval since this changes stored data format, not just code.

## Findings (continued)

### [HIGH] CS-002: God module — models.py concentrates every domain
File: models.py:1-314
Evidence: A single flat module with no classes handles products, users, authentication, orders, stock adjustment, order-item aggregation, and sales reporting (e.g. discount-tier business logic at models.py:256-262 sits next to raw SQL execution).
Impact: The module has many independent reasons to change, cannot be tested per domain in isolation, and any change to one domain (e.g. orders) risks touching code shared with unrelated domains (e.g. products) since everything lives in one namespace.
Recommendation: Split into per-domain modules (e.g. products, users, orders, reports) that each own their own queries, keeping function signatures stable so `controllers.py` call sites do not need to change behavior.

### [HIGH] CS-013: Global mutable connection state
File: database.py:4, 7-10
Evidence: `db_connection` is a module-level global, lazily assigned inside `get_db()` with a `global` statement (database.py:4, 8-10). All request handling across the app implicitly shares this single mutable global.
Impact: No dependency injection point exists for tests or alternate environments; the connection lifecycle is implicit and coupled to import order and first-call timing rather than being managed explicitly by the application.
Recommendation: Move connection creation into an explicit factory/initializer called once from the application entry point, and pass the connection (or a request-scoped accessor) into the modules that need it instead of relying on a module global.

### [HIGH] CS-010: Secret key and debug flag exposed in health check response
File: controllers.py:264-292
Evidence: `health_check` returns `"debug": True` and `"secret_key": "minha-chave-super-secreta-123"` directly in the JSON body (controllers.py:288-289), on an endpoint reachable without authentication.
Impact: Combined with the CRITICAL hardcoded-secret finding above, this makes the secret actively retrievable over the network by any caller, not merely present in source.
Recommendation: Remove `secret_key` and `debug` from the health-check payload entirely; a health check should report service/dependency status, not configuration values.

### [HIGH] ARCH-01: Domain/business rules embedded directly in HTTP controllers
File: controllers.py:52, 208-210, 242, 247-250
Evidence: The list of valid product categories is a literal inside `criar_produto` (controllers.py:52); the list of valid order statuses is a literal inside `atualizar_status_pedido` (controllers.py:242); and notification side effects ("ENVIANDO EMAIL/SMS/PUSH" at controllers.py:208-210, and status-specific notification rules at controllers.py:247-250) are triggered directly from the HTTP handler.
Impact: Domain rules that should be independent of the transport layer are only reachable by editing route-handler functions, and cannot be reused or unit-tested without a Flask request context.
Recommendation: Move category/status enumerations into shared domain constants, and move notification triggering into the order-processing logic in the data/business layer (or a dedicated notification hook called from there), so `controllers.py` only translates HTTP <-> domain calls.

### [HIGH] CS-010-2: Internal exception details leaked verbatim in API error responses
File: controllers.py:10-12, 21-22, 60-62, 77-78, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292
Evidence: Every controller function follows `except Exception as e: return jsonify({"erro": str(e)}), 500`, returning the raw Python exception message to the HTTP client for every unanticipated failure.
Impact: Internal implementation details (e.g. raw SQLite error text, which can itself reveal query structure given the SQL-injection findings above) are exposed to any API caller, aiding further attacks and leaking operational details.
Recommendation: Log the full exception server-side and return a generic error message and code to the client; reserve detailed messages for server logs only.

## Findings (continued)

### [MEDIUM] CS-011: N+1 queries when assembling order responses
File: models.py:171-201, 203-233
Evidence: `get_pedidos_usuario` and `get_todos_pedidos` each run one query for orders, then for every order run a second query for its items (models.py:188, 220), then for every item a third query to look up the product name (models.py:192, 224) — nested `cursor2`/`cursor3` queries inside loops.
Impact: Response time grows linearly with the number of orders and items rather than being a small constant number of queries; this degrades quickly as data grows.
Recommendation: Replace the nested-loop queries with a single join (orders + items + products) or a batched `IN (...)` query per level, and assemble the nested response structure in Python from the joined result set.

### [MEDIUM] CS-001: Duplicated validation logic between create and update product
File: controllers.py:24-62, 64-96
Evidence: `criar_produto` and `atualizar_produto` repeat the same field-presence checks (`nome`, `preco`, `estoque`) and the same negative-value checks for `preco`/`estoque` (controllers.py:30-35, 43-46 vs. 74-79, 87-90) with no shared helper.
Impact: The two validation blocks can drift apart over time (e.g. `atualizar_produto` does not re-validate the category or name length that `criar_produto` checks), producing inconsistent rules for effectively the same data shape.
Recommendation: Extract a single validation function used by both handlers, so the rule set is defined once.

### [MEDIUM] CS-015: Inconsistent error-signaling strategy across the data layer
File: models.py:41, 103, 142-145; controllers.py:16-20, 139-142, 205-206
Evidence: Not-found lookups return `None` (models.py:41, 103); stock/product validation failures inside `criar_pedido` return a plain dict with an `"erro"` key (models.py:142-145), which `controllers.py` then has to specifically check for with `if "erro" in resultado` (controllers.py:205-206); all other failures propagate as raised exceptions caught generically in the controller's `except Exception`.
Impact: Three different conventions for signaling failure from the same layer make the contract between `models.py` and `controllers.py` inconsistent and easy to get wrong when adding a new function.
Recommendation: Pick one consistent strategy (e.g. raise typed exceptions for all failure cases, including stock/not-found, and let controllers translate exception types to HTTP status codes).

### [MEDIUM] CS-019: No type hints anywhere in the codebase
File: app.py, controllers.py, models.py, database.py (all functions)
Evidence: None of the functions across the four modules declare parameter or return type annotations (e.g. `def criar_produto(nome, descricao, preco, estoque, categoria):` at models.py:43).
Impact: Editors/type checkers cannot catch type-related mistakes (e.g. passing a string where a number is expected in price/stock fields), and the expected shape of data crossing the controller/model boundary is only discoverable by reading implementation code.
Recommendation: Add type hints incrementally, starting with the controller/model boundary functions, and optionally introduce `mypy` for static checking.

## Findings (continued)

### [LOW] CS-007: Domain enumerations hardcoded as literals in controllers
File: controllers.py:52, 242
Evidence: `categorias_validas = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]` (controllers.py:52) and the inline status list `["pendente", "aprovado", "enviado", "entregue", "cancelado"]` (controllers.py:242) are literals local to their functions.
Impact: These domain-level enumerations must be found and edited inside HTTP handler code, and cannot be reused by other code paths that might need the same valid-value set.
Recommendation: Extract to named constants (or enums) in a shared module.

### [LOW] CS-020: Inconsistent route-registration style within the same app
File: app.py:11-30 vs. app.py:32-78
Evidence: Most routes are registered via `app.add_url_rule(...)` bound to functions imported from `controllers` (app.py:11-30), while three routes (`/`, `/admin/reset-db`, `/admin/query`) are declared inline on `app` using the `@app.route` decorator with their logic written directly in `app.py` (app.py:32-78).
Impact: Route-handling responsibility is split between two different files and two different registration idioms for no evident reason, making it harder to find where a given route's logic lives.
Recommendation: Standardize on one registration style and move all route-handler logic into `controllers.py` (or an equivalent handlers module) for consistency.

### [LOW] CS-018-1: Logging via print() instead of a logging framework
File: app.py:56, 83-86; controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 248, 250
Evidence: Operational and diagnostic messages are written with bare `print()` calls (e.g. `print("Produto criado com ID: " + str(id))` at controllers.py:57), rather than a configured logger.
Impact: No log levels, no structured output, and no way to control verbosity or route logs to a collection system without editing source code.
Recommendation: Replace `print()` calls with Python's `logging` module, configured once at the entry point.

## Approved-scope proposal

1. Parameterize every SQL statement in models.py to eliminate SQL injection (CS-008-1), preserving existing function signatures and return shapes.
2. Move `SECRET_KEY` and the SQLite path to environment variables with local-dev defaults (CS-009), and remove `secret_key`/`debug` from the `/health` response body (CS-010).
3. Address the two unauthenticated admin endpoints (SEC-01, SEC-02) — needs your decision: remove them entirely, or keep them gated behind authentication. No code change will be made here until you choose.
4. Address plaintext password storage (SEC-03) — needs your decision on migration handling for the existing seeded users, since hashing changes the stored data format, not just the code.
5. Split models.py into per-domain modules (products, users, orders, reports) without changing function signatures used by controllers.py (CS-002).
6. Replace nested-loop order/item/product lookups with joined queries (CS-011).
7. Extract shared product validation used by create and update (CS-001), and extract category/status enumerations into shared constants (CS-007).
8. Standardize all routes to go through controllers.py (CS-020), replace print() with logging (CS-018-1), and add type hints to controller/model function signatures (CS-019) as incremental, behavior-preserving cleanups.

Item 9 (CS-015 inconsistent error-signaling, CS-010-2 exception detail leakage, ARCH-01 notification/enum relocation) will be folded into the same pass as items 5–8 since they touch the same functions.

## Validation plan

- No automated test suite exists in this project (confirmed absent in Phase 1). Validation will rely on:
  - `python app.py` boot check — server starts without error and creates/reuses `loja.db`.
  - Manual smoke checks against each route group (produtos, usuarios, pedidos, relatórios, login, health) using representative requests, comparing response shape/status codes before and after each change.
  - Re-running the same smoke checks after the SQL parameterization change specifically, including a request containing a quote character in a text field, to confirm the injection is closed without breaking normal input.

Approval required: Do you approve this plan for Phase 3? Please also tell me your preference on items 3 (admin endpoints) and 4 (password hashing/migration), since those involve behavior/data decisions beyond a pure refactor.
================================
