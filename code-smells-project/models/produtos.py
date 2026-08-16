import sqlite3
from typing import Optional

_db: Optional[sqlite3.Connection] = None


def init(connection: sqlite3.Connection) -> None:
    global _db
    _db = connection


def get_todos() -> list[dict]:
    cursor = _db.cursor()
    cursor.execute("SELECT * FROM produtos")
    return [_to_dict(row) for row in cursor.fetchall()]


def get_por_id(id: int) -> Optional[dict]:
    cursor = _db.cursor()
    cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
    row = cursor.fetchone()
    return _to_dict(row) if row else None


def criar(nome: str, descricao: str, preco: float, estoque: int, categoria: str) -> int:
    cursor = _db.cursor()
    cursor.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    _db.commit()
    return cursor.lastrowid


def atualizar(id: int, nome: str, descricao: str, preco: float, estoque: int, categoria: str) -> bool:
    cursor = _db.cursor()
    cursor.execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
        (nome, descricao, preco, estoque, categoria, id),
    )
    _db.commit()
    return True


def deletar(id: int) -> bool:
    cursor = _db.cursor()
    cursor.execute("DELETE FROM produtos WHERE id = ?", (id,))
    _db.commit()
    return True


def buscar(
    termo: str,
    categoria: Optional[str] = None,
    preco_min: Optional[float] = None,
    preco_max: Optional[float] = None,
) -> list[dict]:
    cursor = _db.cursor()
    query = "SELECT * FROM produtos WHERE 1=1"
    params: list = []

    if termo:
        query += " AND (nome LIKE ? OR descricao LIKE ?)"
        params.append("%" + termo + "%")
        params.append("%" + termo + "%")
    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    if preco_min:
        query += " AND preco >= ?"
        params.append(preco_min)
    if preco_max:
        query += " AND preco <= ?"
        params.append(preco_max)

    cursor.execute(query, params)
    return [_to_dict(row) for row in cursor.fetchall()]


def decrementar_estoque(id: int, quantidade: int) -> None:
    cursor = _db.cursor()
    cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (quantidade, id))


def contar() -> int:
    cursor = _db.cursor()
    cursor.execute("SELECT COUNT(*) FROM produtos")
    return cursor.fetchone()[0]


def _to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "nome": row["nome"],
        "descricao": row["descricao"],
        "preco": row["preco"],
        "estoque": row["estoque"],
        "categoria": row["categoria"],
        "ativo": row["ativo"],
        "criado_em": row["criado_em"],
    }
