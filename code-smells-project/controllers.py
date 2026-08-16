import logging

from flask import jsonify, request

import config
from models import pedidos, produtos, usuarios
from utils.constants import STATUS_PEDIDO_VALIDOS
from utils.validation import validar_produto

logger = logging.getLogger(__name__)


def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": "1.0.0",
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health"
        }
    })


def listar_produtos():
    try:
        dados = produtos.get_todos()
        return jsonify({"dados": dados, "sucesso": True}), 200
    except Exception:
        logger.exception("Erro ao listar produtos")
        return jsonify({"erro": "Erro interno ao processar a requisição"}), 500


def buscar_produto(id):
    try:
        produto = produtos.get_por_id(id)
        if produto:
            return jsonify({"dados": produto, "sucesso": True}), 200
        return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
    except Exception:
        logger.exception("Erro ao buscar produto %s", id)
        return jsonify({"erro": "Erro interno ao processar a requisição"}), 500


def criar_produto():
    try:
        dados = request.get_json()

        erro = validar_produto(dados)
        if erro:
            return jsonify({"erro": erro}), 400

        nome = dados["nome"]
        descricao = dados.get("descricao", "")
        preco = dados["preco"]
        estoque = dados["estoque"]
        categoria = dados.get("categoria", "geral")

        id = produtos.criar(nome, descricao, preco, estoque, categoria)
        logger.info("Produto criado com ID: %s", id)
        return jsonify({"dados": {"id": id}, "sucesso": True, "mensagem": "Produto criado"}), 201

    except Exception:
        logger.exception("Erro ao criar produto")
        return jsonify({"erro": "Erro interno ao processar a requisição"}), 500


def atualizar_produto(id):
    try:
        dados = request.get_json()

        produto_existente = produtos.get_por_id(id)
        if not produto_existente:
            return jsonify({"erro": "Produto não encontrado"}), 404

        erro = validar_produto(dados)
        if erro:
            return jsonify({"erro": erro}), 400

        nome = dados["nome"]
        descricao = dados.get("descricao", "")
        preco = dados["preco"]
        estoque = dados["estoque"]
        categoria = dados.get("categoria", "geral")

        produtos.atualizar(id, nome, descricao, preco, estoque, categoria)
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    except Exception:
        logger.exception("Erro ao atualizar produto %s", id)
        return jsonify({"erro": "Erro interno ao processar a requisição"}), 500


def deletar_produto(id):
    try:
        produto = produtos.get_por_id(id)
        if not produto:
            return jsonify({"erro": "Produto não encontrado"}), 404

        produtos.deletar(id)
        logger.info("Produto %s deletado", id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
    except Exception:
        logger.exception("Erro ao deletar produto %s", id)
        return jsonify({"erro": "Erro interno ao processar a requisição"}), 500


def buscar_produtos():
    try:
        termo = request.args.get("q", "")
        categoria = request.args.get("categoria", None)
        preco_min = request.args.get("preco_min", None)
        preco_max = request.args.get("preco_max", None)

        if preco_min:
            preco_min = float(preco_min)
        if preco_max:
            preco_max = float(preco_max)

        resultados = produtos.buscar(termo, categoria, preco_min, preco_max)
        return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200
    except Exception:
        logger.exception("Erro ao buscar produtos")
        return jsonify({"erro": "Erro interno ao processar a requisição"}), 500


def listar_usuarios():
    try:
        dados = usuarios.get_todos()
        return jsonify({"dados": dados, "sucesso": True}), 200
    except Exception:
        logger.exception("Erro ao listar usuarios")
        return jsonify({"erro": "Erro interno ao processar a requisição"}), 500


def buscar_usuario(id):
    try:
        usuario = usuarios.get_por_id(id)
        if usuario:
            return jsonify({"dados": usuario, "sucesso": True}), 200
        return jsonify({"erro": "Usuário não encontrado"}), 404
    except Exception:
        logger.exception("Erro ao buscar usuario %s", id)
        return jsonify({"erro": "Erro interno ao processar a requisição"}), 500


def criar_usuario():
    try:
        dados = request.get_json()

        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400

        nome = dados.get("nome", "")
        email = dados.get("email", "")
        senha = dados.get("senha", "")

        if not nome or not email or not senha:
            return jsonify({"erro": "Nome, email e senha são obrigatórios"}), 400

        id = usuarios.criar(nome, email, senha)
        logger.info("Usuário criado: %s", email)
        return jsonify({"dados": {"id": id}, "sucesso": True}), 201

    except Exception:
        logger.exception("Erro ao criar usuario")
        return jsonify({"erro": "Erro interno ao processar a requisição"}), 500


def login():
    try:
        dados = request.get_json()
        email = dados.get("email", "")
        senha = dados.get("senha", "")

        if not email or not senha:
            return jsonify({"erro": "Email e senha são obrigatórios"}), 400

        usuario = usuarios.login(email, senha)
        if usuario:
            logger.info("Login bem-sucedido: %s", email)
            return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
        else:
            logger.info("Login falhou: %s", email)
            return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401

    except Exception:
        logger.exception("Erro no login")
        return jsonify({"erro": "Erro interno ao processar a requisição"}), 500


def criar_pedido():
    try:
        dados = request.get_json()

        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400

        usuario_id = dados.get("usuario_id")
        itens = dados.get("itens", [])

        if not usuario_id:
            return jsonify({"erro": "Usuario ID é obrigatório"}), 400
        if not itens or len(itens) == 0:
            return jsonify({"erro": "Pedido deve ter pelo menos 1 item"}), 400

        resultado = pedidos.criar(usuario_id, itens)

        if "erro" in resultado:
            return jsonify({"erro": resultado["erro"], "sucesso": False}), 400

        logger.info("Pedido %s criado para usuario %s", resultado["pedido_id"], usuario_id)

        return jsonify({
            "dados": resultado,
            "sucesso": True,
            "mensagem": "Pedido criado com sucesso"
        }), 201

    except Exception:
        logger.exception("Erro critico ao criar pedido")
        return jsonify({"erro": "Erro interno ao processar a requisição"}), 500


def listar_pedidos_usuario(usuario_id):
    try:
        dados = pedidos.get_por_usuario(usuario_id)
        return jsonify({"dados": dados, "sucesso": True}), 200
    except Exception:
        logger.exception("Erro ao listar pedidos do usuario %s", usuario_id)
        return jsonify({"erro": "Erro interno ao processar a requisição"}), 500


def listar_todos_pedidos():
    try:
        dados = pedidos.get_todos()
        return jsonify({"dados": dados, "sucesso": True}), 200
    except Exception:
        logger.exception("Erro ao listar pedidos")
        return jsonify({"erro": "Erro interno ao processar a requisição"}), 500


def atualizar_status_pedido(pedido_id):
    try:
        dados = request.get_json()
        novo_status = dados.get("status", "")

        if novo_status not in STATUS_PEDIDO_VALIDOS:
            return jsonify({"erro": "Status inválido"}), 400

        pedidos.atualizar_status(pedido_id, novo_status)

        if novo_status == "aprovado":
            logger.info("Pedido %s aprovado - preparar envio", pedido_id)
        if novo_status == "cancelado":
            logger.info("Pedido %s cancelado - devolver estoque", pedido_id)

        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200

    except Exception:
        logger.exception("Erro ao atualizar status do pedido %s", pedido_id)
        return jsonify({"erro": "Erro interno ao processar a requisição"}), 500


def relatorio_vendas():
    try:
        relatorio = pedidos.relatorio_vendas()
        return jsonify({"dados": relatorio, "sucesso": True}), 200
    except Exception:
        logger.exception("Erro ao gerar relatorio de vendas")
        return jsonify({"erro": "Erro interno ao processar a requisição"}), 500


def health_check():
    try:
        return jsonify({
            "status": "ok",
            "database": "connected",
            "counts": {
                "produtos": produtos.contar(),
                "usuarios": usuarios.contar(),
                "pedidos": pedidos.contar_todos()
            },
            "versao": "1.0.0",
            "ambiente": "producao",
            "db_path": config.DATABASE_PATH
        }), 200
    except Exception:
        logger.exception("Erro no health check")
        return jsonify({"status": "erro", "detalhes": "Erro interno ao verificar o sistema"}), 500
