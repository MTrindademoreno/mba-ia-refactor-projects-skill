================================
PHASE 1: PROJECT ANALYSIS
================================
Project:       code-smells-project
Language(s):   Python 3
Framework(s):  Flask 3.1.1 (flask-cors 5.0.1)
Runtime:       CPython, pip / requirements.txt (no lockfile, no venv committed)
Dependencies:  flask==3.1.1, flask-cors==5.0.1 (requirements.txt:1-2)
Domain:        E-commerce REST API — products (produtos), users (usuarios), orders (pedidos), a sales report endpoint, and admin/db endpoints
Architecture:  Monolithic single-package Flask app with a Controller→Model split, but no Service/Repository layer; models.py performs raw SQL directly (see map below)
Source files:  5 inspected (app.py, controllers.py, database.py, models.py, README.md) — all application source files in the project
Persistence:   SQLite, raw `sqlite3` driver, single global connection (database.py), file `loja.db` created at boot (not present in repo, generated at runtime)
================================

## Evidence

- **Entry point:** `app.py` — creates the Flask app, sets `SECRET_KEY` and `DEBUG` as hardcoded literals (app.py:7-8), registers all routes via `app.add_url_rule` pointing at functions imported from `controllers` (app.py:11-30), and defines three inline routes directly in `app.py` itself: `/` (index, app.py:32-45), `/admin/reset-db` (app.py:47-57), `/admin/query` (app.py:59-78). Boot block at app.py:80-88 calls `get_db()` once and starts the dev server with `debug=True`.
- **Route table (16 endpoints):** GET/POST/PUT/DELETE `/produtos*`, GET/POST `/usuarios*`, POST `/login`, POST/GET/PUT `/pedidos*`, GET `/relatorios/vendas`, GET `/health`, GET `/`, POST `/admin/reset-db`, POST `/admin/query`.
- **Controller layer (`controllers.py`, 292 lines):** one function per route, all following the same shape — parse `request`, hand-roll validation with `if` chains, call a `models.*` function, wrap the result in `jsonify(...)`, catch `Exception` broadly and return HTTP 500 with `str(e)`. No framework-level input schema (no Pydantic/Marshmallow), no shared response helper (each function builds its own dict shape).
- **Model layer (`models.py`, 314 lines):** every persistence function for products, users, auth, orders, and reporting lives in this single module. Functions call `get_db()` directly (module-level import from `database.py`), build SQL with Python string concatenation, and manually map `sqlite3.Row` objects to dicts (repeated in `get_todos_produtos`, `get_produto_por_id`, `buscar_produtos` — models.py:4-22, 24-41, 285-314 — identical row-mapping block duplicated three times).
- **Database module (`database.py`, 86 lines):** module-level global `db_connection`, lazily initialized singleton via `get_db()` (database.py:4-11); `get_db()` also owns schema creation (`CREATE TABLE IF NOT EXISTS`, database.py:14-53) and seed-data insertion (database.py:56-84) — connection management, schema definition, and fixture seeding are one function.
- **Configuration:** no `.env`, `config.py`, or environment-variable usage found anywhere in the four Python files (`grep` for `os.getenv`/`os.environ` returns nothing beyond `import os` in database.py, which is unused for config). `SECRET_KEY` and `DEBUG=True` are literals in `app.py:7-8`; `db_path = "loja.db"` is a literal in `database.py:5`.
- **Tests:** no `tests/` directory, no `test_*.py` files, no test framework (`pytest`, `unittest`) in `requirements.txt` or imported anywhere. Zero automated test coverage.
- **Admin endpoints:** `/admin/reset-db` (app.py:47-57) and `/admin/query` (app.py:59-78) are registered with no authentication/authorization check and no route-prefix protection; `/admin/query` executes arbitrary caller-supplied SQL via `cursor.execute(query)` (app.py:69).
- **Deployment signals:** none — no `Dockerfile`, `Procfile`, `wsgi.py`, or CI config found in this directory. `app.run(..., debug=True)` (app.py:88) is the only run path, i.e., the dev server is the de facto deployment mechanism as committed.

## Architecture map

| Module | Responsibility (as implemented) | Notable dependencies |
| --- | --- | --- |
| `app.py` | Flask app factory/bootstrap, full route table, plus 3 routes with business logic inlined (index, db reset, raw SQL execution) | imports `controllers`, `database.get_db` |
| `controllers.py` | HTTP-layer functions: request parsing, ad-hoc validation, exception-to-JSON translation, response shaping — one function per route | imports `models`, `database.get_db` (used only by `health_check`) |
| `models.py` | Data access AND domain rules for 4 sub-domains (products, users/auth, orders/inventory, sales reporting) via raw SQL string building | imports `database.get_db` |
| `database.py` | Connection singleton, schema DDL, and seed-data fixtures, all inside one `get_db()` function | `sqlite3` |

Dependency direction is consistently `app.py → controllers.py → models.py → database.py` (no circular imports observed), but every layer reaches into `database.get_db()` independently (`app.py`, `controllers.py`, `models.py` all import it directly) rather than through a single access point, and `models.py` is a de facto God Module spanning unrelated sub-domains.

## Constraints and uncertainties

- `loja.db` is not present in the repo; schema and seed data are generated on first boot from `database.py`, so no existing production data needs migration — safe to treat persistence changes as behavior-preserving as long as the schema DDL is kept identical.
- This directory is one of three sibling legacy projects in a shared parent repo (`code-smells-project`, `ecommerce-api-legacy`, `task-manager-api`, per the root commit history); scope for this run is `code-smells-project` only, per the current working directory.
- No test suite exists, so Phase 3 validation will rely on manual boot checks and endpoint smoke tests (e.g., `curl`) rather than an existing automated regression suite — this will be called out explicitly in the Phase 2 validation plan.
- `README.md` already contains a prior manual analysis (5 findings) appended by a previous session; Phase 2 will independently verify and supersede it with file/line evidence rather than assuming it is authoritative.
================================
