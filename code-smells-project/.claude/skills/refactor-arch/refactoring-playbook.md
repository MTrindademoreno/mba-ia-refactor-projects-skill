# Refactoring Playbook - Transformation Patterns & Code Examples

Treat the code examples as conceptual transformations. Reimplement them with the target project's language, standard library, framework, data layer, and error-handling conventions; never introduce Python, Flask, SQLite, or example domain names into an unrelated project.

Padrões concretos de refatoração para cada anti-pattern detectado, com exemplos de código antes/depois.

---

## Pattern 1: CS-008/009 - SQL Injection Fix

### ❌ ANTES: Vulnerable SQL Concatenation
```python
# models.py
def get_produto_por_id(id):
    db = get_db()
    cursor = db.cursor()
    # 🚨 CRÍTICO: SQL Injection vulnerability
    cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
    row = cursor.fetchone()
    if row:
        return {
            "id": row["id"],
            "nome": row["nome"],
            "preco": row["preco"]
        }
    return None

# controllers.py
def buscar_produto(id):
    try:
        produto = models.get_produto_por_id(id)  # ← Vulnerable
        if produto:
            return jsonify({"dados": produto, "sucesso": True}), 200
        else:
            return jsonify({"erro": "Produto não encontrado"}), 404
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
```

### ✅ DEPOIS: Parameterized Queries
```python
# repositories/produto_repository.py
from abc import ABC, abstractmethod
from typing import Optional, List

class ProdutoRepository(ABC):
    @abstractmethod
    def find_by_id(self, produto_id: int) -> Optional[dict]:
        pass

class SQLiteProdutoRepository(ProdutoRepository):
    def __init__(self, db_connection):
        self.db = db_connection
    
    def find_by_id(self, produto_id: int) -> Optional[dict]:
        cursor = self.db.cursor()
        # ✅ SECURE: Parameterized query (prepared statement)
        cursor.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
        row = cursor.fetchone()
        
        if row:
            return {
                "id": row["id"],
                "nome": row["nome"],
                "preco": row["preco"],
                "estoque": row["estoque"]
            }
        return None

# services/produto_service.py
class ProdutoService:
    def __init__(self, produto_repository: ProdutoRepository):
        self.repository = produto_repository
    
    def get_produto(self, produto_id: int) -> Optional[dict]:
        # Validação de tipo
        if not isinstance(produto_id, int) or produto_id <= 0:
            raise ValueError("ID inválido")
        
        return self.repository.find_by_id(produto_id)

# controllers/produto_controller.py
class ProdutoController:
    def __init__(self, produto_service: ProdutoService):
        self.service = produto_service
    
    def buscar_produto(self, produto_id: int):
        try:
            # Validação HTTP
            if not str(produto_id).isdigit():
                return jsonify({"erro": "ID deve ser número"}), 400
            
            # Delegação para Service
            produto = self.service.get_produto(int(produto_id))
            
            if not produto:
                return jsonify({"erro": "Produto não encontrado"}), 404
            
            return jsonify({"dados": produto, "sucesso": True}), 200
        
        except ValueError as e:
            return jsonify({"erro": str(e)}), 400
        except Exception as e:
            return jsonify({"erro": "Erro interno"}), 500

# routes/produto_routes.py
from flask import Blueprint

def create_produto_routes(produto_service):
    bp = Blueprint('produtos', __name__, url_prefix='/produtos')
    controller = ProdutoController(produto_service)
    
    @bp.route('/<int:produto_id>', methods=['GET'])
    def get_produto(produto_id):
        return controller.buscar_produto(produto_id)
    
    return bp
```

**Mudanças Principais:**
- ✅ Separou repository pattern (abstração de dados)
- ✅ Prepared statements com `?` placeholders
- ✅ Validação separada por camada
- ✅ Tipo esperado (int) para ID

---

## Pattern 2: CS-001 - Duplicated Code (Validation)

### ❌ ANTES: Código duplicado em múltiplos controllers
```python
# controllers.py

def criar_produto():
    try:
        dados = request.get_json()
        
        # ❌ DUPLICADO: Validação repetida
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400
        if "nome" not in dados:
            return jsonify({"erro": "Nome é obrigatório"}), 400
        if "preco" not in dados:
            return jsonify({"erro": "Preço é obrigatório"}), 400
        if "estoque" not in dados:
            return jsonify({"erro": "Estoque é obrigatório"}), 400
        
        # Mesma validação aqui...
        nome = dados["nome"]
        preco = dados["preco"]
        estoque = dados["estoque"]
        
        if preco < 0:
            return jsonify({"erro": "Preço não pode ser negativo"}), 400
        if estoque < 0:
            return jsonify({"erro": "Estoque não pode ser negativo"}), 400
        if len(nome) < 2:
            return jsonify({"erro": "Nome muito curto"}), 400
        
        # ... rest of code

def atualizar_produto(id):
    try:
        dados = request.get_json()
        
        # ❌ MESMA VALIDAÇÃO REPETIDA AQUI
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400
        if "nome" not in dados:
            return jsonify({"erro": "Nome é obrigatório"}), 400
        # ... todo repetido novamente
```

### ✅ DEPOIS: Schema validation centralizado
```python
# schemas/produto_schema.py
from pydantic import BaseModel, validator, Field
from typing import Optional

class CreateProdutoSchema(BaseModel):
    nome: str = Field(..., min_length=2, max_length=200)
    descricao: Optional[str] = ""
    preco: float = Field(..., gt=0)  # Greater than 0
    estoque: int = Field(..., ge=0)  # Greater or equal 0
    categoria: str = "geral"
    
    @validator('preco')
    def preco_precision(cls, v):
        # Máximo 2 casas decimais
        if len(str(v).split('.')[-1]) > 2:
            raise ValueError("Preço com máximo 2 casas decimais")
        return v
    
    @validator('categoria')
    def categoria_valida(cls, v):
        validas = ["informatica", "moveis", "vestuario", "geral", "eletronicos"]
        if v not in validas:
            raise ValueError(f"Categoria inválida. Válidas: {validas}")
        return v

class UpdateProdutoSchema(CreateProdutoSchema):
    # Mesma validação que Create
    pass

# controllers/produto_controller.py
from pydantic import ValidationError

class ProdutoController:
    def __init__(self, produto_service: ProdutoService):
        self.service = produto_service
    
    def criar_produto(self):
        try:
            # ✅ Validação centralizada em schema
            dados = CreateProdutoSchema(**request.get_json())
            
            # Dados já validados
            produto = self.service.create(
                nome=dados.nome,
                descricao=dados.descricao,
                preco=dados.preco,
                estoque=dados.estoque,
                categoria=dados.categoria
            )
            
            return jsonify({
                "dados": {"id": produto["id"]},
                "sucesso": True,
                "mensagem": "Produto criado"
            }), 201
        
        except ValidationError as e:
            # Erros de validação HTTP
            return jsonify({"erro": e.errors()}), 400
        except Exception as e:
            return jsonify({"erro": "Erro interno"}), 500
    
    def atualizar_produto(self, produto_id: int):
        try:
            # ✅ MESMA validação, sem duplicação
            dados = UpdateProdutoSchema(**request.get_json())
            
            produto = self.service.update(produto_id, dados.dict())
            
            if not produto:
                return jsonify({"erro": "Produto não encontrado"}), 404
            
            return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200
        
        except ValidationError as e:
            return jsonify({"erro": e.errors()}), 400
        except Exception as e:
            return jsonify({"erro": "Erro interno"}), 500
```

**Benefícios:**
- ✅ Código de validação centralizado
- ✅ Reutilizável em múltiplos endpoints
- ✅ Manutenção em um único lugar
- ✅ Teste de validação isolado

---

## Pattern 3: CS-002 - God Object / Large Class

### ❌ ANTES: Controllers gigantes com múltiplas responsabilidades
```python
# controllers.py (1000+ linhas)

class UserController:
    # Operações de usuário
    def criar_usuario(self):
        # validação
        # SQL query
        # send email  ← Responsibility leak!
        # send SMS    ← Responsibility leak!
        # logging
        pass
    
    def login(self):
        # Validação email/senha
        # Query BD
        # Gerar token JWT  ← Deveria estar em Service
        # Salvar sessão
        pass
    
    def relatorio_vendas(self):
        # ❌ Vendas nada tem a ver com usuário!
        # Mas está aqui porque foi "fácil"
        pass
    
    def processar_pagamento(self):
        # ❌ Pagamento nada tem a ver com usuário!
        # Integração com gateway de pagamento
        pass
```

### ✅ DEPOIS: Responsabilidades separadas em Services
```python
# services/user_service.py
class UserService:
    def __init__(self, user_repository, notification_service):
        self.repo = user_repository
        self.notifications = notification_service
    
    def create_user(self, name: str, email: str, password: str) -> User:
        """ÚNICA responsabilidade: Criar usuário (regra de negócio)"""
        # Validar email único
        if self.repo.find_by_email(email):
            raise DuplicateEmailException("Email já existe")
        
        # Criar usuário
        user = User(name=name, email=email, password=password)
        created = self.repo.save(user)
        
        # Notificar (delegado ao NotificationService)
        self.notifications.send_welcome_email(created.email)
        
        return created

# services/notification_service.py
class NotificationService:
    """ÚNICA responsabilidade: Enviar notificações"""
    
    def __init__(self, email_client, sms_client):
        self.email = email_client
        self.sms = sms_client
    
    def send_welcome_email(self, email: str):
        self.email.send(
            to=email,
            subject="Bem-vindo!",
            body="Sua conta foi criada com sucesso"
        )
    
    def send_sms(self, phone: str, message: str):
        self.sms.send(phone, message)

# services/payment_service.py
class PaymentService:
    """ÚNICA responsabilidade: Processar pagamentos"""
    
    def __init__(self, gateway_client):
        self.gateway = gateway_client
    
    def process_payment(self, order_id: int, amount: float) -> bool:
        return self.gateway.charge(amount)

# services/report_service.py
class ReportService:
    """ÚNICA responsabilidade: Gerar relatórios"""
    
    def __init__(self, report_repository):
        self.repo = report_repository
    
    def sales_report(self, start_date, end_date):
        return self.repo.get_sales(start_date, end_date)

# controllers/user_controller.py
class UserController:
    """Responsabilidade: Orquestrar request/response de usuário"""
    
    def __init__(self, user_service: UserService):
        self.service = user_service
    
    def create(self):
        try:
            data = CreateUserSchema(**request.get_json())
            user = self.service.create_user(
                name=data.name,
                email=data.email,
                password=data.password
            )
            return jsonify({"id": user.id, "email": user.email}), 201
        except DuplicateEmailException:
            return jsonify({"erro": "Email já existe"}), 409

# controllers/payment_controller.py
class PaymentController:
    """Responsabilidade: Orquestrar request/response de pagamento"""
    
    def __init__(self, payment_service: PaymentService):
        self.service = payment_service
    
    def process_order(self, order_id: int):
        try:
            data = ProcessPaymentSchema(**request.get_json())
            success = self.service.process_payment(order_id, data.amount)
            if success:
                return jsonify({"sucesso": True}), 200
            else:
                return jsonify({"erro": "Pagamento recusado"}), 402
        except Exception as e:
            return jsonify({"erro": "Erro ao processar"}), 500
```

**Benefícios:**
- ✅ Single Responsibility (cada classe uma razão para mudar)
- ✅ Fácil de testar (mock cada service)
- ✅ Fácil de reutilizar (services independentes)
- ✅ Fácil de estender (adicionar novo serviço não afeta outros)

---

## Pattern 4: CS-003 - Tight Coupling (No DI)

### ❌ ANTES: Acoplamento direto
```python
# models.py
db = sqlite3.connect("loja.db")

def get_todos_usuarios():
    cursor = db.cursor()  # ← Acoplado ao DB global
    cursor.execute("SELECT * FROM usuarios")
    return cursor.fetchall()

# controllers.py
from models import get_todos_usuarios  # ← Acoplado à implementação

def listar_usuarios():
    usuarios = get_todos_usuarios()  # ← Impossível mockar
    return jsonify({"dados": usuarios}), 200

# Testando é impossível:
# - Não consegue mockar BD
# - Testes usam BD real
# - Não consegue testar isoladamente
```

### ✅ DEPOIS: Dependency Injection
```python
# interfaces/user_repository.py
from abc import ABC, abstractmethod

class UserRepository(ABC):
    @abstractmethod
    def get_all(self) -> List[User]:
        pass

# repositories/sqlite_user_repository.py
class SQLiteUserRepository(UserRepository):
    def __init__(self, db_connection):
        self.db = db_connection  # ← Injetado
    
    def get_all(self) -> List[User]:
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM usuarios")
        return [self._map_to_user(row) for row in cursor.fetchall()]

# services/user_service.py
class UserService:
    def __init__(self, user_repository: UserRepository):
        self.repository = user_repository  # ← Injetado (abstração!)
    
    def get_all_users(self) -> List[User]:
        return self.repository.get_all()

# controllers/user_controller.py
class UserController:
    def __init__(self, user_service: UserService):
        self.service = user_service  # ← Injetado
    
    def listar(self):
        usuarios = self.service.get_all_users()
        return jsonify({"dados": usuarios}), 200

# app.py - Composition Root
from config.database import get_db

def create_app():
    db = get_db()
    
    # Injetar todas as dependências
    user_repo = SQLiteUserRepository(db)
    user_service = UserService(user_repo)
    user_controller = UserController(user_service)
    
    # Rotas
    bp = create_user_routes(user_service)
    app.register_blueprint(bp)
    
    return app

# tests/test_user_controller.py
def test_listar_usuarios():
    # ✅ Mock do repository
    mock_repo = Mock(spec=UserRepository)
    mock_repo.get_all.return_value = [
        User(1, "John", "john@test.com"),
        User(2, "Jane", "jane@test.com")
    ]
    
    # ✅ Injetar mock
    service = UserService(mock_repo)
    controller = UserController(service)
    
    # ✅ Testar isoladamente
    usuarios = controller.listar()
    assert len(usuarios) == 2
    
    # ✅ Verificar que repo foi chamado
    mock_repo.get_all.assert_called_once()
```

**Benefícios:**
- ✅ Desacoplado (troca SQLite por PostgreSQL facilmente)
- ✅ Testável (mocks funcionam)
- ✅ Reutilizável (service sem conhecer repository)

---

## Pattern 5: CS-009/010 - Hardcoded Secrets & Exposed Config

### ❌ ANTES: Secrets no código
```python
# app.py
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"  # ❌ HARDCODED
app.config["DEBUG"] = True  # ❌ Exposto em produção
DATABASE_URL = "sqlite:///loja.db"

# database.py
def health_check():
    return jsonify({
        "status": "ok",
        "secret_key": "minha-chave-super-secreta-123",  # ❌ Exposto no response!
        "debug": True,  # ❌ Exposto
        "db_path": "loja.db"  # ❌ Exposto
    })
```

### ✅ DEPOIS: Environment-based config
```python
# .env (não commitar!)
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=False
DATABASE_URL=postgresql://user:pass@localhost/mydb
LOG_LEVEL=INFO

# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Obrigatórios - falhar se não existir
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY não configurada!")
    
    # Com defaults
    DEBUG = os.getenv("DEBUG", "False") == "True"
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///app.db")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Nunca retornar em responses
    @staticmethod
    def get_safe_health():
        """Dados seguros para health check"""
        return {
            "status": "ok",
            "version": "1.0.0"
            # ✅ SEM: secret_key, debug, db_path
        }

settings = Settings()

# app.py
from config.settings import settings

app = Flask(__name__)
app.config["SECRET_KEY"] = settings.SECRET_KEY  # ← De variável de ambiente
app.config["DEBUG"] = settings.DEBUG  # ← De variável de ambiente

# controllers/health_controller.py
def health_check():
    return jsonify(settings.get_safe_health()), 200  # ✅ Sem secrets!

# .gitignore
.env
.env.local
.env*.local
*.key
*.pem
```

**Benefícios:**
- ✅ Secrets não no repositório
- ✅ Fácil rotacionar credenciais (ambiente)
- ✅ Diferentes configs por ambiente (dev/staging/prod)
- ✅ Seguro em produção

---

## Pattern 6: CS-011 - N+1 Query Problem

### ❌ ANTES: N+1 Queries
```python
# controllers.py
def listar_pedidos():
    db = get_db()
    cursor = db.cursor()
    
    # Query 1: Todos os pedidos
    cursor.execute("SELECT * FROM pedidos")
    pedidos = cursor.fetchall()
    
    result = []
    for pedido in pedidos:
        # ❌ N+1: Uma query por pedido!
        cursor.execute("SELECT * FROM usuarios WHERE id = ?", (pedido['usuario_id'],))
        usuario = cursor.fetchone()
        
        # ❌ Mais N queries para itens
        cursor.execute("SELECT * FROM itens_pedido WHERE pedido_id = ?", (pedido['id'],))
        itens = cursor.fetchall()
        
        result.append({
            "id": pedido['id'],
            "usuario": usuario['nome'],  # De query extra!
            "itens": itens  # De query extra!
        })
    
    return jsonify({"dados": result}), 200
    # Total: 1 + N + N queries! Horrível para performance
```

### ✅ DEPOIS: Eager Loading / Joins
```python
# repositories/order_repository.py
class OrderRepository:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def get_all_with_details(self) -> List[dict]:
        """✅ Eager loading: Uma query com JOINs"""
        cursor = self.db.cursor()
        
        query = """
        SELECT 
            p.id as pedido_id,
            p.status,
            u.id as usuario_id,
            u.nome as usuario_nome,
            ip.id as item_id,
            ip.produto_id,
            ip.quantidade
        FROM pedidos p
        LEFT JOIN usuarios u ON p.usuario_id = u.id
        LEFT JOIN itens_pedido ip ON p.id = ip.pedido_id
        ORDER BY p.id, ip.id
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Consolidar resultado em estrutura
        pedidos_dict = {}
        for row in rows:
            pedido_id = row['pedido_id']
            if pedido_id not in pedidos_dict:
                pedidos_dict[pedido_id] = {
                    "id": pedido_id,
                    "status": row['status'],
                    "usuario": row['usuario_nome'],
                    "itens": []
                }
            
            if row['item_id']:
                pedidos_dict[pedido_id]['itens'].append({
                    "id": row['item_id'],
                    "produto_id": row['produto_id'],
                    "quantidade": row['quantidade']
                })
        
        return list(pedidos_dict.values())

# services/order_service.py
class OrderService:
    def __init__(self, order_repository: OrderRepository):
        self.repository = order_repository
    
    def get_all_orders_with_details(self):
        return self.repository.get_all_with_details()

# controllers/order_controller.py
class OrderController:
    def __init__(self, order_service: OrderService):
        self.service = order_service
    
    def list_orders(self):
        pedidos = self.service.get_all_orders_with_details()
        return jsonify({"dados": pedidos}), 200

# Alternativa com ORM (SQLAlchemy)
from sqlalchemy.orm import joinedload

class OrderRepositoryORM:
    def get_all_with_details(self):
        return (
            Order.query
            .joinedload(Order.usuario)  # ← Eager load
            .joinedload(Order.itens)    # ← Eager load
            .all()
        )
```

**Benefícios:**
- ✅ Uma query em vez de N+1
- ✅ Performance exponencialmente melhor
- ✅ Menos latência de rede
- ✅ Menos carga no banco

---

## Pattern 7: CS-013 - Global State / Singletons

### ❌ ANTES: Estado global
```python
# database.py
db_connection = None  # ❌ Global state

def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect(":memory:", check_same_thread=False)
    return db_connection

# models.py
from database import get_db

def get_usuarios():
    db = get_db()  # ❌ Acoplado ao global
    # ... query
```

### ✅ DEPOIS: Dependency injection
```python
# config/database.py
class DatabaseConnection:
    _instance = None
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.connection = None
    
    def connect(self):
        self.connection = sqlite3.connect(self.db_url)
        return self.connection
    
    def close(self):
        if self.connection:
            self.connection.close()

# app.py - Composition Root
def create_app():
    # ✅ Criar instância UMA VEZ
    db = DatabaseConnection("sqlite:///app.db")
    db.connect()
    
    # ✅ Injetar para tudo que precisar
    user_repo = SQLiteUserRepository(db.connection)
    user_service = UserService(user_repo)
    user_controller = UserController(user_service)
    
    # ... rest of setup
    
    @app.teardown_appcontext
    def close_db(error):
        db.close()
    
    return app

# Teste: Fácil criar múltiplas instâncias
def test_isolation():
    # ✅ Cada teste com sua instância
    db1 = DatabaseConnection(":memory:")
    db1.connect()
    repo1 = SQLiteUserRepository(db1.connection)
    service1 = UserService(repo1)
    
    db2 = DatabaseConnection(":memory:")
    db2.connect()
    repo2 = SQLiteUserRepository(db2.connection)
    service2 = UserService(repo2)
    
    # Totalmente isolados!
```

---

## Summary: Transformation Checklist

```
PHASE 2 REFACTORING CHECKLIST

SECURITY
  [ ] Remove SQL concatenation (use prepared statements)
  [ ] Remove hardcoded secrets (use environment variables)
  [ ] Sanitize error responses (no internal details)
  [ ] Add input validation schema
  
ARCHITECTURE
  [ ] Extract Repository layer
  [ ] Extract Service layer
  [ ] Implement Dependency Injection
  [ ] Create Composition Root (app.py)
  
CODE QUALITY
  [ ] Extract duplicated validation
  [ ] Split God Objects
  [ ] Remove global state
  [ ] Extract constants and magic values
  
TESTING
  [ ] Setup test infrastructure (pytest, mocks)
  [ ] Write unit tests (Services)
  [ ] Write integration tests (Repositories)
  [ ] Write API tests (Controllers)
  
CONFIGURATION
  [ ] Create .env file
  [ ] Move config to environment
  [ ] Create settings.py
  [ ] Add to .gitignore
  
DOCUMENTATION
  [ ] Document new architecture
  [ ] Update README
  [ ] Add inline comments for complex logic
  [ ] Document API endpoints
```
