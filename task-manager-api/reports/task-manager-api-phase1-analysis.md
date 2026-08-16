================================
PHASE 1: PROJECT ANALYSIS
================================
Project:       task-manager-api
Language(s):   Python 3
Framework(s):  Flask 3.0.0 (flask-sqlalchemy 3.1.1, flask-cors 4.0.0, marshmallow 3.20.1 declared but unused, requests 2.31.0 declared but unused, python-dotenv 1.0.0 declared but unused)
Runtime:       CPython, package manager pip (requirements.txt, no lockfile)
Dependencies:  flask, flask-sqlalchemy, flask-cors, marshmallow, requests, python-dotenv (requirements.txt:1-6)
Domain:        Task management API — users, tasks, categories, and reporting endpoints (routes/task_routes.py, routes/user_routes.py, routes/report_routes.py)
Architecture:  Partially layered Flask app (models/, routes/, services/, utils/ directories exist) but routes act as controllers, serializers, and validators combined; no service or repository layer is actually used between routes and the ORM
Source files:  15 inspected (100% of non-generated Python source): app.py, database.py, seed.py, models/__init__.py, models/task.py, models/user.py, models/category.py, routes/__init__.py, routes/task_routes.py, routes/user_routes.py, routes/report_routes.py, services/__init__.py, services/notification_service.py, utils/__init__.py, utils/helpers.py
Persistence:   SQLite via SQLAlchemy ORM, file `tasks.db` created at app startup (app.py:11, app.py:30-31); no migration tool (no Alembic) — schema is created directly via `db.create_all()`
================================

## Evidence

- **Entry point:** `app.py:1-35` creates the Flask app, wires `SQLALCHEMY_DATABASE_URI`, `SECRET_KEY`, CORS, registers three blueprints (`task_bp`, `user_bp`, `report_bp`), defines `/health` and `/` routes inline, and calls `db.create_all()` at import time (module-level side effect, not gated behind `if __name__ == '__main__'`).
- **Data layer:** `models/task.py`, `models/user.py`, `models/category.py` define SQLAlchemy models with `to_dict()` serializers and some domain logic (`Task.is_overdue()`, `Task.validate_status()`, `Task.validate_priority()`, `User.set_password()`, `User.check_password()`, `User.is_admin()`). `database.py` holds the shared `db = SQLAlchemy()` singleton, imported by every model and by `app.py`.
- **Route layer:** `routes/task_routes.py` (10 endpoints under `/tasks*`), `routes/user_routes.py` (7 endpoints under `/users*` and `/login`), `routes/report_routes.py` (7 endpoints under `/reports*` and `/categories*`). All are Flask Blueprints registered in `app.py`. Route handlers directly call `Task.query`, `User.query`, `Category.query`, perform inline validation, build response dictionaries by hand in several places, and call `db.session.add/commit/rollback` directly.
- **Service layer (declared but unused):** `services/notification_service.py` defines `NotificationService` with `send_email`, `notify_task_assigned`, `notify_task_overdue`. Confirmed via project-wide search that `NotificationService` is never imported or instantiated outside its own file — it is dead code.
- **Utility layer (partially unused):** `utils/helpers.py` defines `format_date`, `calculate_percentage` (both actually imported and used by `routes/report_routes.py:7`), plus `validate_email`, `sanitize_string`, `generate_id`, `log_action`, `parse_date`, `is_valid_color`, `process_task_data`, and several `VALID_*`/`DEFAULT_*` constants — none of these are imported anywhere else in the project (confirmed by search); they duplicate logic re-implemented inline in the route files (e.g., email regex duplicated in `routes/user_routes.py:61`, status/priority validation duplicated in `routes/task_routes.py:110-114`, tag join logic duplicated in `routes/task_routes.py:141-144`).
- **Seed script:** `seed.py` imports `app` and `db` from `app.py`, wipes and repopulates `users`, `categories`, `tasks` tables. It executes `db.session.commit()` calls directly against models, no service layer involved.
- **Configuration:** No `.env`, `.gitignore`, or `config.py` found in the repository. `SECRET_KEY` (`app.py:13`) and SMTP credentials (`services/notification_service.py:9-10`) are hardcoded literals, not read from environment variables. `python-dotenv` is declared in `requirements.txt` but never imported or used anywhere.
- **Tests:** No test files, test directory, or test framework import found anywhere in the project (`unittest`/`pytest` search returned zero matches in application code).
- **README self-assessment:** `README.md:15-38` already contains a prior manual analysis (in Portuguese) covering hardcoded secrets/weak hashing, missing auth enforcement, N+1 queries, duplicated overdue logic, manual serialization duplication, and unused imports. This session's independent read of the source confirms these same conditions from the actual files; it is treated as a prior note to verify against, not as ground truth, and Phase 2 will re-derive severities and evidence directly from source.

## Architecture map

| Module / file | Responsibility observed | Notable dependencies |
| --- | --- | --- |
| `app.py` | App factory/bootstrap, config, blueprint registration, 2 inline routes, DB table creation at import time | `database.db`, all three route blueprints |
| `database.py` | Shared `SQLAlchemy()` instance | none (leaf) |
| `models/user.py` | User ORM model, password hashing (MD5, unsalted), role check, full-field serialization (including password hash) | `database.db`, `hashlib` |
| `models/task.py` | Task ORM model, serialization, status/priority validation, overdue check | `database.db` |
| `models/category.py` | Category ORM model, serialization | `database.db` |
| `routes/task_routes.py` | 10 endpoints: CRUD + search + stats for tasks; inline validation, inline serialization, inline overdue logic, direct `db.session` calls | `database.db`, `models.task/user/category` |
| `routes/user_routes.py` | 7 endpoints: CRUD for users, user tasks, login (no real token issuance/verification) | `database.db`, `models.user/task` |
| `routes/report_routes.py` | 7 endpoints: summary/user reports, category CRUD; heavy in-Python aggregation over query results | `database.db`, `models.task/user/category`, `utils.helpers` (2 of 9 functions used) |
| `services/notification_service.py` | Email notification logic — unused/dead code, hardcoded SMTP credentials | `smtplib` |
| `utils/helpers.py` | Grab-bag of validation/formatting helpers and constants — 2 of 9 functions used, rest dead code duplicated inline in routes | none |
| `seed.py` | One-off data seeding script, imports the whole app to reuse `db` | `app`, `models.*` |

## Constraints and uncertainties

- No test suite exists, so any Phase 3 refactor will need to rely on manual/boot/endpoint smoke checks rather than automated regression tests — this should be flagged as a validation risk in Phase 2's plan.
- No `.env` or environment-based config currently exists; introducing environment variables for secrets in Phase 3 changes operational setup (must be called out explicitly as a deployment-affecting change, not silently assumed).
- `tasks.db` is not present in the repository (git status shows no such file); it is created fresh via `seed.py` + `db.create_all()`, so no production data migration concern applies here — confirm this understanding before Phase 3 touches the schema.
- The README's existing "Analise manual" section overlaps heavily with what Phase 2's audit will independently document; Phase 2 will cite exact lines from source rather than deferring to the README text.
- `marshmallow` and `requests` are declared as dependencies but not imported anywhere in source — worth flagging as unused dependencies in Phase 2 rather than as an architecture finding.
