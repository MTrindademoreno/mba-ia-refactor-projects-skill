# Refactoring Playbook - Transformation Patterns

Every pattern below is written as **neutral pseudocode**, not real syntax from any language. Angle brackets (`<like_this>`) mark a placeholder you fill in with the idiom of the project's actual language, framework, and driver/ORM — identified during Phase 1 (see `analysis-heuristics.md`) — never with Python, Flask, SQLite, or the example domain names used here. If the detected stack has its own established idiom for a transformation (e.g. an ORM's native eager-loading feature, a framework's own DI container, a language's standard env-config loader), prefer that idiom over a literal reading of the pseudocode.

Each pattern gives:
- **Sinal de detecção:** the structural/semantic signal to look for in the source, independent of syntax.
- **Invariante pós-fix:** what must stay true after the change (contract, inputs/outputs, response shape) unless the Approved-scope proposal explicitly calls out a contract change.
- **Antes/Depois em pseudocódigo:** the shape of the transformation.
- **Como aplicar na stack detectada:** how to translate the pseudocode into the project's real language and libraries.

---

## Pattern 1: CS-008/009 - SQL/Command Injection Fix

**Sinal de detecção:** A query or shell command string is built by concatenating or interpolating a value that originates from request/user input, instead of passing that value through the driver's or ORM's parameter-binding mechanism.

**Invariante pós-fix:** Same query, same result set, same function signature and response shape — only the construction mechanism changes.

### ❌ Antes
```
function find_by_id(id):
    query = "SELECT * FROM <table> WHERE id = " + to_string(id)
    row = execute(query)
    return row
end function
```

### ✅ Depois
```
function find_by_id(id):
    query = "SELECT * FROM <table> WHERE id = " + <driver_bind_placeholder>
    row = execute(query, params = [id])
    return row
end function
```

**Como aplicar na stack detectada:**
- Identify the exact binding syntax of the detected driver/ORM (e.g. positional `?`, named `:id`, numbered `$1`, or an ORM query-builder call) and use it for every concatenated value, not just the one shown in the finding.
- If the stack has an ORM already in use elsewhere in the project, prefer its query builder over a raw parameterized string.

---

## Pattern 2: CS-001 - Duplicated Validation

**Sinal de detecção:** The same set of validation rules (required fields, bounds, formats) is written more than once across different entry points (e.g. a "create" and an "update" handler).

**Invariante pós-fix:** Every entry point rejects the same invalid inputs, with the same error contract, as before.

### ❌ Antes
```
function create_item(input):
    if input.name is missing: return error("name required")
    if input.price < 0: return error("price must be >= 0")
    ...
end function

function update_item(id, input):
    if input.name is missing: return error("name required")
    if input.price < 0: return error("price must be >= 0")
    ...
end function
```

### ✅ Depois
```
function validate_item(input):
    errors = []
    if input.name is missing: errors.add("name required")
    if input.price < 0: errors.add("price must be >= 0")
    return errors
end function

function create_item(input):
    errors = validate_item(input)
    if errors is not empty: return error(errors)
    ...
end function

function update_item(id, input):
    errors = validate_item(input)
    if errors is not empty: return error(errors)
    ...
end function
```

**Como aplicar na stack detectada:**
- Reuse whatever validation mechanism is already idiomatic for the stack (a schema/DTO type, a validation library already in the project's dependencies, or a plain shared function) — introduce a new validation library only if the project has none and the plan calls for it.

---

## Pattern 3: CS-002 - God Object / Large Class

**Sinal de detecção:** One class, module, or file owns request handling plus more than one unrelated business concern (e.g. user management + payments + reporting + notifications) — it has many independent reasons to change.

**Invariante pós-fix:** Same endpoints, same request/response shapes; only internal ownership of the logic changes.

### ❌ Antes
```
class UserController:
    function create_user(request):
        ... validation ...
        ... db query ...
        ... send_email ...   # unrelated concern
    end function

    function sales_report(request):
        ...                  # unrelated concern
    end function

    function process_payment(request):
        ...                  # unrelated concern
    end function
end class
```

### ✅ Depois
```
class UserService:
    function create_user(name, email, password):
        ...
        notification_service.send_welcome(email)
        return user
    end function
end class

class NotificationService: ... end class
class PaymentService: ... end class
class ReportService: ... end class

class UserController:
    function create(request):
        user = user_service.create_user(request.name, request.email, request.password)
        return respond(201, user)
    end function
end class
```

**Como aplicar na stack detectada:**
- Split by responsibility into one service/module per concern; the controller/handler only orchestrates and translates request ⇄ response.
- In non-class-based languages, use the equivalent unit of organization (a module, package, or set of functions with a clear single concern) instead of a class.

---

## Pattern 4: CS-003 - Tight Coupling (No Dependency Injection)

**Sinal de detecção:** A module reaches a concrete global/singleton dependency directly (e.g. a module-level database handle) instead of receiving it as a parameter or injected dependency, making substitution or isolated testing impossible.

**Invariante pós-fix:** Same runtime behavior; only how the dependency is obtained changes.

### ❌ Antes
```
global_db = connect_to_database()

function get_all_users():
    return global_db.query("SELECT * FROM users")
end function
```

### ✅ Depois
```
class UserRepository:
    function __init__(db_connection):
        this.db = db_connection
    end function

    function get_all():
        return this.db.query("SELECT * FROM users")
    end function
end class

# composition root
db = connect_to_database()
user_repository = new UserRepository(db)
```

**Como aplicar na stack detectada:**
- Use whatever dependency-injection mechanism is idiomatic for the stack: constructor injection, a factory function, or the framework's own DI container if it has one. Do not introduce a DI framework the project doesn't already use unless the approved plan calls for it.

---

## Pattern 5: CS-009/010 - Hardcoded Secrets & Exposed Config

**Sinal de detecção:** A credential or secret literal is written directly in source, and/or a diagnostic/health endpoint returns configuration or secret values in its response body.

**Invariante pós-fix:** Same runtime behavior once the environment supplies the value. Removing secret fields from a response body changes that endpoint's contract — flag it explicitly in the Approved-scope proposal rather than assuming it's in scope.

### ❌ Antes
```
config.secret_key = "literal-secret-value"
config.debug = true

function health_check():
    return respond(200, { status: "ok", secret_key: config.secret_key, debug: config.debug })
end function
```

### ✅ Depois
```
config.secret_key = read_env("SECRET_KEY")          # fail fast if missing
config.debug = read_env("DEBUG", default = false)

function health_check():
    return respond(200, { status: "ok", version: "1.0.0" })   # no secret/config leaked
end function
```

**Como aplicar na stack detectada:**
- Use the stack's standard configuration mechanism identified in Phase 1 (environment variables, a framework-native config/secrets file, a secrets manager already in use) — do not invent a `.env`/dotenv convention for a stack that already has its own idiom (e.g. a framework-native `application.yml`, credentials store, or config module).

---

## Pattern 6: CS-011 - N+1 Query Problem

**Sinal de detecção:** A loop over a collection issues one additional query per iteration to fetch related data, instead of a single batched or joined fetch.

**Invariante pós-fix:** Same aggregate result shape; only the number and shape of the underlying queries changes.

### ❌ Antes
```
orders = execute("SELECT * FROM orders")
result = []
for order in orders:
    user = execute("SELECT * FROM users WHERE id = ?", [order.user_id])
    items = execute("SELECT * FROM order_items WHERE order_id = ?", [order.id])
    result.add({ order, user, items })
end for
```

### ✅ Depois
```
rows = execute("""
    SELECT o.*, u.*, i.*
    FROM orders o
    LEFT JOIN users u ON o.user_id = u.id
    LEFT JOIN order_items i ON o.id = i.order_id
""")
result = group_rows_by_order(rows)
```

**Como aplicar na stack detectada:**
- Prefer the ORM's native eager-loading feature if the project already uses an ORM (e.g. a `with`/`include`/`joinedload`-style option); otherwise use a single joined query or a batched `WHERE id IN (...)` follow-up query instead of a query-per-iteration loop.

---

## Pattern 7: CS-013 - Global State / Singletons

**Sinal de detecção:** A module-level mutable variable holds a shared resource (connection, cache, counter) that every caller reads or mutates directly by reference to the module, rather than through an injected instance.

**Invariante pós-fix:** Same behavior in production (one shared instance for the app's lifetime); tests instead get isolated instances.

### ❌ Antes
```
shared_connection = null

function get_connection():
    if shared_connection is null:
        shared_connection = open_connection()
    end if
    return shared_connection
end function
```

### ✅ Depois
```
class ConnectionProvider:
    function __init__(url):
        this.url = url
        this.connection = null
    end function

    function connect():
        this.connection = open_connection(this.url)
        return this.connection
    end function
end class

# composition root: create exactly one instance for the running app
provider = new ConnectionProvider(config.database_url)
provider.connect()
# tests: create a separate instance per test, fully isolated from the app's instance
```

**Como aplicar na stack detectada:**
- Replace the module-level global with an instance created once at the application's composition root (entry point) and passed down to whatever needs it; use the stack's own app-lifecycle hooks (e.g. a teardown/shutdown hook) to close it if one exists.

---

## Summary: Transformation Checklist

```
PHASE 3 REFACTORING CHECKLIST

SECURITY
  [ ] Remove query/command string concatenation (use parameter binding)
  [ ] Remove hardcoded secrets (use the stack's environment/config mechanism)
  [ ] Sanitize error responses (no internal details, stack traces, or secrets)
  [ ] Add input validation at every entry point that lacks it

ARCHITECTURE
  [ ] Extract a data-access layer (repository or equivalent)
  [ ] Extract a business-logic layer (service or equivalent)
  [ ] Apply dependency injection instead of module-level globals
  [ ] Create or clarify a single composition root (entry point)

CODE QUALITY
  [ ] Extract duplicated validation into one shared function/schema
  [ ] Split God Objects/God Modules by responsibility
  [ ] Remove global mutable state
  [ ] Extract magic values into named constants

TESTING
  [ ] Confirm the project's existing test framework/mocking approach (do not introduce a new one unless none exists)
  [ ] Add or update unit tests for the extracted business-logic layer
  [ ] Add or update integration tests for the extracted data-access layer
  [ ] Add or update endpoint/API tests for the request-handling layer

CONFIGURATION
  [ ] Move hardcoded config to the stack's environment/config mechanism
  [ ] Centralize configuration reading in one module
  [ ] Confirm secrets are excluded from version control (check existing ignore file)

DOCUMENTATION
  [ ] Document the new structure in the Phase 3 report
  [ ] Update the project README if its documented structure changed
  [ ] Document remaining follow-up work and unresolved findings
```
