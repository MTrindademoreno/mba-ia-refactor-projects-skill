import sqlite3
from typing import Optional

from werkzeug.security import check_password_hash, generate_password_hash

_db: Optional[sqlite3.Connection] = None


def init(connection: sqlite3.Connection) -> None:
    global _db
    _db = connection


def get_todos() -> list[dict]:
    cursor = _db.cursor()
    cursor.execute("SELECT * FROM usuarios")
    return [_to_dict(row) for row in cursor.fetchall()]


def get_por_id(id: int) -> Optional[dict]:
    cursor = _db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (id,))
    row = cursor.fetchone()
    return _to_dict(row) if row else None


def criar(nome: str, email: str, senha: str, tipo: str = "cliente") -> int:
    senha_hash = generate_password_hash(senha)
    cursor = _db.cursor()
    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, tipo),
    )
    _db.commit()
    return cursor.lastrowid


def login(email: str, senha: str) -> Optional[dict]:
    cursor = _db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
    row = cursor.fetchone()
    if row and check_password_hash(row["senha"], senha):
        return {
            "id": row["id"],
            "nome": row["nome"],
            "email": row["email"],
            "tipo": row["tipo"],
        }
    return None


def contar() -> int:
    cursor = _db.cursor()
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    return cursor.fetchone()[0]


def _to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }
