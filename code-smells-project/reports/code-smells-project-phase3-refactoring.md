================================
PHASE 3: REFACTORING COMPLETE
================================
Target architecture: Flask monolith reorganized by responsibility — HTTP entry points (`routes.py` + `controllers.py`), domain data access split by domain (`models/`), shared validation/constants (`utils/`), environment-based configuration (`config.py`), and an explicit composition root (`app.py`) that owns database connection setup instead of a module-level global.

## Changed structure

```
app.py            (rewritten)  Composition root: builds the DB connection, wires it into each
                                 models/ submodule via init(), creates the Flask app, runs the server.
config.py         (new)        Environment-based settings: SECRET_KEY, DEBUG, DATABASE_PATH.
routes.py         (new)        All route registration in one place (moved out of app.py); the two
                                 unauthenticated admin routes are not carried over.
controllers.py    (rewritten)  Same request handlers as before, now calling models/produtos.py,
                                 models/usuarios.py, models/pedidos.py, and utils/validation.py;
                                 all generic exception handlers now log internally and return a
                                 sanitized message instead of the raw exception text.
database.py       (rewritten)  Database class with connect(): builds the schema and seeds initial
                                 data explicitly, called once from app.py instead of lazily from a
                                 module-level global on first access.
models.py         (deleted)    Replaced by models/ (see below).
models/           (new)
  produtos.py                  Product data access — all queries parameterized.
  usuarios.py                  User data access — passwords hashed with werkzeug.security;
                                 responses no longer include the password/hash field.
  pedidos.py                   Order + sales-report data access — order/item/product reads use a
                                 single joined query instead of nested per-row lookups.
utils/            (new)
  constants.py                 CATEGORIAS_VALIDAS, STATUS_PEDIDO_VALIDOS (moved out of controllers.py).
  validation.py                validar_produto() shared by product create and update.
```

## Changes made

- **CS-008-1** (SQL injection, CRITICAL): every query in `models/produtos.py`, `models/usuarios.py`, and `models/pedidos.py` now uses `?` parameter binding instead of string concatenation.
- **SEC-01 / SEC-02** (unauthenticated admin endpoints, CRITICAL): `/admin/reset-db` and `/admin/query` were removed entirely (per your approval); they no longer exist in `routes.py`, `app.py`, or anywhere else.
- **CS-009 / CS-010** (hardcoded secret, exposed config, CRITICAL/HIGH): `SECRET_KEY` and the database path now come from `config.py`, sourced from `SECRET_KEY`/`DATABASE_PATH` environment variables with local-dev fallbacks. `/health` no longer returns `secret_key` or `debug`.
- **SEC-03** (plaintext passwords, CRITICAL): `models/usuarios.py` hashes passwords with `werkzeug.security.generate_password_hash` on creation and verifies with `check_password_hash` on login (per your approval); `database.py`'s seed data now stores hashed versions of the same three seed passwords, so the documented seed credentials (`admin@loja.com` / `admin123`, etc.) still work.
- **CS-002** (God module, HIGH): `models.py` was split into `models/produtos.py`, `models/usuarios.py`, and `models/pedidos.py` (which also owns the sales-report query, since it operates on the same `pedidos` table). `controllers.py` call sites were updated to the new module paths; function behavior is otherwise unchanged.
- **CS-013** (global mutable connection state, HIGH — not separately numbered in the Phase 2 proposal, addressed as a direct consequence of splitting `models.py`): `database.py` no longer holds a lazily-initialized module-level global. `app.py` now creates the connection once at startup and passes it into each `models/` submodule via an explicit `init(connection)` call.
- **CS-010 / HIGH** (secret_key/debug in `/health`): removed from the response body (see CS-009/CS-010 above).
- **CS-010-2** (internal exception details leaked in API responses, HIGH): every `except Exception` block in `controllers.py` now calls `logger.exception(...)` and returns a generic `"Erro interno ao processar a requisição"` message instead of `str(e)`. `health_check`'s error branch was changed the same way.
- **ARCH-01** (domain rules embedded in controllers, HIGH): the product-category list and order-status list moved to `utils/constants.py`; order-creation and status-change notifications moved from `print()` calls inside `controllers.py` into `logger.info(...)` calls (see CS-018-1 below), still triggered at the same point in the flow.
- **CS-011** (N+1 queries, MEDIUM): `models/pedidos.py`'s `get_por_usuario`/`get_todos` now run a single `LEFT JOIN` query across `pedidos`, `itens_pedido`, and `produtos` and group the rows in Python, instead of one query per order plus one query per item.
- **CS-001** (duplicated validation, MEDIUM): `criar_produto` and `atualizar_produto` in `controllers.py` both call the single `validar_produto()` function in `utils/validation.py`. This intentionally makes `atualizar_produto` apply the same name-length and category checks `criar_produto` already had — closing the exact rule drift the Phase 2 audit flagged, at the cost of `atualizar_produto` now rejecting a couple of edge-case inputs (very short/long names, invalid category) it previously accepted.
- **CS-015** (inconsistent error signaling, MEDIUM): the "return a dict with an `erro` key" convention from order creation was kept only for `models/pedidos.py::criar` (its one genuine business-rule-failure case), and controllers still check for it in the same way as before; no other model function returns that shape any more — not-found is `None`, and everything else is a real exception.
- **CS-019** (no type hints, MEDIUM): added to all functions in `config.py`, `database.py`, `utils/validation.py`, `utils/constants.py`, and every `models/*.py` submodule.
- **CS-007** (magic category/status literals, LOW): moved into `utils/constants.py` (see ARCH-01 above).
- **CS-020** (inconsistent route registration, LOW): all 16 routes are now registered the same way, in one place (`routes.py`), through `controllers.py` handlers; `app.py` no longer declares any `@app.route` handlers directly.
- **CS-018-1** (print-based logging, LOW): `logging.basicConfig` is configured once in `app.py`; all diagnostic/notification `print()` calls in `controllers.py` and `models/pedidos.py`'s order-status logic were replaced with `logger.info`/`logger.exception`. The one-time startup banner in `app.py`'s `if __name__ == "__main__"` block was left as `print()`, since it's a CLI startup message, not request-handling logging.

## Deliberate response-contract changes (flagged, not silent)

- `/health` no longer returns `secret_key` or `debug` (approved as part of the Phase 2 plan). `db_path` was kept in the response, now sourced from `config.DATABASE_PATH` instead of a literal.
- `/admin/reset-db` and `/admin/query` no longer exist (approved).
- `GET /usuarios` and `GET /usuarios/<id>` no longer include the `senha` field in their JSON response. The original endpoint returned the password in plaintext; once it's a hash instead, returning it serves no purpose and keeps a security anti-pattern that CS-010's "exposed sensitive information" category already flags. This wasn't separately called out as its own approval question, so flagging it explicitly here.
- Every controller's generic (unexpected-exception) error response text changed from the raw exception message to a fixed `"Erro interno ao processar a requisição"` string; expected-error responses (validation failures, not-found, business-rule failures) kept their original text and status codes.
- `atualizar_produto` (`PUT /produtos/<id>`) now also enforces name length (2–200 chars) and category validity, which it previously did not — see CS-001 above.

## Validation

| Check | Command or method | Result |
| --- | --- | --- |
| Dependency install | `pip install -r requirements.txt` | pass — flask 3.1.1, flask-cors 5.0.1, werkzeug 3.1.8 installed; no new entries needed in requirements.txt since werkzeug ships as Flask's dependency |
| Boot check (test client) | `python -c "import app; app.app.test_client()..."` | pass — app imports, builds, and serves requests without error |
| Boot check (real server) | `python app.py` + `curl` against a live process | pass — server starts, `/health` and `/produtos` respond 200 over real HTTP, admin routes return 404 |
| Endpoint smoke tests | manual requests via Flask test client, covering: index, health, product list/get/create/update/delete/search (including a name containing a quote character, to confirm SQL-injection resistance), user create/list (confirms no password field leaks), login (correct and incorrect password against the hashed seed data), order creation (success, insufficient stock, unknown product), order listing by user and globally (confirms joined-query output matches the original nested `itens` shape), order status update (valid and invalid status, notification log lines), sales report (discount tiers) | pass — all responses matched expected status codes and shapes per the endpoint's original contract, except the deliberate contract changes listed above |
| Automated regression tests | none — project has no test suite (confirmed in Phase 1) | not run: no test suite exists |
| Static typing / lint | none configured in the project | not run: no `mypy`/linter configured; type hints were added but not statically checked by a tool |

Test artifacts (`loja.db` created during smoke testing, along with the server processes and log file used for the live-server check) were removed after validation; `*.db` is already covered by the repository's `.gitignore`.

## Remaining risks and follow-up

- **No automated test suite.** All validation above was manual/exploratory. Adding `pytest` with unit tests for `utils/validation.py` and `models/*.py`, plus a handful of Flask test-client integration tests for the controllers, would let future changes be verified without manual smoke testing.
- **`SECRET_KEY`/`DEBUG` still have committed fallback defaults** (`config.py`) so the app keeps booting out of the box without a `.env` file, matching current project conventions (no environment-config setup existed before this refactor). For any real deployment, `SECRET_KEY` must be set via environment variable and `DEBUG` must be `False` — the code allows this but does not enforce it (no fail-fast check), which is a reasonable follow-up if this project moves toward production use.
- **Dependency injection is partial.** `models/*.py` modules receive their database connection once via an explicit `init()` call from the composition root (fixing CS-013's core problem — no more implicit lazy-global mutation from arbitrary call sites), but they still hold that connection in a module-level variable rather than each function receiving it as a parameter or each domain being a class with constructor injection. Full elimination of the module-level accessor (e.g. converting to repository classes) was intentionally out of scope for this pass, since the approved Phase 2 plan scoped the fix as a per-domain module split, not a class-based repository/service layer.
- **`criar_pedido`'s per-item product lookup loop remains a query-per-item pattern** (one `SELECT` per order line to check stock and price). This was left as-is because it's a genuine per-item business check (stock/price must be read before deciding whether the order is valid), not the redundant read-side N+1 pattern that CS-011 flagged in `get_por_usuario`/`get_todos`; batching it further wasn't part of the approved scope.
================================
