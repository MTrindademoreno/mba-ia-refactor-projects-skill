================================
PHASE 3: REFACTORING COMPLETE
================================
Target architecture: Layered Flask app (routes → services → models), keeping the existing `models/`, `routes/`, `services/`, `utils/` directories and adding a `config/` module for environment-driven settings.

## Changed structure
```
config/
  __init__.py        (new)
  settings.py         (new — SECRET_KEY, DATABASE_URL, DEBUG, HOST, PORT read via os.getenv/python-dotenv)
app.py                 (changed — uses config.settings instead of inline literals; adds logging.basicConfig)
models/user.py         (changed — werkzeug password hashing, password dropped from to_dict())
models/task.py          (changed — removed unused `import json`)
routes/task_routes.py   (changed — thin HTTP layer, delegates to services.task_service; no per-route try/except)
routes/user_routes.py   (changed — thin HTTP layer, delegates to services.user_service; no per-route try/except)
routes/report_routes.py (changed — thin HTTP layer, delegates to services.report_service / category_service; no per-route try/except)
services/task_service.py     (new — task validation, persistence, serialization)
services/user_service.py     (new — user validation, persistence, serialization, login)
services/category_service.py (new — category validation, persistence, serialization)
services/report_service.py   (new — summary/user report aggregation)
services/errors.py           (new — ServiceError(message, status_code))
services/notification_service.py (deleted — dead code, never invoked)
utils/helpers.py       (changed — trimmed to format_date, calculate_percentage, validate_email; the rest was unreferenced dead code)
```

## Changes made
- CS-009-a: `SECRET_KEY` and `DATABASE_URL` now load from environment variables via `config/settings.py` (`os.getenv` + `python-dotenv`), with a non-secret local default for `SECRET_KEY` only (`config/settings.py:6-7`); `app.py:17-19` reads from `settings` instead of hardcoding. The SMTP credentials that were hardcoded in `services/notification_service.py:9-10` no longer exist — the file was dead code and was deleted rather than migrated to env vars (see DEAD-CODE-01 below).
- CS-009-b: `models/user.py` now hashes with `werkzeug.security.generate_password_hash`/`check_password_hash` instead of unsalted MD5, and `User.to_dict()` no longer includes the `password` key at all.
- CS-003: Extracted `services/task_service.py`, `services/user_service.py`, `services/category_service.py`, `services/report_service.py`. Every route in `task_routes.py`, `user_routes.py`, `report_routes.py` now only parses the request, calls one service function, and translates the result/`ServiceError` into a JSON response — no route touches `db.session`/`Model.query` directly anymore.
- CS-001-a: All overdue checks now call `task.is_overdue()` (`services/task_service.py:60,83,234`; `services/report_service.py:32,134`; `services/user_service.py:160`) instead of re-deriving the condition inline.
- CS-001-b: Task/user/category serialization goes through `to_dict()` everywhere, with endpoint-specific extras merged in on top (e.g. `_serialize_task_summary` in `services/task_service.py:58-63` adds `overdue`, `user_name`, `category_name` to `task.to_dict()`).
- CS-011: `services/task_service.list_tasks()` uses `Task.query.options(joinedload(Task.user), joinedload(Task.category))` (`services/task_service.py:68-70`) instead of one extra query per task. `services/report_service.summary_report()` replaced the per-user task query with two grouped aggregate queries (`db.session.query(Task.user_id, func.count(Task.id)).group_by(...)`, `services/report_service.py:50-60`). `services/category_service.list_categories()` replaced the per-category count query the same way (`services/category_service.py:15-19`).
- CS-010: `app.py:40` now runs with `debug=settings.DEBUG` (default `False`) and `host=settings.HOST` (default `127.0.0.1`), both overridable via environment variables.
- CS-014: All seven bare `except:` blocks were replaced with `except Exception as e:` plus `logger.error(...)` calls across `services/task_service.py`, `services/user_service.py`, `services/category_service.py` (grep-verified: 10 `except Exception as e:` occurrences across the three service modules, all paired with a rollback + log call on write operations).
- CS-006 / unused imports: `routes/task_routes.py`, `routes/user_routes.py`, `routes/report_routes.py`, and `models/task.py` no longer import `json`, `os`, `sys`, `time`, or `hashlib` — each module now imports only what it uses.
- DEAD-CODE-01: `services/notification_service.py` was deleted (never invoked anywhere). `utils/helpers.py` was trimmed from 9 functions/5 constants to the 3 actually used (`format_date`, `calculate_percentage`, and `validate_email`, the last of which is now wired into `services/user_service._require_valid_email` instead of being dead).
- Error-handling centralization (follow-up identified after the initial Phase 3 pass, within the already-approved CS-003 scope): `app.py` now registers a single `@app.errorhandler(ServiceError)` (`app.py:29-31`) that converts any `ServiceError` raised by a service call into `jsonify({'error': error.message}), error.status_code`. All 15 previously duplicated `try: ... except ServiceError as e: return jsonify({'error': e.message}), e.status_code` blocks were removed from `routes/task_routes.py`, `routes/user_routes.py`, and `routes/report_routes.py` — every route handler now just calls its service function directly. Behavior is unchanged: Flask dispatches an uncaught `ServiceError` to the registered handler, producing the same status code and body as before.

## Not implemented (deferred by design)
- AUTHN-01 (no route enforces authentication/authorization): **not changed**. `services/user_service.login()` still returns the same unsigned `'fake-jwt-token-' + str(user.id)` (`services/user_service.py:188`), and no route validates an `Authorization` header or calls `User.is_admin()`. The Phase 2 plan flagged this as the one step that changes current client-facing behavior and required explicit scope confirmation before implementation; that confirmation was not given, so it was left out of this pass to keep Phase 3 behavior-preserving. This remains an open, high-severity gap.

## Validation
| Check | Command or method | Result |
| --- | --- | --- |
| Import/syntax check | `python -m py_compile app.py config/*.py database.py seed.py models/*.py routes/*.py services/*.py utils/helpers.py` | pass — all files compile |
| Boot check | `python -c "import app"` | pass — app module imports and initializes without error |
| Endpoint smoke test | `flask.test_client()`: `GET /health`, `GET /tasks`, `GET /tasks/999999` (not found), `GET /users`, `GET /reports/summary`, `POST /login` (bad credentials), `POST /tasks` (empty body) | pass — `/health` 200, `/tasks` 200 (10 items), `/tasks/999999` 404 via the centralized error handler, `/users` 200 (3 items, no `password` key present), `/reports/summary` 200, `/login` with wrong credentials 401 via the centralized error handler, `/tasks` with empty body 400 via the centralized error handler |
| No automated test suite | n/a | not run: project has no test framework or test files (confirmed in Phase 1); the smoke test above is the available validation surface |

## Remaining risks and follow-up
- AUTHN-01 is unresolved: every endpoint (tasks, users, categories, reports) is still reachable without authentication. This should be prioritized as the next change, with the token scheme (JWT vs. session) confirmed explicitly before implementation since it changes client-facing behavior.
- `marshmallow` and `requests` remain declared in `requirements.txt` with no corresponding usage found anywhere in the codebase (noted in Phase 1); left untouched since removing dependencies was outside the approved Phase 2 scope.
================================
