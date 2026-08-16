# MVC Architecture Guidelines - Target Architecture Standards

Apply these principles rather than copying the directory trees or pseudocode below verbatim. Preserve conventions required by the detected framework (for example, framework-managed routing, dependency injection, modules, or domain layers). MVC is a useful mapping for request-driven applications, not a mandatory directory structure for every project type. Code samples in this document are **neutral pseudocode**, not real syntax — translate them into the project's actual language, framework, and libraries as identified in Phase 1.

Especificação do padrão MVC alvo para refatoração de projetos monolíticos. Este documento define o que é uma arquitetura MVC bem-estruturada, com responsabilidades claras e princípios SOLID aplicados.

## 1. Princípios Fundamentais

### Separação de Responsabilidades
- **Model**: Dados e lógica de negócio
- **View/Routes**: Definição de endpoints HTTP e serialização de response
- **Controller**: Orquestração de requisições e chamadas ao Model

### Princípios SOLID
- **S**ingle Responsibility: Cada classe/módulo tem UM motivo para mudar
- **O**pen/Closed: Aberto para extensão, fechado para modificação
- **L**iskov Substitution: Subtipos devem poder substituir tipos
- **I**nterface Segregation: Muitos contratos específicos > um contrato geral
- **D**ependency Inversion: Depender de abstrações, não de implementações

---

## 2. Estrutura de Diretórios

### Camadas (language-neutral)

| Camada | Responsabilidade |
| --- | --- |
| `config/` | Configuração (env-based), inicialização de recursos externos (BD, filas, etc.) |
| `models/` | Dados e regras de domínio |
| `repositories/` | Acesso a dados (queries, persistência), isolado atrás de uma interface |
| `services/` | Lógica de negócio e orquestração entre repositories |
| `views/`, `routes/` | Definição de endpoints e (des)serialização de request/response |
| `controllers/` | Tradução request/response ⇄ chamadas ao service |
| `middlewares/` | Preocupações transversais: erro, autenticação, validação |
| `utils/` | Funções utilitárias sem estado |
| `tests/` | Testes unitários, de integração e de API |
| entry point / composition root | Monta e injeta todas as dependências |

As duas árvores abaixo (Python/Flask e Node/Express) são **duas realizações possíveis** dessa tabela, não a única forma correta. Para outra stack (Java/Spring, Go, Ruby/Rails, .NET, etc.), mapeie as mesmas camadas para a convenção de diretório/pacote nativa daquele ecossistema — por exemplo, Spring costuma organizar por feature/pacote em vez de por camada, e Go costuma usar `internal/` com pacotes por domínio; não force a árvore abaixo sobre esses ecossistemas.

### Para Projetos Python/Flask

```
src/
├── config/
│   ├── __init__.py
│   ├── settings.py          ← Configurações (env-based)
│   └── database.py          ← Inicialização do BD
│
├── models/
│   ├── __init__.py
│   ├── user.py              ← Model User (dados + validação)
│   ├── product.py           ← Model Product
│   └── schemas.py           ← Validação com Pydantic/Marshmallow
│
├── repositories/            ← NOVO: Camada de acesso a dados
│   ├── __init__.py
│   ├── base_repository.py   ← Classe base
│   ├── user_repository.py   ← Queries do usuário
│   └── product_repository.py ← Queries de produtos
│
├── services/                ← NOVO: Lógica de negócio
│   ├── __init__.py
│   ├── user_service.py      ← Lógica de usuários
│   ├── product_service.py   ← Lógica de produtos
│   └── order_service.py     ← Lógica de pedidos
│
├── views/
│   ├── __init__.py
│   ├── user_routes.py       ← Rotas: GET/POST /users
│   ├── product_routes.py    ← Rotas: GET/POST /products
│   └── order_routes.py      ← Rotas: GET/POST /orders
│
├── controllers/
│   ├── __init__.py
│   ├── user_controller.py   ← Handlers das rotas de user
│   ├── product_controller.py ← Handlers das rotas de product
│   └── order_controller.py  ← Handlers das rotas de order
│
├── middlewares/
│   ├── __init__.py
│   ├── error_handler.py     ← Tratamento de exceções
│   ├── auth.py              ← Autenticação/autorização
│   └── validation.py        ← Validação de input
│
├── utils/
│   ├── __init__.py
│   ├── decorators.py        ← Decoradores reutilizáveis
│   ├── exceptions.py        ← Classes de exceção
│   └── helpers.py           ← Funções utilitárias
│
├── tests/
│   ├── __init__.py
│   ├── unit/                ← Testes unitários
│   ├── integration/         ← Testes de integração
│   └── conftest.py          ← Fixtures pytest
│
├── app.py                   ← Composition Root (inicialização da app)
└── requirements.txt
```

### Para Projetos Node/Express

```
src/
├── config/
│   ├── index.js             ← Configurações
│   ├── database.js          ← Inicialização do BD
│   └── env.js                ← Variáveis de ambiente
│
├── models/
│   ├── User.js               ← Model User
│   ├── Product.js            ← Model Product
│   └── schemas.js            ← Validação (Joi, Yup, etc)
│
├── repositories/             ← Camada de acesso a dados
│   ├── BaseRepository.js
│   ├── UserRepository.js
│   └── ProductRepository.js
│
├── services/                 ← Lógica de negócio
│   ├── UserService.js
│   ├── ProductService.js
│   └── OrderService.js
│
├── routes/
│   ├── index.js               ← Registro de rotas
│   ├── users.js                ← Rotas: GET/POST /users
│   ├── products.js             ← Rotas: GET/POST /products
│   └── orders.js               ← Rotas: GET/POST /orders
│
├── controllers/
│   ├── UserController.js
│   ├── ProductController.js
│   └── OrderController.js
│
├── middleware/
│   ├── errorHandler.js
│   ├── auth.js
│   └── validation.js
│
├── utils/
│   ├── decorators.js
│   ├── exceptions.js
│   └── helpers.js
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── setup.js
│
├── app.js                    ← Composition Root
└── package.json
```

---

## 3. Responsabilidades por Camada

### Model Layer
**Responsabilidade:** Dados e regras de negócio

```
class User:
    function __init__(name, email, password):
        this.name = name
        this.email = email
        this.password = hash_password(password)   # regra de negócio
    end function

    function is_valid_email():
        return this.email contains "@"
    end function
end class
```

**O que NÃO faz:**
- ❌ Não faz queries diretas (vai no Repository)
- ❌ Não manipula Request/Response HTTP
- ❌ Não acessa banco de dados diretamente

---

### Repository Layer (NOVO em refatoração)
**Responsabilidade:** Persistência e queries

```
interface UserRepository:
    function find_by_id(user_id) -> User or null
    function find_by_email(email) -> User or null
    function save(user) -> User
end interface

class SqlUserRepository implements UserRepository:
    function __init__(db_connection):
        this.db = db_connection
    end function

    function find_by_id(user_id):
        row = this.db.query("SELECT * FROM users WHERE id = <bind>", [user_id])
        return row is not null ? map_to_user(row) : null
    end function

    function save(user):
        this.db.execute(
            "INSERT INTO users (name, email, password) VALUES (<bind>, <bind>, <bind>)",
            [user.name, user.email, user.password]
        )
        return user
    end function
end class
```

**O que faz:**
- ✅ Queries com parâmetros vinculados (nunca concatenação de string)
- ✅ Mapeamento entre linhas do BD e objetos de domínio
- ✅ Abstração do tipo de banco (troca de implementação sem afetar o Service)

**O que NÃO faz:**
- ❌ Lógica de negócio
- ❌ Validação de dados
- ❌ Orquestração de requisições

---

### Service Layer (NOVO em refatoração)
**Responsabilidade:** Lógica de negócio e orquestração

```
class UserService:
    function __init__(user_repository):
        this.repository = user_repository
    end function

    function create_user(name, email, password):
        # Regra: email deve ser único
        existing = this.repository.find_by_email(email)
        if existing is not null:
            raise error("email already exists")
        end if

        user = new User(name, email, password)
        return this.repository.save(user)
    end function

    function authenticate(email, password):
        user = this.repository.find_by_email(email)
        if user is null or not user.check_password(password):
            return null
        end if
        return user
    end function
end class
```

**O que faz:**
- ✅ Implementa regras de negócio
- ✅ Orquestra múltiplos repositories
- ✅ Recebe dependências injetadas (não instancia recursos globais)

**O que NÃO faz:**
- ❌ Acessa banco direto
- ❌ Manipula HTTP requests
- ❌ Valida parâmetros HTTP

---

### Controller Layer
**Responsabilidade:** Orquestrar request/response

```
class UserController:
    function __init__(user_service):
        this.service = user_service
    end function

    function create(request):
        data = parse_json(request.body)

        # Validação HTTP
        if data is null or data.email is missing:
            return respond(400, { error: "email required" })
        end if

        # Delegação para Service
        try:
            user = this.service.create_user(data.name, data.email, data.password)
            return respond(201, { id: user.id, email: user.email, message: "user created" })
        on_error DuplicateEmailError as e:
            return respond(409, { error: e.message })
        on_error UnexpectedError as e:
            return respond(500, { error: "internal error" })
        end try
    end function
end class
```

**O que faz:**
- ✅ Valida parâmetros HTTP
- ✅ Serializa a resposta
- ✅ Delega lógica para Service
- ✅ Traduz exceções de domínio em status HTTP

**O que NÃO faz:**
- ❌ Acessa banco direto
- ❌ Implementa lógica de negócio
- ❌ Valida regras de domínio

---

### View/Routes Layer
**Responsabilidade:** Definir endpoints e desserializar input

```
function create_user_routes(user_service):
    controller = new UserController(user_service)

    route POST "/users" -> controller.create(request)
    route GET  "/users/<email>" -> controller.get_by_email(request)

    return route_group
end function
```

**O que faz:**
- ✅ Define rotas e métodos HTTP
- ✅ Desserializa parâmetros de rota/query
- ✅ Delega para Controllers

**O que NÃO faz:**
- ❌ Lógica de negócio
- ❌ Acesso a dados direto

---

## 4. Fluxo de Requisição (MVC Correto)

```
HTTP Request
    ↓
[Routes] - Identifica endpoint
    ↓
[Controller] - Valida input HTTP, delega
    ↓
[Service] - Implementa regra de negócio, orquestra
    ↓
[Repository] - Acessa dados (parâmetros vinculados)
    ↓
[Model] - Objeto de domínio (validações)
    ↓
[Database] - Executa query
    ↓
[Response] - Controller serializa, retorna
    ↓
HTTP Response
```

---

## 5. Dependency Injection Pattern

### Composition Root (entry point)
```
function create_app():
    app = new_application()

    # Database
    db = connect_to_database(config.database_url)

    # Repositories
    user_repository = new SqlUserRepository(db)

    # Services
    user_service = new UserService(user_repository)

    # Routes (controller is created inside, or injected the same way)
    user_routes = create_user_routes(user_service)
    app.register(user_routes)

    return app
end function

app = create_app()
app.run(host = "0.0.0.0", port = 5000, debug = false)
```

**Benefícios:**
- ✅ Fácil testar (mock dependencies)
- ✅ Fácil trocar implementações (ex.: um banco por outro)
- ✅ Código desacoplado

**Como aplicar na stack detectada:** use o mecanismo de DI já idiomático da stack — injeção via construtor, uma factory function, ou o container de DI do próprio framework, se ele tiver um. Não introduza um framework de DI novo que o projeto não usa, a menos que o plano aprovado peça isso.

---

## 6. Testing Strategy

### Unit Tests (Service Layer)
```
test "create_user rejects a duplicate email":
    mock_repository = mock(UserRepository)
    mock_repository.find_by_email.returns(existing_user)

    service = new UserService(mock_repository)

    assert service.create_user("John", "john@test.com", "pass123") raises DuplicateEmailError
end test
```

### Integration Tests (Repository Layer)
```
test "repository saves and retrieves a user":
    db = open_in_memory_database()
    repository = new SqlUserRepository(db)

    user = new User("John", "john@test.com", "hashed_pass")
    saved = repository.save(user)

    retrieved = repository.find_by_id(saved.id)
    assert retrieved.email == "john@test.com"
end test
```

### API Tests (Controller Layer)
```
test "POST /users creates a user":
    app = create_app()
    client = test_client(app)

    response = client.post("/users", body = { name: "John", email: "john@test.com", password: "pass123" })

    assert response.status == 201
    assert response.body.email == "john@test.com"
end test
```

**Como aplicar na stack detectada:** confirme o framework de teste e a biblioteca de mocking que o projeto já usa (Phase 1 deve ter identificado isso) e escreva os testes nesse framework; só introduza um framework de teste novo se o projeto não tiver nenhum.

---

## 7. Error Handling Strategy

### Exceções de Domínio
```
class BusinessRuleError extends Error: end class
class DuplicateEmailError extends BusinessRuleError: end class
class UserNotFoundError extends BusinessRuleError: end class
```

### Tratamento no Controller
```
class UserController:
    function create(request):
        try:
            user = this.service.create_user(...)
            return respond(201, user)
        on_error DuplicateEmailError as e:
            return respond(409, { error: e.message })
        on_error BusinessRuleError as e:
            return respond(400, { error: e.message })
        on_error UnexpectedError as e:
            log_error(e)
            return respond(500, { error: "internal error" })
        end try
    end function
end class
```

**Como aplicar na stack detectada:** use o mecanismo de exceções/erros nativo da linguagem (classes de exceção, tipos de erro, ou `Result`/`Either` em linguagens que preferem retorno explícito de erro) e o middleware/handler de erro central que o framework já oferece, em vez de repetir o mesmo bloco try/catch em cada handler.

---

## 8. Configuration Management

### ✅ BOM: Baseado em variáveis de ambiente
```
# config module
load_environment()

class Settings:
    secret_key = read_env("SECRET_KEY")
    if secret_key is missing:
        raise error("SECRET_KEY not configured")
    end if

    debug = read_env("DEBUG", default = false)
    database_url = read_env("DATABASE_URL", default = "sqlite:///app.db")
    log_level = read_env("LOG_LEVEL", default = "INFO")
end class
```

### ❌ RUIM: Hardcoded
```
debug = true
secret_key = "my-secret-123"
database_url = "sqlite:///app.db"
```

**Como aplicar na stack detectada:** use o mecanismo de configuração nativo da stack (variáveis de ambiente lidas de forma idiomática, um arquivo de config nativo do framework, ou um cofre de segredos já em uso) — não assuma um arquivo `.env` se a stack já tem uma convenção própria de configuração.

---

## 9. Validation Strategy

### Input Validation (Controller/Routes)
```
schema CreateUserSchema:
    name: string, required
    email: string, required, format = email
    password: string, required, min_length = 8
end schema

function create_user(request):
    result = validate(request.body, CreateUserSchema)
    if result.has_errors:
        return respond(400, { errors: result.errors })
    end if
    # dados já validados em result.data
end function
```

### Business Rule Validation (Service)
```
class UserService:
    function create_user(name, email, password):
        if this.repository.find_by_email(email) is not null:
            raise DuplicateEmailError("email already exists")
        end if

        user = new User(name, email, password)
        return this.repository.save(user)
    end function
end class
```

**Como aplicar na stack detectada:** use a biblioteca de validação/schema já presente nas dependências do projeto (ou o recurso equivalente nativo da linguagem); introduza uma biblioteca nova só se o projeto não tiver nenhuma e o plano aprovado incluir essa mudança.

---

## 10. Summary Table: Before & After

| Aspect | ❌ Before (Monolithic God Class) | ✅ After (MVC + SOLID) |
|--------|----------------------------------|----------------------|
| **File Structure** | Tudo em um único arquivo de entrada | Separado em camadas |
| **Database Access** | Direto no Controller | Via Repository |
| **Business Logic** | Espalhado (Model + Controller) | Centralizado em Service |
| **Dependencies** | Diretas e acopladas | Injetadas e abstratas |
| **Testing** | Impossível testar isolado | Unit/integration/API fácil |
| **Manutenção** | Difícil (risco alto) | Fácil (baixo risco) |
| **Reuso de Código** | Difícil (tudo misturado) | Fácil (separação clara) |
| **Security** | Vulnerável (concatenação de query) | Seguro (parâmetros vinculados) |
