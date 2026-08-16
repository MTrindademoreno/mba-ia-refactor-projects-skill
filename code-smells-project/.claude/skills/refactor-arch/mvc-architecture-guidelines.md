# MVC Architecture Guidelines - Target Architecture Standards

Apply these principles rather than copying the Python or Node examples below. Preserve conventions required by the detected framework (for example, framework-managed routing, dependency injection, modules, or domain layers). MVC is a useful mapping for request-driven applications, not a mandatory directory structure for every project type.

Especificação do padrão MVC alvo para refatoração de projetos monolíticos. Este documento define o que é uma arquitetura MVC bem-estruturada, com responsabilidades claras e princípios SOLID aplicados.

## 1. Princípios Fundamentais

### Separação de Responsabilidades
- **Model**: Dados e lógica de negócio
- **View/Routes**: Definição de endpoints HTTP e serialização de response
- **Controller**: Orquestração de requisições e chamadas ao Model

### Princípios SOLID
- **S**ingle Responsibility: Cada classe tem UM motivo para mudar
- **O**pen/Closed: Aberto para extensão, fechado para modificação
- **L**iskov Substitution: Subtipos devem poder substituir tipos
- **I**nterface Segregation: Muitos clientes específicos > um contrato geral
- **D**ependency Inversion: Depender de abstrações, não de implementações

---

## 2. Estrutura de Diretórios (Canonical)

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
│   └── env.js               ← Variáveis de ambiente
│
├── models/
│   ├── User.js              ← Model User
│   ├── Product.js           ← Model Product
│   └── schemas.js           ← Validação (Joi, Yup, etc)
│
├── repositories/            ← Camada de acesso a dados
│   ├── BaseRepository.js
│   ├── UserRepository.js
│   └── ProductRepository.js
│
├── services/                ← Lógica de negócio
│   ├── UserService.js
│   ├── ProductService.js
│   └── OrderService.js
│
├── routes/
│   ├── index.js             ← Registro de rotas
│   ├── users.js             ← Rotas: GET/POST /users
│   ├── products.js          ← Rotas: GET/POST /products
│   └── orders.js            ← Rotas: GET/POST /orders
│
├── controllers/
│   ├── UserController.js    ← Handlers das rotas
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
├── app.js                   ← Composition Root
└── package.json
```

---

## 3. Responsabilidades por Camada

### Model Layer
**Responsabilidade:** Dados e regras de negócio

```python
# ✅ BOM: Model com responsabilidade clara
class User:
    def __init__(self, name: str, email: str, password: str):
        self.name = name
        self.email = email
        self.password = self._hash_password(password)  # Validação
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """Regra de negócio: hashear senha"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def is_valid_email(self) -> bool:
        """Validação de domínio"""
        return "@" in self.email
```

**O que NÃO faz:**
- ❌ Não faz queries diretas (vai no Repository)
- ❌ Não manipula Request/Response HTTP
- ❌ Não acessa banco de dados diretamente

---

### Repository Layer (NOVO em refatoração)
**Responsabilidade:** Persistência e queries

```python
# ✅ BOM: Repository com separação clara
from abc import ABC, abstractmethod

class UserRepository(ABC):
    @abstractmethod
    def find_by_id(self, user_id: int) -> Optional[User]:
        pass
    
    @abstractmethod
    def find_by_email(self, email: str) -> Optional[User]:
        pass
    
    @abstractmethod
    def save(self, user: User) -> User:
        pass

class SQLiteUserRepository(UserRepository):
    def __init__(self, db_connection):
        self.db = db_connection
    
    def find_by_id(self, user_id: int) -> Optional[User]:
        # Prepared statement (evita SQL injection)
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return self._map_to_user(row) if row else None
    
    def save(self, user: User) -> User:
        cursor = self.db.cursor()
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
            (user.name, user.email, user.password)
        )
        self.db.commit()
        return user
```

**O que faz:**
- ✅ Queries com prepared statements
- ✅ Mapping entre DB e objetos de domínio
- ✅ Abstração do tipo de banco (SQLite, PostgreSQL, etc)

**O que NÃO faz:**
- ❌ Lógica de negócio
- ❌ Validação de dados
- ❌ Orquestração de requisições

---

### Service Layer (NOVO em refatoração)
**Responsabilidade:** Lógica de negócio e orquestração

```python
# ✅ BOM: Service com DI e regras de negócio
class UserService:
    def __init__(self, user_repository: UserRepository):
        self.repository = user_repository
    
    def create_user(self, name: str, email: str, password: str) -> User:
        """Regra: email deve ser único"""
        existing = self.repository.find_by_email(email)
        if existing:
            raise ValueError(f"Email {email} já existe")
        
        user = User(name=name, email=email, password=password)
        return self.repository.save(user)
    
    def authenticate(self, email: str, password: str) -> Optional[User]:
        """Regra: validar credenciais"""
        user = self.repository.find_by_email(email)
        if not user:
            return None
        
        if user.password != User._hash_password(password):
            return None
        
        return user
```

**O que faz:**
- ✅ Implementa regras de negócio
- ✅ Orquestra múltiplos repositories
- ✅ Usa dependency injection

**O que NÃO faz:**
- ❌ Acessa banco direto
- ❌ Manipula HTTP requests
- ❌ Válida parametros HTTP

---

### Controller Layer
**Responsabilidade:** Orquestrar request/response

```python
# ✅ BOM: Controller delegando para Service
from flask import Blueprint, request, jsonify

users_bp = Blueprint('users', __name__, url_prefix='/users')

class UserController:
    def __init__(self, user_service: UserService):
        self.service = user_service
    
    def create(self):
        """POST /users - Criar usuário"""
        try:
            data = request.get_json()
            
            # Validação HTTP
            if not data or "email" not in data:
                return jsonify({"erro": "Email obrigatório"}), 400
            
            # Delegação para Service
            user = self.service.create_user(
                name=data.get("name"),
                email=data.get("email"),
                password=data.get("password")
            )
            
            return jsonify({
                "id": user.id,
                "email": user.email,
                "mensagem": "Usuário criado"
            }), 201
        
        except ValueError as e:
            return jsonify({"erro": str(e)}), 400
        except Exception as e:
            return jsonify({"erro": "Erro interno"}), 500
    
    def get_by_email(self, email: str):
        """GET /users/<email> - Obter usuário"""
        try:
            # Validação
            if not email:
                return jsonify({"erro": "Email inválido"}), 400
            
            # Delegação
            user = self.service.get_user(email)
            if not user:
                return jsonify({"erro": "Usuário não encontrado"}), 404
            
            return jsonify({"email": user.email, "nome": user.name}), 200
        
        except Exception as e:
            return jsonify({"erro": "Erro interno"}), 500
```

**O que faz:**
- ✅ Valida parâmetros HTTP
- ✅ Serializa response JSON
- ✅ Delega lógica para Service
- ✅ Trata exceções e retorna status HTTP correto

**O que NÃO faz:**
- ❌ Acessa banco direto
- ❌ Implementa lógica de negócio
- ❌ Valida regras de domínio

---

### View/Routes Layer
**Responsabilidade:** Definir endpoints e desserializar input

```python
# ✅ BOM: Routes limpas, delegando para Controllers
from flask import Blueprint
from controllers.user_controller import UserController

def create_user_routes(user_service: UserService):
    users_bp = Blueprint('users', __name__, url_prefix='/users')
    controller = UserController(user_service)
    
    @users_bp.route('', methods=['POST'])
    def create():
        return controller.create()
    
    @users_bp.route('/<email>', methods=['GET'])
    def get(email: str):
        return controller.get_by_email(email)
    
    return users_bp
```

**O que faz:**
- ✅ Define rotas e métodos HTTP
- ✅ Desserializa query parameters
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
[Repository] - Acessa dados (prepared statements)
    ↓
[Model] - Objeto de domínio (validações)
    ↓
[Database] - Executa query
    ↓
[Response] - Controller serializa, retorna JSON
    ↓
HTTP Response
```

---

## 5. Dependency Injection Pattern

### Composition Root (app.py)
```python
# ✅ BOM: Centralized DI setup
from flask import Flask
from config.database import get_db
from repositories.user_repository import SQLiteUserRepository
from services.user_service import UserService
from controllers.user_controller import UserController
from views.user_routes import create_user_routes

def create_app():
    app = Flask(__name__)
    
    # Database
    db = get_db()
    
    # Repositories
    user_repository = SQLiteUserRepository(db)
    
    # Services
    user_service = UserService(user_repository)
    
    # Controllers
    # (Passed to routes factory)
    
    # Routes
    user_routes = create_user_routes(user_service)
    app.register_blueprint(user_routes)
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=False, host="0.0.0.0", port=5000)
```

**Benefícios:**
- ✅ Fácil testar (mock dependencies)
- ✅ Fácil trocar implementações (SQLite → PostgreSQL)
- ✅ Código desacoplado

---

## 6. Testing Strategy

### Unit Tests (Service Layer)
```python
import pytest
from services.user_service import UserService
from unittest.mock import Mock

def test_create_user_with_duplicate_email():
    """Service deve rejeitar email duplicado"""
    mock_repo = Mock()
    mock_repo.find_by_email.return_value = Mock()  # Simula usuário existente
    
    service = UserService(mock_repo)
    
    with pytest.raises(ValueError, match="já existe"):
        service.create_user("John", "john@test.com", "pass123")
```

### Integration Tests (Repository Layer)
```python
def test_user_repository_save_and_retrieve():
    """Repository deve salvar e recuperar usuário"""
    db = sqlite3.connect(":memory:")
    repo = SQLiteUserRepository(db)
    
    user = User("John", "john@test.com", "hashed_pass")
    saved = repo.save(user)
    
    retrieved = repo.find_by_id(saved.id)
    assert retrieved.email == "john@test.com"
```

### API Tests (Controller Layer)
```python
def test_create_user_endpoint():
    """POST /users deve criar usuário"""
    app = create_app()
    client = app.test_client()
    
    response = client.post('/users', json={
        "name": "John",
        "email": "john@test.com",
        "password": "pass123"
    })
    
    assert response.status_code == 201
    assert response.json["email"] == "john@test.com"
```

---

## 7. Error Handling Strategy

### Custom Exceptions
```python
# ✅ BOM: Exceções específicas de domínio
class BusinessRuleException(Exception):
    """Base para exceções de negócio"""
    pass

class DuplicateEmailException(BusinessRuleException):
    """Email já registrado"""
    pass

class UserNotFoundException(BusinessRuleException):
    """Usuário não encontrado"""
    pass
```

### Exception Handling in Controller
```python
# ✅ BOM: Traduzir exceções para HTTP
class UserController:
    def create(self):
        try:
            user = self.service.create_user(...)
            return jsonify({...}), 201
        
        except DuplicateEmailException as e:
            return jsonify({"erro": str(e)}), 409  # Conflict
        except BusinessRuleException as e:
            return jsonify({"erro": str(e)}), 400  # Bad Request
        except Exception as e:
            logger.error(f"Erro inesperado: {e}")
            return jsonify({"erro": "Erro interno do servidor"}), 500
```

---

## 8. Configuration Management

### ✅ BOM: Environment-based
```python
# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DEBUG = os.getenv("DEBUG", "False") == "True"
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///app.db")
    SECRET_KEY = os.getenv("SECRET_KEY")  # Obrigatório em produção
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")

settings = Settings()
```

### ❌ RUIM: Hardcoded
```python
# ❌ EVITAR
DEBUG = True
SECRET_KEY = "my-secret-123"
DATABASE_URL = "sqlite:///app.db"
```

---

## 9. Validation Strategy

### Input Validation (Controller/Routes)
```python
# ✅ BOM: Pydantic/Marshmallow schemas
from pydantic import BaseModel, EmailStr, validator

class CreateUserSchema(BaseModel):
    name: str
    email: EmailStr
    password: str
    
    @validator('password')
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError('Senha deve ter 8+ caracteres')
        return v

# Na rota
def create_user(self):
    try:
        data = CreateUserSchema(**request.get_json())
        # Data já validada
    except ValidationError as e:
        return jsonify({"erro": e.errors()}), 400
```

### Business Rule Validation (Service)
```python
# ✅ BOM: Regras de negócio no Service
class UserService:
    def create_user(self, name: str, email: str, password: str):
        # Validação de regra de negócio
        if self.repository.find_by_email(email):
            raise DuplicateEmailException("Email já existe")
        
        user = User(name, email, password)
        return self.repository.save(user)
```

---

## 10. Summary Table: Before & After

| Aspect | ❌ Before (Monolithic God Class) | ✅ After (MVC + SOLID) |
|--------|----------------------------------|----------------------|
| **File Structure** | Tudo em app.py (500+ linhas) | Separado em camadas |
| **Database Access** | Direto no Controller | Via Repository |
| **Business Logic** | Espalhado (Model + Controller) | Centralizado em Service |
| **Dependencies** | Diretas e acopladas | Injetadas e abstratas |
| **Testing** | Impossível testar isolado | Unit/integration/API fácil |
| **Manutenção** | Difícil (risco alto) | Fácil (baixo risco) |
| **Reuso de Código** | Difícil (tudo misturado) | Fácil (separação clara) |
| **Security** | Vulnerável (concatenação SQL) | Seguro (prepared statements) |

