================================
PHASE 1: PROJECT ANALYSIS
================================
Project:       code-smells-project
Language(s):   Python 3
Framework(s):  Flask 3.1.1 (flask-cors 5.0.1)
Runtime:       Python + pip (requirements.txt, no lockfile, no virtualenv manifest found)
Dependencies:  flask==3.1.1, flask-cors==5.0.1
Domain:        E-commerce API — products (produtos), users (usuarios), orders (pedidos), sales report, health check
Architecture:  Monolithic single-package Flask app with a thin controller layer over a single flat data-access module; no models/views/controllers directory split despite file naming
Source files:  5 inspected (app.py, controllers.py, database.py, models.py, requirements.txt) + README.md
Persistence:   SQLite, file `loja.db`, raw `sqlite3` driver (no ORM), schema created imperatively in database.py with seed data
================================

## Evidence

- **Entry point:** `app.py:1-88`. Creates the Flask app, registers all routes via `app.add_url_rule` bound directly to functions imported from `controllers`, and starts the dev server with `app.run(..., debug=True)` at `app.py:88`.
- **Manifest:** `requirements.txt:1-2` — only `flask` and `flask-cors` pinned, no test/lint/dev dependencies.
- **Routing:** all 16 routes are declared in `app.py:11-30`, plus two inline routes defined directly on `app` at `app.py:32-78` (`/`, `/admin/reset-db`, `/admin/query`) that bypass the `controllers` module entirely.
- **Controllers:** `controllers.py:1-292` contains one function per route, each handling request parsing, validation, and response shaping, and each importing `models` and (for `health_check`) `database.get_db` directly.
- **Data access:** `models.py:1-314` is a single flat module with no classes, mixing SQL execution, business logic (stock checks, order totals, discount tiers in `relatorio_vendas` at `models.py:256-262`), and result-shaping (manual dict construction repeated in `get_todos_produtos`, `get_produto_por_id`, `buscar_produtos`).
- **Database bootstrap:** `database.py:1-86` holds a module-level global `db_connection` (line 4) lazily initialized in `get_db()` (line 7), with `CREATE TABLE IF NOT EXISTS` DDL and seed-data inserts executed inline on first call — no separate migration mechanism.
- **Configuration:** `app.config["SECRET_KEY"]` and `DEBUG` are hardcoded literals in `app.py:7-8`; `db_path = "loja.db"` is hardcoded in `database.py:5`. No `.env`, `config.py`, or `os.getenv` usage found anywhere in the project.
- **Tests:** no `tests/` directory, no `test_*.py` files, and no test framework (`pytest`, `unittest`) referenced in `requirements.txt` or imported in source.
- **README:** `README.md` documents run instructions and also contains prose from a prior manual analysis and prior skill-construction notes, referencing an audit report file that is not currently present in `reports/` (the directory is empty at the start of this run).

## Architecture map

| Module | Responsibility observed | Notable dependencies |
| --- | --- | --- |
| `app.py` | Flask app creation, route registration, dev-server bootstrap; also contains two inline admin route handlers (`reset_database`, `executar_query`) that duplicate the controller-layer responsibility ad hoc | imports `controllers`, `database.get_db` |
| `controllers.py` | Per-route request handling: JSON parsing, field validation, error wrapping, response formatting | imports `models`, `database.get_db` (only for `health_check`) |
| `models.py` | Single flat module covering products, users, authentication, orders, stock, search, and sales reporting; builds SQL by string concatenation throughout | imports `database.get_db` |
| `database.py` | Global lazy-initialized SQLite connection, schema DDL, and seed data, all combined in `get_db()` | `sqlite3` |
| `requirements.txt` | Declares only runtime web-framework dependencies | — |

No `models/`, `views/`, or `controllers/` directories exist; the flat filenames (`controllers.py`, `models.py`) suggest an intended MVC-style separation, but `app.py` also contains route logic directly (the two `/admin/*` handlers), so route-handling responsibility is currently split between two places.

## Constraints and uncertainties

- No test suite exists, so any Phase 3 validation will rely on manual boot and endpoint smoke checks rather than automated regression tests — this should be confirmed with the user before Phase 3.
- The README references a previously produced audit report (`reports/audit-project-1-code-smells-project.md`) that is not present in the current `reports/` directory; this Phase 1 analysis was produced independently from source, not from that missing file.
- No `.env` or environment-based configuration exists anywhere in the project; whether the user wants environment-variable externalization is a Phase 2/3 scope question, not assumed here.
- `requirements.txt` has no pinned transitive dependencies or lockfile, so the exact installed Flask/Werkzeug patch version in any given environment is not verified from source alone.
================================
