# Analysis Heuristics - Stack Detection & Architecture Mapping

The examples in this document are illustrative, not an exhaustive stack list. Start with all root manifests, build files, lockfiles, source extensions, and runtime configuration. For an unlisted language or framework, identify its canonical toolchain and use the same evidence-based mapping process; do not report it as unsupported.

Guia prático para detectar tecnologias, frameworks, padrões arquiteturais e mapear componentes durante a Fase 1 (Análise).

## 1. Detecção de Linguagem & Framework

### Python Projects
**Indicators:**
- `.py` files throughout project
- `requirements.txt` ou `setup.py` ou `pyproject.toml`
- `__init__.py` in directories (package structure)
- `if __name__ == "__main__"` entry point pattern

**Web Frameworks (by imports in main files):**
```python
# Flask
from flask import Flask, request, jsonify
from flask_cors import CORS

# FastAPI
from fastapi import FastAPI, HTTPException

# Django
import django
from django.http import JsonResponse

# Bottle
from bottle import Bottle, request, response
```

### JavaScript/Node Projects
**Indicators:**
- `.js` or `.ts` files
- `package.json` (mandatory)
- `node_modules/` directory
- `npm` or `yarn` as package manager

**Web Frameworks (by package.json dependencies):**
```json
{
  "dependencies": {
    "express": "^4.x" // Express.js
    "fastify": "^4.x" // Fastify
    "hapi": "^21.x" // Hapi
    "koa": "^2.x" // Koa
    "next": "^13.x" // Next.js
  }
}
```

### Java Projects
**Indicators:**
- `.java` files
- `pom.xml` (Maven) or `build.gradle` (Gradle)
- `src/main/java` directory structure
- `.class` compiled files in `target/` or `build/`

**Frameworks (by pom.xml or build.gradle):**
```xml
<!-- Spring Boot -->
<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-web</artifactId>
</dependency>

<!-- Micronaut, Quarkus, etc. -->
```

---

## 2. Detecção de Banco de Dados

### File-based Databases
```
- *.db files (SQLite)
- *.sqlite, *.sqlite3
- Indicador: Lightweight, single-file databases
```

### Connection Strings & Configuration Files
```python
# Python - database.py, config.py
DATABASE_URL = "sqlite:///app.db"
DATABASE_URL = "postgresql://user:pass@localhost/db"
DATABASE_URL = "mysql://user:pass@localhost/db"

# .env files
DB_HOST=localhost
DB_NAME=mydb
DB_USER=admin
DB_PASSWORD=secret
```

### Import-based Detection
```python
# SQLite
import sqlite3
db = sqlite3.connect("database.db")

# PostgreSQL
import psycopg2
conn = psycopg2.connect("dbname=mydb user=admin")

# MySQL
import mysql.connector
conn = mysql.connector.connect(host="localhost", user="admin", database="mydb")

# MongoDB
from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017/")

# ORM Libraries
from sqlalchemy import create_engine  # SQLAlchemy
from django.db import models  # Django ORM
```

### Schema Detection
Look for:
- `CREATE TABLE` statements (raw SQL)
- Migration files (Alembic, Django migrations)
- Model definitions (ORM classes)
- Database initialization code

---

## 3. Architecture Pattern Detection

### Monolithic vs Distributed
**Monolithic Signals:**
- Single entry point (`app.py`, `main.py`, `index.js`)
- All code in one directory/package
- Direct imports between layers
- No service boundaries

**Distributed/Microservices Signals:**
- Multiple entry points (one per service)
- Separate directories/repositories per service
- API clients for inter-service communication
- Service discovery configuration

### MVC vs Other Patterns
**MVC Signals:**
- Separate directories: `models/`, `views/`, `controllers/`
- Route handlers in `views/` or `routes/`
- Business logic in `models/`
- Request handlers in `controllers/`

**Example Python/Flask MVC:**
```
src/
├── models/          ← Data layer
├── views/           ← Route definitions
├── controllers/     ← Request handlers
└── app.py           ← Main
```

**Layered/N-tier Signals:**
- `presentation/`, `business/`, `persistence/`
- Clear separation of concerns
- Explicit service layers

**God Class / Monolithic Code Signals:**
- Large files (>500 lines)
- Multiple responsibilities in one file
- Direct database queries mixed with business logic
- Request handling mixed with data access

---

## 4. Dependency & Coupling Analysis

### Direct Imports (Tight Coupling)
```python
# ❌ BAD - Direct implementation import
from models.user import User
user = User()

# ✅ GOOD - Interface/abstract import
from interfaces.user_repository import UserRepository
```

### Circular Dependencies
Look for:
- File A imports from B, B imports from A
- Check import statements in each module
- Tools: `pylint`, `madge` for JavaScript

### Global State
```python
# ❌ BAD - Global connections
db = sqlite3.connect(":memory:")

# ✅ GOOD - Dependency injection
class UserService:
    def __init__(self, db_connection):
        self.db = db_connection
```

### Entry Point Analysis
Check `app.py`, `main.py`, `index.js`:
- How is initialization done?
- Are objects created directly or injected?
- Is there a "composition root" pattern?

---

## 5. Configuration Detection

### Hardcoded Configuration
```python
# ❌ BAD
SECRET_KEY = "my-secret-key-123"
DEBUG = True
DATABASE_URL = "sqlite:///app.db"
API_KEY = "sk_live_xxx"
```

### Environment-based Configuration
```python
# ✅ GOOD
import os
SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = os.getenv("DEBUG", "False") == "True"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///app.db")
```

### Configuration Files
Look for:
- `config.py`, `settings.py`, `config.yml`, `.env`
- Environment-specific configs (dev, staging, prod)
- Secrets in version control (🚨 RED FLAG)

---

## 6. Testing Infrastructure Detection

### Test Files
```
- tests/ directory exists ❌ or missing ✅?
- test_*.py files (Python)
- *.test.js files (JavaScript)
- *_test.go files (Go)
```

### Test Framework Imports
```python
import unittest  # Built-in
import pytest  # Popular Python
from django.test import TestCase  # Django

# JavaScript
import { test } from '@jest/globals'  // Jest
import { describe, it } from 'mocha'  // Mocha
```

### Coverage
- `.coverage` files
- Coverage config in `setup.cfg`, `.coveragerc`, `pyproject.toml`

---

## 7. Security Vulnerability Signals

### High-Risk Patterns
- ❌ SQL concatenation: `"SELECT * FROM users WHERE id = " + str(user_id)`
- ❌ Hardcoded credentials in code
- ❌ Secrets exposed in health check endpoints
- ❌ Debug mode enabled in production
- ❌ No input validation on routes

### Positive Signals
- ✅ Parameterized queries: `SELECT * FROM users WHERE id = ?`
- ✅ Environment-based secrets
- ✅ Input validation frameworks (Pydantic, Joi, etc)
- ✅ Auth middleware/decorators

---

## 8. Component Mapping Process

### Step-by-Step for Monolithic Project

1. **Identify Entry Point**
   - Find `app.py`, `main.py`, `index.js`
   - Extract Flask/Express/Spring initialization

2. **Map Route Handlers**
   - List all endpoints (`/api/users`, `/api/products`, etc)
   - Find route definitions file (often `routes.py`, `app.js`)

3. **Trace Controller Logic**
   - From route → find handler function
   - Identify what business logic it calls
   - Document input validation

4. **Identify Data Models**
   - Look for `models/` directory or ORM definitions
   - Find database table mappings
   - Document relationships

5. **Find Database Access**
   - Locate database initialization
   - Check for raw SQL or ORM usage
   - Identify connection pooling

6. **Extract Configuration**
   - Find all hardcoded values
   - Identify environment variables
   - Check for secrets exposure

7. **Document External Dependencies**
   - Third-party APIs used
   - Message queues, caches
   - External services

---

## 9. Heuristic Checklist

Use this during Phase 1 analysis:

```
LANGUAGE & FRAMEWORK
[ ] Language identified (Python, JavaScript, Java, etc)
[ ] Framework identified (Flask, Express, Django, etc)
[ ] Version captured

DATABASE
[ ] Database type identified (SQLite, PostgreSQL, etc)
[ ] Connection method (raw SQL, ORM, etc)
[ ] Schema documented

ARCHITECTURE
[ ] Pattern identified (Monolithic, MVC, Layered, etc)
[ ] Entry point located
[ ] Main layers/modules documented
[ ] Component dependencies mapped

CODE QUALITY
[ ] Coupling level assessed (tight/loose)
[ ] Global state identified (if any)
[ ] Circular dependencies checked
[ ] File sizes evaluated

CONFIGURATION
[ ] Hardcoded values found
[ ] Environment config exists
[ ] Secrets exposure checked
[ ] Debug mode status

TESTING
[ ] Test directory exists
[ ] Test framework identified
[ ] Coverage level assessed

SECURITY
[ ] SQL injection risks found
[ ] Hardcoded credentials found
[ ] Input validation checked
[ ] Auth mechanism found
```

---

## 10. Red Flags During Analysis

🚨 **CRITICAL (Stop & Report):**
- SQL injection vulnerabilities found
- Secrets hardcoded in source code
- No input validation on routes

🔴 **HIGH (Immediate Action Needed):**
- All logic in one file/class (God Object)
- No separation of concerns (MVC violated)
- Direct database calls in routes
- Global mutable state everywhere

🟡 **MEDIUM (Plan Refactoring):**
- Circular dependencies
- No configuration management
- Mixed validation logic
- No error handling standardization

🟢 **LOW (Technical Debt):**
- Poor naming conventions
- Magic numbers/strings
- Inconsistent code style
- Missing comments
