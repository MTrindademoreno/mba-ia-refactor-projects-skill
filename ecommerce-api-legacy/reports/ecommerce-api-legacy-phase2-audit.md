```
================================
ARCHITECTURE AUDIT REPORT
================================
Project:  ecommerce-api-legacy
Stack:    Node.js (CommonJS) / Express 4.18.2 / sqlite3 5.1.6 (in-memory)
Files:    3 source files (src/app.js, src/AppManager.js, src/utils.js) | ~182 lines total

Summary
CRITICAL: 3 | HIGH: 5 | MEDIUM: 4 | LOW: 5
================================
```

## Findings

### [CRITICAL] CS-009: Hardcoded secrets committed to source control
File: src/utils.js:1-7
Evidence: `config` hardcodes `dbPass: "senha_super_secreta_prod_123"` and `paymentGatewayKey: "pk_live_1234567890abcdef"` (a live-looking payment gateway key) directly in a file tracked by git, with no `.env` or secret-manager indirection anywhere in the repo.
Impact: Any repository access (or a public leak) exposes what looks like a production payment key and a database password; keys cannot be rotated without a code change and redeploy.
Recommendation: Move these values to environment variables (`process.env.DB_PASS`, `process.env.PAYMENT_GATEWAY_KEY`, etc.), read via `config`, and add a `.env.example` with placeholder keys. Do not commit real values.

### [CRITICAL] Insecure, reversible password "hashing"
File: src/utils.js:17-23; used at src/AppManager.js:68-71
Evidence: `badCrypto` is not a cryptographic hash — it base64-encodes the password 10,000 times and truncates the result to 10 characters (`hash += Buffer.from(pwd).toString('base64').substring(0, 2)`), which is deterministic, unsalted, and trivially invertible/collision-prone (10 chars drawn from a fixed base64 alphabet). It is used to store new users' passwords in `setupRoutes` → checkout's user-creation branch, and falls back to a hardcoded default password `"123456"` when none is supplied (`badCrypto(p || "123456")`).
Impact: User passwords are effectively stored in a weakly obfuscated, guessable form rather than a real one-way hash; any user created without a password silently gets the same well-known default credential.
Recommendation: Replace `badCrypto` with a standard one-way, salted hash (e.g., Node's built-in `crypto.scryptSync`/`crypto.randomBytes` for a salt, or `bcrypt`), and require a password on signup instead of silently defaulting it. Note: the seeded user (`AppManager.js:18`) stores its password as plain `'123'` already, so there is no existing hashed data to migrate.

### [CRITICAL] God Object: persistence, routing, and business logic combined in one class
File: src/AppManager.js:1-142
Evidence: A single `AppManager` class owns the raw DB connection (`this.db`, line 7), the full schema/seed definition (`initDb`, lines 10-23), and all three route registrations with inline request parsing, validation, payment "processing," and nested callback-based SQL for both writes and the report query (`setupRoutes`, lines 25-138). There is no router, controller, service, or repository module — every concern lives in one file and one class.
Impact: Matches this project's own severity criteria for a complete separation-of-concerns violation ("God Class contendo banco de dados, lógicas complexas e roteamento no mesmo arquivo"). Any change — a new route, a schema tweak, a validation rule — risks touching unrelated logic, and no part of the request-handling pipeline can be unit-tested without a live SQLite instance.
Recommendation: Split into a thin Express router/controller layer (request parsing + response shaping), a service layer (checkout flow, financial report aggregation), and a repository layer (per-entity SQL), wiring the SQLite connection through constructors instead of module-level/class-level ownership.

### [HIGH] Deleting a user orphans its enrollments and payments
File: src/AppManager.js:131-137
Evidence: `DELETE /api/users/:id` runs only `DELETE FROM users WHERE id = ?` and returns the message `"Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."` — the response text itself confirms `enrollments` and `payments` rows referencing the deleted user are left behind.
Impact: Produces orphaned rows that corrupt the financial report (`GET /api/admin/financial-report` would show `student: 'Unknown'` for orphaned enrollments) and any future analytics; there is no referential-integrity enforcement (no foreign keys, no cascade, no transaction).
Recommendation: Decide and implement an explicit deletion strategy — e.g., delete dependent `enrollments`/`payments` in the same transaction, or block deletion when dependent records exist, or soft-delete the user. This changes the endpoint's current (buggy) behavior, so the desired semantics need explicit confirmation before Phase 3 touches it.

### [HIGH] Checkout performs multiple dependent writes with no transaction
File: src/AppManager.js:50-63
Evidence: The checkout flow inserts an `enrollment` (line 50), then a `payment` (line 54), then an `audit_log` (line 57) as three sequential, independently-committed `db.run` calls with no `BEGIN`/`COMMIT`/`ROLLBACK` wrapper. If the payment or audit-log insert fails after the enrollment succeeds, the request errors out but the enrollment row remains committed.
Impact: A financial/domain-critical flow can leave a paying customer with a "phantom" enrollment and no payment record, or a payment without an audit trail, with no compensating action.
Recommendation: Wrap the three inserts in a single SQLite transaction (`BEGIN`/`COMMIT`, with `ROLLBACK` on any callback error) so the checkout either fully succeeds or fully rolls back.

### [HIGH] CS-003 — No dependency injection; `AppManager` owns its own DB connection
File: src/AppManager.js:4-8; src/app.js:8
Evidence: The constructor unconditionally creates `new sqlite3.Database(':memory:')` (line 7), and `src/app.js:8` instantiates `new AppManager()` directly with no way to supply a different connection, mock, or test double.
Impact: `AppManager` cannot be unit-tested or reused against a different database (e.g., a persistent SQLite file, or an in-memory DB per test) without patching the module internals.
Recommendation: Accept the DB connection (or a repository/service that wraps it) as a constructor parameter, with the concrete SQLite connection constructed once in the composition root (`app.js`) and injected in.

### [HIGH] CS-013 — Global mutable module state
File: src/utils.js:9, 14; used at src/AppManager.js:59
Evidence: `globalCache` is a module-level mutable object (line 9) written to by `logAndCache` (line 14) and called from the checkout handler (`logAndCache(\`last_checkout_${userId}\`, course.title)`, line 59) with no scoping, expiry, or encapsulation.
Impact: Shared mutable state across all requests makes behavior dependent on call order, is unsafe if the process ever handles concurrent requests against shared keys, and cannot be reset between tests.
Recommendation: Replace the module-level object with an injected cache instance (even a simple `Map` owned by the composition root) or remove it if it is not read anywhere in the current codebase (confirmed unread in the 3 inspected source files).

### [HIGH] CS-016 — Route handlers are untestable in isolation
File: src/AppManager.js:28-138
Evidence: Every route handler directly parses `req.body`/`req.params`, calls `this.db.*` inline, and writes the HTTP response from deep inside nested SQL callbacks (e.g., `res.status(200).json(...)` at line 60, four callback levels deep). There is no seam between "what should happen" (business rule) and "how it's persisted/returned."
Impact: No part of the checkout or report logic can be exercised without a running Express app and a live SQLite connection; this is consistent with the project having zero automated tests (confirmed absent in Phase 1).
Recommendation: Extract the checkout and report logic into plain functions/services that take already-validated input and a repository, returning a result the route handler then maps to an HTTP response — enabling unit tests without HTTP or a real DB.

### [MEDIUM] CS-011: N+1 query pattern in the financial report
File: src/AppManager.js:80-129
Evidence: For each course (line 89), the handler queries `enrollments` (line 92); for each enrollment, it queries `users` (line 104) and then `payments` (line 106) — i.e., 1 + N + (2×M) queries for N courses and M total enrollments, coordinated with manual pending-counters (`coursesPending`, `enrPending`) instead of `Promise.all`/joins.
Impact: Query count grows linearly with courses × enrollments; the manual counter-based completion tracking is also fragile (an error in any nested callback is silently swallowed — `err` is destructured but never checked at lines 92, 104, 106).
Recommendation: Replace the nested queries with a small number of batched queries (e.g., one join across `enrollments`, `users`, and `payments`, or `Promise.all` over per-course lookups) and check/handle errors at each step instead of discarding them.

### [MEDIUM] Checkout validation only checks presence, not shape
File: src/AppManager.js:29-35
Evidence: `if (!u || !e || !cid || !cc) return res.status(400).send("Bad Request");` validates that four fields are truthy but never validates email format, that `cid` is numeric, or that `cc` looks like a card number before it's used in `cc.startsWith("4")` (line 46) and logged verbatim (line 45).
Impact: Malformed input (e.g., a non-numeric `c_id`, or a `card` value that isn't card-shaped at all) is accepted and only fails later with a generic 404/500, and raw card-like input is logged to stdout in full (`console.log` at line 45), which is also a sensitive-data-in-logs concern.
Recommendation: Add explicit input validation (a validation library or manual checks) for type/shape before use, and stop logging the raw card value.

### [MEDIUM] CS-004: Long method with deep nesting in the checkout handler
File: src/AppManager.js:28-78
Evidence: The `/api/checkout` handler is ~50 lines with up to five levels of nested callbacks (route → course lookup → user lookup → `processPaymentAndEnroll` → enrollment insert → payment insert → audit insert), mixing input parsing, business rules, and persistence in one closure.
Impact: Hard to follow the control flow and error paths; easy to introduce bugs when modifying one branch without noticing effects on sibling callbacks.
Recommendation: Extract named steps (e.g., `findOrCreateUser`, `chargeCard`, `createEnrollmentAndPayment`) once the service/repository split from the God Object finding above is in place.

### [MEDIUM] In-memory database is recreated on every boot
File: src/AppManager.js:7, 10-23
Evidence: `new sqlite3.Database(':memory:')` combined with `initDb()` re-running `CREATE TABLE`/seed `INSERT` statements on every process start means all data (users, enrollments, payments, audit logs) is lost on restart and reset to the two hardcoded seed rows.
Impact: No durable data between restarts; this may be intentional for a demo/challenge boilerplate (confirmed as existing, seed-driven behavior in Phase 1), but it should be an explicit, approved decision rather than an incidental side effect of any refactor.
Recommendation: If persistence is desired, switch to a file-backed SQLite database (or another store) behind the same repository interface. Treat this as a scope decision for the user, not an automatic fix.

### [LOW] `src/utils.js` mixes unrelated concerns and exports dead code
File: src/utils.js:1-25
Evidence: One module exports static config, a mutable cache, a logger, and a password-hashing function together; `totalRevenue` (line 10, exported line 25) is never read or written anywhere else in the 3 inspected source files.
Impact: Reduced cohesion makes it unclear which consumer depends on which concern; the unused export is dead weight that can mislead readers into thinking it's used for revenue tracking.
Recommendation: Split into focused modules (`config.js`, `cache.js`, `logger.js`, `password.js`) as part of the broader restructuring, and drop `totalRevenue` if a final repo-wide check confirms it is unused.

### [LOW] Implicit bootstrap ordering
File: src/app.js:8-10
Evidence: `manager.initDb()` must run before `manager.setupRoutes(app)` for routes to see initialized tables, but this is only enforced by call order in `app.js`, not by any structural guarantee (e.g., an `async` factory that awaits DB readiness before returning the configured app).
Impact: A future edit that reorders these two lines (or moves `setupRoutes` into the constructor) would silently boot routes against an uninitialized schema.
Recommendation: Introduce a small `createApp()` factory that performs initialization and route setup in a fixed sequence and returns a ready-to-listen app, making the dependency explicit and testable.

### [LOW] CS-006 / CS-007: Cryptic parameter names and a magic string for card validation
File: src/AppManager.js:29-33, 46, 89, 102
Evidence: Request fields are destructured into single/double-letter names (`u`, `e`, `p`, `cid`, `cc` at lines 29-33; `c`, `enr` at lines 89, 102), and the mock payment approval rule is a bare literal: `cc.startsWith("4")` (line 46) with no named constant or comment explaining the "starts with 4 = Visa-like test card" convention.
Impact: Increases the effort needed to read and safely modify the checkout logic; the magic `"4"` prefix in particular is easy to misread as arbitrary rather than a deliberate (mock) card-network rule.
Recommendation: Rename to descriptive identifiers (`username`, `email`, `password`, `courseId`, `cardNumber`, `course`, `enrollment`) and extract the card check into a named constant/function (e.g., `isApprovedTestCard(cardNumber)`).

## Verified absence of findings

- **SQL injection:** every `db.run`/`db.get`/`db.all` call in `AppManager.js` uses parameterized `?` placeholders with an argument array (e.g., lines 37, 40, 50, 54, 57, 69, 83, 92, 104, 106, 133) — no string concatenation into SQL was found.
- **Deprecated APIs:** `express@4.18.2` and `sqlite3@5.1.6` (per `package-lock.json`) are current, supported major versions with no deprecated-API usage observed in the inspected code (standard `app.use`/`app.post` middleware, standard `sqlite3` callback API).

## Approved-scope proposal

1. Move hardcoded secrets in `src/utils.js` into environment variables, with a `.env.example` placeholder file (resolves the CRITICAL secrets finding).
2. Replace `badCrypto` with a real salted one-way hash and remove the silent default-password fallback (resolves the CRITICAL password-storage finding).
3. Split `AppManager` into a router/controller layer, a service layer (checkout, financial report), and a repository layer (users, courses, enrollments, payments, audit_logs), with the SQLite connection constructed once in `src/app.js` and injected in (resolves the God Object, tight-coupling, and untestable-code findings).
4. Wrap the checkout's enrollment/payment/audit-log inserts in a single DB transaction (resolves the non-transactional-checkout finding).
5. Replace the nested per-course/per-enrollment queries in the financial report with a batched approach and proper error handling (resolves the N+1 finding).
6. Extract an explicit `createApp()` bootstrap factory that sequences DB init and route setup (resolves the implicit-bootstrap-ordering finding).
7. Rename cryptic variables and extract the magic card-prefix check to a named constant/function; remove the unused `totalRevenue` export (resolves the two remaining LOW findings).

**Explicitly out of scope pending your decision:** the orphaned-records-on-user-delete behavior (finding above) changes an existing endpoint's contract — please confirm the desired semantics (cascade-delete dependents, block deletion when dependents exist, or soft-delete) before Phase 3 implements it. Likewise, switching the in-memory database to a persistent store is out of scope unless you confirm you want that behavior change; the default plan keeps `:memory:` as-is.

## Validation plan

- **Boot check:** `npm start` (or `node src/app.js`) — confirm the server starts on port 3000 without errors, same as today.
- **Manual smoke tests via `api.http`** (no automated test suite currently exists — this is the available validation surface):
  - `POST /api/checkout` success case (approved card) — expect `200` with `{ msg: "Sucesso", enrollment_id }`.
  - `POST /api/checkout` denied-card case — expect `400` with the denial message.
  - `GET /api/admin/financial-report` — expect the same aggregate shape (course/revenue/students) as before the refactor.
  - `DELETE /api/users/:id` — behavior to be re-validated against whatever deletion semantics you approve.
- **Regression risk note:** because there are no automated tests, behavior-preservation for the God Object split and transaction changes will rely entirely on the manual checks above; if you want stronger guarantees, adding a minimal test suite (e.g., `supertest` against the running app) could be proposed as an additional, separately-approved step.

Approval required: Do you approve this plan for Phase 3? Please also confirm the desired behavior for the user-delete endpoint (cascade / block / soft-delete) and whether the in-memory database should remain as-is.
