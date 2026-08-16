================================
ARCHITECTURE AUDIT REPORT
================================
Project:  code-smells-project
Stack:    Python 3, Flask 3.1.1, sqlite3 (raw driver), no ORM

Files:    4 application source files inspected (app.py: 89 lines, controllers.py: 293 lines, database.py: 87 lines, models.py: 315 lines) | 784 total lines

Summary
CRITICAL: 4 | HIGH: 4 | MEDIUM: 4 | LOW: 2
================================

## Findings

### [CRITICAL] CS-008a: SQL injection via string-concatenated queries (models.py)
File: models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155, 157-160, 163-166, 174, 188, 192, 220, 224, 279-280, 289-297
Evidence: Every query builder in `models.py` concatenates raw request-derived values directly into SQL text instead of using parameterized queries, e.g. `login_usuario`: `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"` (models.py:109-111), and `buscar_produtos`: `query += " AND (nome LIKE '%" + termo + "%' ...)"` (models.py:291). `sqlite3.Cursor.execute` supports `?` placeholders (used nowhere in this file), so the vulnerable pattern is consistent across all 13 data-access functions.
Impact: Any of these 13 functions accepts attacker-controlled strings (product name/description/category, email/senha, search term, status) with no escaping. `login_usuario` alone allows classic auth-bypass injection (e.g., `senha = "' OR '1'='1"`). Full read/write/delete access to all four tables is achievable through the public API without credentials.
Recommendation: Replace every concatenated query with parameterized `cursor.execute(sql, (params,))` calls; this is a mechanical, behavior-preserving change per function (Python's `sqlite3` supports `?` placeholders natively, no new dependency required).

### [CRITICAL] CS-008b: Unauthenticated arbitrary SQL execution endpoint
File: app.py:59-78
Evidence: `POST /admin/query` reads `dados.get("sql", "")` from the request body and passes it straight to `cursor.execute(query)` (app.py:69) with no authentication, authorization, or query allow-listing. It also commits any non-`SELECT` statement (app.py:75). `POST /admin/reset-db` (app.py:47-57) is likewise unauthenticated and unconditionally truncates all four tables.
Impact: Any unauthenticated caller can read, modify, or destroy the entire database, including dropping/altering the schema via SQLite's DDL support — this is a full data-plane compromise, strictly worse than a single injection point.
Recommendation: Remove `/admin/query` entirely (or gate it behind authentication + an explicit allow-list of read-only statements if it must exist for internal tooling); require authentication for `/admin/reset-db` and restrict it to non-production environments.

### [CRITICAL] CS-009: Hardcoded secret key and debug mode in source
File: app.py:7-8
Evidence: `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` and `app.config["DEBUG"] = True` are literals committed to source control; `app.run(..., debug=True)` (app.py:88) confirms the Flask debugger is intended to be reachable at runtime.
Impact: `SECRET_KEY` cannot be rotated without a code change/redeploy and is visible to anyone with repo access; with `DEBUG=True` in a reachable deployment, Flask's interactive debugger (Werkzeug) allows remote code execution if an unhandled exception surfaces a debugger PIN prompt.
Recommendation: Load `SECRET_KEY` and `DEBUG` from environment variables (e.g., `os.getenv("SECRET_KEY")`, default `DEBUG` to `False`), and fail startup if `SECRET_KEY` is unset in a non-development environment.

### [CRITICAL] Plaintext password storage and comparison
File: models.py:105-120 (login_usuario), 122-131 (criar_usuario); database.py:75-83 (seed data)
Evidence: `criar_usuario` inserts `senha` verbatim into the `usuarios` table with no hashing (models.py:126-129); `login_usuario` authenticates by string-equality SQL comparison against the stored plaintext value (models.py:109-111); seed users are inserted with plaintext passwords (`"admin123"`, `"123456"`, database.py:75-79); `get_todos_usuarios`/`get_usuario_por_id` also return the raw `senha` field to API callers (models.py:83, 99).
Impact: A database read (including via the CS-008b endpoint, or any future read-only leak) exposes every user's real password in cleartext; the `/usuarios` and `/usuarios/<id>` endpoints already return `senha` in the JSON response body today.
Recommendation: Hash passwords on write with a modern KDF (e.g., `werkzeug.security.generate_password_hash`, already available transitively via Flask) and verify with `check_password_hash` on login; stop selecting/returning the `senha` column in list/detail responses.

### [HIGH] CS-002: God Module — models.py spans four unrelated domains
File: models.py:1-315
Evidence: A single 315-line module contains persistence and rules for products (models.py:4-70), users/authentication (72-131), orders/inventory (133-201), aggregate reporting (203-273), order status transitions (275-283), and product search (285-314) — six distinct responsibilities in one file with no internal boundaries.
Impact: Any change to one domain (e.g., order logic) requires touching a file shared by unrelated domains, increasing merge conflicts and the blast radius of regressions; the module cannot be tested or reasoned about per-domain.
Recommendation: Split into domain-scoped modules (e.g., `produtos_repository.py`, `usuarios_repository.py`, `pedidos_repository.py`, `relatorios.py`) that each own their own queries, keeping the public function names/signatures stable so `controllers.py` call sites do not change.

### [HIGH] CS-013: Global mutable connection singleton
File: database.py:4, 7-11
Evidence: `db_connection = None` is a module-level global; `get_db()` lazily assigns to it via `global db_connection` and returns the same `sqlite3.Connection` to every caller across the process, opened with `check_same_thread=False` (database.py:10) specifically to allow cross-thread sharing of one connection/cursor state.
Impact: Flask's dev server and most WSGI servers handle requests on multiple threads; sharing one `sqlite3.Connection` (and implicitly its transaction state) across concurrent requests risks interleaved commits and inconsistent reads, and makes the module impossible to unit-test without mutating global state or monkeypatching.
Recommendation: Create a request-scoped connection using Flask's `g` object (`flask.g` + `teardown_appcontext`) or a connection-per-call pattern, still targeting the same `loja.db` file, so each request gets an isolated connection without global mutable state.

### [HIGH] CS-003: No abstraction between HTTP, domain, and persistence layers
File: app.py:4, 49, 66; controllers.py:3; models.py:1
Evidence: `app.py`, `controllers.py`, and `models.py` all import `database.get_db` directly and call it independently (app.py:49 and app.py:66 for the two admin routes, controllers.py's `health_check` at controllers.py:266, and every function in `models.py`); there is no repository interface or service layer that `controllers.py` depends on — it calls `models.*` functions that themselves reach into the global connection.
Impact: Every layer is hard-wired to the concrete SQLite connection; swapping storage, mocking persistence for a controller test, or adding a caching layer would require touching call sites in three files instead of one seam.
Recommendation: Once models.py is split (per CS-002), route all data access exclusively through the new per-domain modules and remove the direct `database.get_db` import from `app.py` and `controllers.py`, keeping `database.py` as the only module that constructs connections.

### [HIGH] CS-016: No automated test coverage
File: n/a (absence confirmed — no `tests/` directory, no `test_*.py`, no `pytest`/`unittest` in requirements.txt or imports)
Evidence: `requirements.txt` lists only `flask` and `flask-cors`; no test framework or test files exist in the project.
Impact: Every refactor in this project, including the plan below, currently has no automated regression safety net; correctness after any change can only be verified by manual boot and endpoint checks.
Recommendation: Out of scope to add a full suite in this pass (would expand scope beyond the approved architecture fixes), but Phase 3 validation will rely on manual boot + `curl` smoke tests per endpoint, listed in the Validation plan below. Recommend a follow-up task to add `pytest` + a minimal test module per domain once the split lands.

### [MEDIUM] CS-011: N+1 queries when assembling order responses
File: models.py:171-201 (get_pedidos_usuario), 203-233 (get_todos_pedidos)
Evidence: Both functions run one query for orders, then for each order row run a second query for its items (models.py:188, 220), and for each item row run a third query to resolve the product name (models.py:192, 224) — three nested cursors (`cursor`, `cursor2`, `cursor3`) per call, O(orders × items) round trips total.
Impact: Response time for `GET /pedidos` and `GET /pedidos/usuario/<id>` degrades linearly with order/item volume instead of running as a constant small number of queries.
Recommendation: Replace the nested-cursor loop with a single `JOIN` across `pedidos`, `itens_pedido`, and `produtos` (or two queries: one for orders, one batched `WHERE pedido_id IN (...)` for items+product names), grouping results in Python.

### [MEDIUM] CS-001: Duplicated row-mapping and validation logic
File: models.py:9-21, 31-40, 304-313; controllers.py:26-54, 66-90
Evidence: The product-row-to-dict mapping (`id`, `nome`, `descricao`, `preco`, `estoque`, `categoria`, `ativo`, `criado_em`) is written out identically three times in `get_todos_produtos`, `get_produto_por_id`, and `buscar_produtos`. Separately, `criar_produto` and `atualizar_produto` in `controllers.py` repeat the same five `if` checks for missing `nome`/`preco`/`estoque` and the same negative-value checks (controllers.py:30-46 vs. 74-90).
Impact: A field added to the product schema, or a validation rule change, must be edited in three (or two) places; the previous manual analysis in README.md already flagged the validation duplication independently, corroborating this finding.
Recommendation: Extract a single `_row_to_produto(row)` mapping helper in the products module, and a single `_validar_produto(dados)` validation helper shared by create/update in the controller (or a lightweight validation layer), called from both call sites.

### [MEDIUM] Internal error details leak to API callers via broad exception handling
File: controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262
Evidence: Every controller function wraps its body in `try/except Exception as e: return jsonify({"erro": str(e)}), 500`, returning the raw Python exception message to the HTTP client in all 15 endpoints; several also `print()` the same detail to stdout (e.g., controllers.py:11, 61, 219).
Impact: Exception text can surface internal implementation details (query fragments, file paths, type names) to any caller, and stdout logging with no structure/level makes production log triage harder.
Recommendation: Keep the broad catch as a last-resort safety net, but log the full exception server-side (e.g., `app.logger.exception(...)`) and return a generic client-facing message; reserve detailed messages for the specific, already-handled validation branches.

### [MEDIUM] CS-019: No type hints or input schemas across the HTTP/domain boundary
File: controllers.py (all function signatures), models.py (all function signatures)
Evidence: No function in `controllers.py` or `models.py` declares parameter or return types; request bodies are read via untyped `dados.get(...)` calls with manual `if key not in dados` checks instead of a schema (e.g., controllers.py:24-54).
Impact: There is no machine-checkable contract for what a controller passes to a model function or what shape it returns; this matches the previous manual analysis in README.md ("contratos entre camadas são implícitos") and increases the risk of silent breakage during the split proposed in CS-002.
Recommendation: Add type hints to the new per-domain module functions as they are created in Phase 3 (e.g., `def criar_produto(nome: str, descricao: str, preco: float, estoque: int, categoria: str) -> int`); introducing a full validation library (Pydantic/Marshmallow) is a larger change and should be a follow-up, not part of this pass.

### [LOW] CS-007: Magic strings for domain enumerations
File: controllers.py:52, 242
Evidence: The valid product categories list (`["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]`, controllers.py:52) and the valid order status list (`["pendente", "aprovado", "enviado", "entregue", "cancelado"]`, controllers.py:242) are inline literals inside HTTP handler functions.
Impact: The domain vocabulary for categories/status is defined only where a specific route happens to need it; a second route needing the same list (there is none today, but `atualizar_status_pedido`'s check is the only place the status enum exists) risks drifting out of sync if duplicated later.
Recommendation: Move both lists to module-level constants (e.g., `CATEGORIAS_VALIDAS`, `STATUS_VALIDOS`) in the module that owns each domain, imported by the controller.

### [LOW] CS-020: Inconsistent string formatting (concatenation vs. f-strings)
File: controllers.py:8, 11, 54, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250; models.py:47-50, 57-61, 68, 92, 109-111, 126-129, 140-166, 174, 188, 192, 220, 224, 279-280, 291-297
Evidence: All string building in both files uses `"..." + str(x) + "..."` concatenation rather than Python f-strings, even in the same statements that will be rewritten for CS-008a's parameterization.
Impact: Purely a readability/consistency issue; no functional risk on its own, but worth fixing opportunistically while touching the same lines for the SQL-injection fix.
Recommendation: When rewriting query strings and log/print messages for CS-008a, switch to f-strings at the same time (e.g., `f"Produto criado com ID: {id}"`).

## Approved-scope proposal

1. **Security fixes (CS-008a, CS-008b, CS-009, plaintext passwords):** parameterize every SQL statement in `models.py`; remove or lock down `/admin/query` and `/admin/reset-db`; move `SECRET_KEY`/`DEBUG` to environment variables; hash passwords with `werkzeug.security` and stop returning `senha` in responses.
2. **Structural split (CS-002, CS-003):** split `models.py` into `produtos_repository.py`, `usuarios_repository.py`, `pedidos_repository.py`, and `relatorios.py`, each importing `database.get_db` directly (removing that import from `app.py`/`controllers.py` where unused after the split); keep all public function names/signatures unchanged so `controllers.py` needs only import-path updates.
3. **Connection lifecycle (CS-013):** replace the global `db_connection` singleton with a Flask `g`-scoped connection opened per request and closed via `teardown_appcontext`, keeping the same `loja.db` file and schema/seed bootstrap behavior on first run.
4. **N+1 fix (CS-011):** rewrite `get_pedidos_usuario`/`get_todos_pedidos` to use a joined or batched query instead of nested per-row cursors.
5. **De-duplication (CS-001):** extract the shared product row-mapping helper and the shared product validation helper.
6. **Error handling (broad-exception finding):** log full exceptions server-side, return generic client-facing error messages from the broad `except` blocks.
7. **Low-severity cleanup (CS-007, CS-020, CS-019 for new modules):** extract category/status constants; add type hints to the newly created domain modules; convert touched string-building to f-strings.

Out of scope for this pass: adding a test framework/suite (CS-016) and a full request-validation library (extended CS-019) — both flagged as follow-up work, not required to fix the audited findings safely.

## Validation plan

- No automated test suite exists (CS-016), so validation is manual:
- `python app.py` boots without errors and logs the startup banner (confirms schema/seed bootstrap still runs).
- `GET /health` returns `200` with accurate counts and, after the CS-009/CS-010 fix, no longer includes `secret_key`/`debug` in the body.
- `GET /produtos`, `GET /produtos/<id>`, `GET /produtos/busca?q=...` return the same shape/data as before the split.
- `POST /produtos`, `PUT /produtos/<id>`, `DELETE /produtos/<id>` succeed with valid payloads and still reject invalid ones with the same 400 messages.
- `POST /usuarios` creates a user; `GET /usuarios`/`GET /usuarios/<id>` no longer expose `senha` in the response body.
- `POST /login` succeeds with the seeded admin credentials and fails with wrong credentials (confirms hashing didn't break auth); attempt a SQL-injection payload in `email`/`senha` and confirm it now fails cleanly instead of bypassing auth.
- `POST /pedidos`, `GET /pedidos`, `GET /pedidos/usuario/<id>`, `PUT /pedidos/<id>/status` return unchanged data shapes; verify order/item counts match pre-refactor manual runs.
- `GET /relatorios/vendas` returns the same aggregate numbers as before the change.
- `POST /admin/query` and `POST /admin/reset-db` reachability/behavior matches whatever the approved plan decides (removed, or now rejecting unauthenticated calls).
- No linter/formatter/build tooling is configured in this project (no `setup.cfg`, `pyproject.toml`, `.flake8`, or CI config found), so no static-check command will be run beyond `python -c "import app"`-style import sanity checks during Phase 3.

Approval required: Do you approve this plan for Phase 3?
================================
