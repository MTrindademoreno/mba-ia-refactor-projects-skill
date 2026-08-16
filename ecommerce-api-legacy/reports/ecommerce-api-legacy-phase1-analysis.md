```
================================
PHASE 1: PROJECT ANALYSIS
================================
Project:       ecommerce-api-legacy (package name: desafio-arquitetura-ia-boilerplate)
Language(s):   JavaScript (Node.js, CommonJS)
Framework(s):  Express ^4.18.2
Runtime:       Node.js, package manager npm (package-lock.json, lockfileVersion 3)
Dependencies:  express ^4.18.2, sqlite3 ^5.1.6 (no dev dependencies, no test framework, no linter/formatter configured)
Domain:        Course/e-commerce checkout API — the README labels it an "LMS API (com fluxo de checkout)"; it exposes checkout, an admin financial report, and user deletion for a course-enrollment platform
Architecture:  Single-class monolith — one `AppManager` God Object owns DB init, all three route handlers, and inline business logic; no separation between routing, controller, service, or persistence layers
Source files:  4 inspected (src/app.js, src/AppManager.js, src/utils.js) + package.json, package-lock.json, README.md, api.http
Persistence:   SQLite, in-memory (`new sqlite3.Database(':memory:')`), schema and seed data recreated on every boot via raw SQL in `initDb()`
================================
```

## Evidence

- **Entry point:** `src/app.js:1-14` — creates the Express app, instantiates `AppManager`, calls `manager.initDb()` then `manager.setupRoutes(app)` in sequence (implicit ordering, no composition root), and starts the HTTP listener on `config.port`.
- **Core logic:** `src/AppManager.js:1-142` — a single class with:
  - `constructor` (lines 4-8): opens a global in-memory SQLite connection as an instance field.
  - `initDb()` (lines 10-23): raw `CREATE TABLE` statements for `users`, `courses`, `enrollments`, `payments`, `audit_logs`, plus hardcoded `INSERT` seed data.
  - `setupRoutes(app)` (lines 25-138): registers three routes directly inline, each containing full request parsing, validation, business rules, and nested callback-based SQL calls in a single closure.
- **Configuration/cross-cutting module:** `src/utils.js:1-25` — exports a `config` object with hardcoded secrets (`dbPass`, `paymentGatewayKey`), a mutable `globalCache` object, an unused `totalRevenue` counter, a `logAndCache` logger, and a custom `badCrypto` password-hashing function (non-cryptographic, base64-based).
- **Manifests:** `package.json` declares only `start: node src/app.js`; no test script, no build step, no linter. `package-lock.json` confirms npm as the package manager and pins transitive dependency versions consistent with `sqlite3`'s native-binding install chain.
- **Tests:** none found — no `test/`, `tests/`, `*.test.js`, or `*.spec.js` files, and no test framework listed in `package.json`.
- **API surface (from `AppManager.js` route registrations and `api.http`):**
  - `POST /api/checkout` — creates/looks up a user, validates a course, "processes" a card, creates an enrollment, a payment, and an audit log, all as separate sequential SQL statements.
  - `GET /api/admin/financial-report` — builds a nested per-course/per-enrollment report using manually tracked pending counters instead of `Promise`-based aggregation.
  - `DELETE /api/users/:id` — deletes a user row only; the handler's own response text admits related `enrollments`/`payments` rows are left orphaned.
- **Deployment signals:** none — no Dockerfile, no CI config, no environment-specific config files (`.env`, `config/*.yml`) found; all configuration is hardcoded in `src/utils.js`.

## Architecture map

| Module | Responsibility (as implemented) | Notable dependencies |
| --- | --- | --- |
| `src/app.js` | Composition root / boot: creates Express app, wires JSON body parsing, instantiates and drives `AppManager` lifecycle, starts listener | `express`, `./AppManager`, `./utils` (`config`) |
| `src/AppManager.js` | Simultaneously: DB schema owner, seed loader, router, controller, validator, and data-access layer for all three endpoints | `sqlite3`, `./utils` (`config`, `logAndCache`, `badCrypto`, `totalRevenue`) |
| `src/utils.js` | Grab-bag: static config/secrets, in-process cache, logging, and a hand-rolled hashing function | none (leaf module) |

There is no models/views/controllers separation, no service or repository layer, and no dependency injection — `AppManager` constructs its own DB connection internally, and the Express `app` instance is passed into `setupRoutes` rather than routes being mounted from a router module.

## Constraints and uncertainties

- The database is in-memory only (`:memory:`), so all data is lost on every restart; this is an existing, seed-driven behavior and not something to silently "fix" as persistence without explicit approval, since it may be intentional for a demo/challenge boilerplate.
- No automated tests exist, so any refactor's behavior-preservation can only be validated through manual smoke checks (`api.http` requests) and boot verification, not a regression suite — this should be flagged as a validation risk in Phase 2/3.
- `src/utils.js` exports `globalCache` and `totalRevenue`, but only `logAndCache` (which mutates `globalCache`) is actually used by `AppManager`; `totalRevenue` appears unused in the inspected files — worth confirming with a repo-wide reference check before removal in Phase 3.
- Secrets in `config` (`dbPass`, `paymentGatewayKey`) are hardcoded in source and committed to version control; no `.env` or secret-management mechanism exists. This is a security-relevant fact for Phase 2, not yet a proposed fix.
- The README's "Analise manual" section already documents five findings (orphaned deletes, non-transactional checkout, in-memory DB reset, mixed-concern `utils.js`, implicit bootstrap order) written by a prior manual review; Phase 2's audit should independently verify and cross-reference these rather than assume they are exhaustive or still accurate.
