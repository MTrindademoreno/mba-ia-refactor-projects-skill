================================
ARCHITECTURE AUDIT REPORT
================================
Project:  task-manager-api
Stack:    Python 3, Flask 3.0.0, Flask-SQLAlchemy 3.1.1, SQLite

Files:    15 inspected Python source files (~1,050 lines total across app.py, database.py, seed.py, models/*, routes/*, services/*, utils/*)

Summary
CRITICAL: 2 | HIGH: 4 | MEDIUM: 3 | LOW: 2
================================

## Findings

### [CRITICAL] CS-009-a: Hardcoded secrets committed to source code
File: app.py:13, services/notification_service.py:9-10
Evidence: `app.config['SECRET_KEY'] = 'super-secret-key-123'` (app.py:13) and `self.email_user = 'taskmanager@gmail.com'` / `self.email_password = 'senha123'` (services/notification_service.py:9-10) are literal strings in version-controlled files. No `.env`, `.gitignore`, or `os.getenv` usage exists anywhere in the project (confirmed by search), even though `python-dotenv` is already declared in requirements.txt:6 and unused.
Impact: Flask's `SECRET_KEY` signs session cookies; anyone with repository access can forge sessions. SMTP credentials are exposed the same way. Rotating either requires a code change and a new deploy rather than a config update.
Recommendation: Load both values with `os.getenv(...)`, keep non-secret local defaults only for `SECRET_KEY` in development, and require the SMTP credentials to be set via environment/secret manager with no source fallback.

### [CRITICAL] CS-009-b: Unsalted MD5 password hashing, with the hash returned by the API
File: models/user.py:27-32 (hashing), models/user.py:16-25 (serialization), routes/user_routes.py:33, :85, :129, :209 (endpoints that return it)
Evidence: `set_password`/`check_password` use `hashlib.md5(pwd.encode()).hexdigest()` with no salt (models/user.py:27-32). `User.to_dict()` includes `'password': self.password` (models/user.py:21). That dict is returned as-is by `get_user` (user_routes.py:33), `create_user` (user_routes.py:85), `update_user` (user_routes.py:129), and `login` (user_routes.py:209). Note: `get_users` (user_routes.py:14-24) builds its response manually and does **not** include the password field — only the four endpoints above expose it.
Impact: MD5 is not a password-hashing algorithm (no salt, fast to brute-force/rainbow-table); combined with the hash being exposed over the API on four endpoints, an attacker who can read any single API response can offline-crack user passwords.
Recommendation: Hash with `werkzeug.security.generate_password_hash`/`check_password_hash` (already a transitive Flask dependency, no new package needed) and drop the `password` key from `User.to_dict()` entirely (add a separate internal accessor only if a caller genuinely needs the hash).

### [HIGH] AUTHN-01: No route enforces authentication or authorization
File: routes/user_routes.py:185-211 (login), routes/task_routes.py (all routes), routes/user_routes.py (all routes except login), routes/report_routes.py (all routes)
Evidence: `login` issues `'token': 'fake-jwt-token-' + str(user.id)` (user_routes.py:210) — a predictable, unsigned string. No route in any of the three blueprints reads an `Authorization` header, validates that token, or calls `User.is_admin()` to gate access, even though `is_admin()` already exists (models/user.py:34-38) and roles (`admin`/`manager`/`user`) are stored on every user.
Impact: Every list, create, update, and delete endpoint for tasks, users, categories, and reports is reachable by any unauthenticated client. The role model exists in the domain but has no enforcement point.
Recommendation: Introduce a real token (e.g., signed JWT or server-side session) issued at login, and a decorator/before_request hook that validates it and enforces `is_admin()`/role checks on the routes that need them. This changes the current (currently absent) access-control contract, so confirm the intended auth scheme before implementing.

### [HIGH] CS-003: Routes perform persistence, validation, and serialization directly with no service/repository boundary
File: routes/task_routes.py (all 10 handlers), routes/user_routes.py (all 7 handlers), routes/report_routes.py (all 7 handlers)
Evidence: Every route function calls `Model.query`/`db.session.add/commit/rollback` directly, re-implements validation inline (e.g., status/priority checks duplicated at task_routes.py:110-114 and :181-184), and builds response payloads by hand in several places (task_routes.py:16-59, user_routes.py:161-181) instead of going through a dedicated layer. The `services/` directory exists but its only module (`NotificationService`) is never invoked; there is no repository or service abstraction between routes and the ORM.
Impact: Business rules (validation, overdue calculation, serialization) are copy-pasted across blueprints rather than owned by one component, so every change has to be applied consistently by hand across up to six call sites (see CS-001 findings below); route handlers cannot be unit-tested without a live Flask/DB context.
Recommendation: Introduce a thin service layer (e.g., `services/task_service.py`, `services/user_service.py`) that owns validation, persistence, and `to_dict()`-based serialization; have route handlers only translate HTTP <-> service calls.

### [HIGH] CS-010: Debug mode enabled with public bind address
File: app.py:34
Evidence: `app.run(debug=True, host='0.0.0.0', port=5000)`. Flask's debug mode surfaces full stack traces and source snippets in error responses and enables the interactive Werkzeug debugger; `host='0.0.0.0'` binds it to every network interface rather than localhost.
Impact: If this configuration reaches any non-trusted network, internal paths, source code, and variable state are exposed in error pages (matches catalog CS-010: "stack traces com paths do sistema" / "detalhes internos em error messages").
Recommendation: Gate `debug` on an environment variable defaulting to `False`, and default `host` to `127.0.0.1` unless an explicit deployment need requires otherwise.

### [HIGH] CS-014: Broad `except:` clauses swallow errors on write operations
File: task_routes.py:62, task_routes.py:236, user_routes.py:130, user_routes.py:149, report_routes.py:186, report_routes.py:207, report_routes.py:221
Evidence: Seven handlers catch with a bare `except:` and no logging — e.g. `delete_task` (task_routes.py:231-238), `update_user` (user_routes.py:127-132), `delete_user` (user_routes.py:144-151), and all three category mutations (report_routes.py:182-188, :204-209, :217-223) — returning only a generic `{'error': '...'}` with no record of the underlying exception. This is inconsistent with `create_task`, `update_task`, and `create_user`, which do `except Exception as e:` and `print(...)` the message.
Impact: When these seven operations fail for any reason other than the anticipated one, the actual cause is discarded; operators cannot diagnose failures from logs, and the inconsistency (some routes log, some don't) makes the error-handling behavior of the API unpredictable.
Recommendation: Standardize on `except Exception as e:` with structured logging (or a shared error-handling decorator) across every route that touches `db.session`.

### [MEDIUM] CS-011: N+1 queries in three read endpoints
File: routes/task_routes.py:41-57, routes/report_routes.py:53-68, routes/report_routes.py:157-165
Evidence: `get_tasks` issues one extra `User.query.get(...)` and one extra `Category.query.get(...)` per task inside its loop (task_routes.py:41-57), even though `Task.user` and `Task.category` are already mapped `relationship()`s (models/task.py:20-21). `summary_report`'s `user_stats` loop issues one `Task.query.filter_by(user_id=u.id).all()` per user (report_routes.py:53-68). `get_categories` issues one `Task.query.filter_by(category_id=c.id).count()` per category (report_routes.py:157-165).
Impact: Query count scales linearly with the number of tasks/users/categories returned, so these three endpoints get slower as the dataset grows even though the same data could be fetched with eager loading or a single aggregate query.
Recommendation: Use `Task.query.options(joinedload(Task.user), joinedload(Task.category))` for `get_tasks`, and replace the per-row `.filter_by(...)` calls in the report endpoints with grouped aggregate queries (e.g. `db.session.query(Task.user_id, func.count()).group_by(Task.user_id)`).

### [MEDIUM] CS-001-a: The "overdue" business rule is duplicated in six places instead of reusing `Task.is_overdue()`
File: models/task.py:50-60 (canonical), task_routes.py:30-39, task_routes.py:71-80, task_routes.py:283-287, user_routes.py:171-180, report_routes.py:33-38, report_routes.py:132-135
Evidence: `Task.is_overdue()` already implements the check (models/task.py:50-60), but the same `if due_date and due_date < utcnow() and status not in ('done','cancelled')` logic is hand-written again in `get_tasks`, `get_task`, `task_stats`, `get_user_tasks`, `summary_report`, and `user_report`.
Impact: A future change to the rule (e.g., a grace-period, or a new terminal status) requires editing six call sites; missing one silently produces inconsistent `overdue` values between endpoints.
Recommendation: Call `task.is_overdue()` from every one of these six sites instead of re-deriving the condition.

### [MEDIUM] CS-001-b: Task serialization is manually rebuilt instead of reusing `Task.to_dict()`
File: routes/task_routes.py:16-59 (get_tasks), routes/user_routes.py:161-181 (get_user_tasks)
Evidence: Both handlers construct a `task_data` dict field-by-field that duplicates `Task.to_dict()` (models/task.py:23-36), with divergences between the two: `get_user_tasks`'s dict omits `user_id`, `category_id`, and `tags` that `to_dict()`/`get_tasks` include.
Impact: Any field added to, removed from, or renamed in `Task.to_dict()` must be remembered and re-applied in these two places by hand, and the two endpoints already disagree on the response shape for what is nominally "a task".
Recommendation: Call `task.to_dict()` and merge in only the endpoint-specific extra fields (`overdue`, `user_name`, `category_name`) rather than re-listing every column.

### [LOW] CS-006/unused-imports: Unused imports across three modules
File: routes/task_routes.py:7, routes/user_routes.py:6, utils/helpers.py:3-7
Evidence: `import json, os, sys, time` (task_routes.py:7) — none of the four names are referenced anywhere in the file. `import hashlib, json, re` (user_routes.py:6) — `hashlib` and `json` are never referenced (password hashing lives in `User`; `re` is used for the email regex at line 61). `import os, json, sys, math, hashlib` (utils/helpers.py:3-7) — none of the five are referenced in the file.
Impact: Unused imports obscure which dependencies a module actually needs and signal the code hasn't had a incremental lint/cleanup pass.
Recommendation: Remove the unused names from each import statement.

### [LOW] DEAD-CODE-01: An unused notification service and most of `utils/helpers.py` are dead code
File: services/notification_service.py:1-49, utils/helpers.py:19-116 (all functions/constants except `format_date` and `calculate_percentage`)
Evidence: Project-wide search confirms `NotificationService` is never imported or instantiated outside its own file. Of the nine functions and five constants defined in `utils/helpers.py`, only `format_date` and `calculate_percentage` are imported (by report_routes.py:7); `validate_email`, `sanitize_string`, `generate_id`, `log_action`, `parse_date`, `is_valid_color`, `process_task_data`, and the `VALID_*`/`DEFAULT_*`/`MIN_*`/`MAX_*` constants are unreferenced anywhere, while equivalent logic (email regex, tag-join, status/priority checks) is instead hand-duplicated inline in the route files.
Impact: ~120 lines of code that look load-bearing (a "service", a "helpers" module) are not actually exercised, which misleads readers about what the running application depends on and adds surface area with no functional payoff.
Recommendation: Either delete the unused class/functions, or — where they duplicate inline logic already in the routes (e.g., `validate_email` vs. the regex in user_routes.py:61) — wire the routes to call them instead of removing them, as part of the CS-001/CS-003 consolidation above.

## Approved-scope proposal

All steps are behavior-preserving except step 3, which changes the current (currently nonexistent) access-control behavior and should be confirmed explicitly before implementation.

1. Move `SECRET_KEY`, the SQLite URI, and the SMTP credentials to environment variables (`os.getenv`, using `python-dotenv` which is already an unused dependency), keeping only a non-secret local default for `SECRET_KEY` in development. — resolves CS-009-a
2. Replace MD5 password hashing with `werkzeug.security.generate_password_hash`/`check_password_hash`, and remove the `password` field from `User.to_dict()`. — resolves CS-009-b
3. Add token-based authentication (validate a real token on protected routes, enforce `User.is_admin()`/role checks where appropriate) — pending confirmation of the intended scheme, since this is the one change that alters current client-facing behavior. — resolves AUTHN-01
4. Extract a service layer (`services/task_service.py`, `services/user_service.py`, `services/category_service.py`) that owns validation and persistence; route handlers call the service and only translate HTTP in/out. — resolves CS-003
5. Route every serialization through `Task.to_dict()`/`User.to_dict()`/`Category.to_dict()` and every overdue check through `Task.is_overdue()`, removing the duplicated inline logic. — resolves CS-001-a, CS-001-b
6. Fix the three N+1 read paths with eager loading / grouped aggregate queries. — resolves CS-011
7. Gate `debug`/`host` in `app.run()` behind environment variables defaulting to safe values. — resolves CS-010
8. Standardize the seven bare `except:` blocks to `except Exception as e:` with logging. — resolves CS-014
9. Remove unused imports (task_routes.py:7, user_routes.py:6, utils/helpers.py:3-7) and either delete or wire up the dead `NotificationService`/`utils/helpers.py` functions. — resolves the two LOW findings

## Validation plan

- Boot check: `python app.py` starts without error and `GET /health` returns 200 (no automated tests exist in the project today — confirmed by search — so this and the checks below are the available validation surface).
- `python seed.py` completes successfully after the password-hashing change (it calls `User.set_password`) and after any service-layer extraction (it calls the models directly today, so keep that path working or update it to use the new service).
- Manual/curl smoke test of every endpoint in `routes/task_routes.py`, `routes/user_routes.py`, and `routes/report_routes.py` before and after each step, comparing response shape and status codes (expected diffs: `password` no longer present in user responses after step 2; new 401/403 responses after step 3).
- `python -m py_compile` (or equivalent import check) on every changed file to catch syntax/import errors from the cleanup in step 9.

Approval required: Do you approve this plan for Phase 3?
