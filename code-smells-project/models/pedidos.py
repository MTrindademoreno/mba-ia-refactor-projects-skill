import sqlite3
from typing import Optional

_db: Optional[sqlite3.Connection] = None


def init(connection: sqlite3.Connection) -> None:
    global _db
    _db = connection


def criar(usuario_id: int, itens: list[dict]) -> dict:
    cursor = _db.cursor()

    total = 0
    precos_por_produto: dict[int, float] = {}

    for item in itens:
        cursor.execute("SELECT * FROM produtos WHERE id = ?", (item["produto_id"],))
        produto = cursor.fetchone()
        if produto is None:
            return {"erro": "Produto " + str(item["produto_id"]) + " não encontrado"}
        if produto["estoque"] < item["quantidade"]:
            return {"erro": "Estoque insuficiente para " + produto["nome"]}
        precos_por_produto[item["produto_id"]] = produto["preco"]
        total = total + (produto["preco"] * item["quantidade"])

    cursor.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
        (usuario_id, total),
    )
    pedido_id = cursor.lastrowid

    for item in itens:
        preco_unitario = precos_por_produto[item["produto_id"]]
        cursor.execute(
            "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
            (pedido_id, item["produto_id"], item["quantidade"], preco_unitario),
        )
        cursor.execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
            (item["quantidade"], item["produto_id"]),
        )

    _db.commit()
    return {"pedido_id": pedido_id, "total": total}


def get_por_usuario(usuario_id: int) -> list[dict]:
    return _buscar_pedidos("WHERE p.usuario_id = ?", (usuario_id,))


def get_todos() -> list[dict]:
    return _buscar_pedidos("", ())


def atualizar_status(pedido_id: int, novo_status: str) -> bool:
    cursor = _db.cursor()
    cursor.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    _db.commit()
    return True


def contar_todos() -> int:
    cursor = _db.cursor()
    cursor.execute("SELECT COUNT(*) FROM pedidos")
    return cursor.fetchone()[0]


def somar_faturamento() -> float:
    cursor = _db.cursor()
    cursor.execute("SELECT SUM(total) FROM pedidos")
    valor = cursor.fetchone()[0]
    return valor if valor is not None else 0


def contar_por_status(status: str) -> int:
    cursor = _db.cursor()
    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = ?", (status,))
    return cursor.fetchone()[0]


def relatorio_vendas() -> dict:
    total_pedidos = contar_todos()
    faturamento = somar_faturamento()
    pendentes = contar_por_status("pendente")
    aprovados = contar_por_status("aprovado")
    cancelados = contar_por_status("cancelado")

    desconto = 0
    if faturamento > 10000:
        desconto = faturamento * 0.1
    elif faturamento > 5000:
        desconto = faturamento * 0.05
    elif faturamento > 1000:
        desconto = faturamento * 0.02

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": pendentes,
        "pedidos_aprovados": aprovados,
        "pedidos_cancelados": cancelados,
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }


def _buscar_pedidos(where_clause: str, params: tuple) -> list[dict]:
    cursor = _db.cursor()
    query = (
        "SELECT p.id AS pedido_id, p.usuario_id, p.status, p.total, p.criado_em, "
        "i.produto_id, i.quantidade, i.preco_unitario, pr.nome AS produto_nome "
        "FROM pedidos p "
        "LEFT JOIN itens_pedido i ON i.pedido_id = p.id "
        "LEFT JOIN produtos pr ON pr.id = i.produto_id "
        + where_clause
        + " ORDER BY p.id"
    )
    cursor.execute(query, params)
    rows = cursor.fetchall()

    pedidos: dict[int, dict] = {}
    ordem: list[int] = []
    for row in rows:
        pid = row["pedido_id"]
        if pid not in pedidos:
            pedidos[pid] = {
                "id": pid,
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "criado_em": row["criado_em"],
                "itens": [],
            }
            ordem.append(pid)
        if row["produto_id"] is not None:
            pedidos[pid]["itens"].append(
                {
                    "produto_id": row["produto_id"],
                    "produto_nome": row["produto_nome"] if row["produto_nome"] else "Desconhecido",
                    "quantidade": row["quantidade"],
                    "preco_unitario": row["preco_unitario"],
                }
            )

    return [pedidos[pid] for pid in ordem]
