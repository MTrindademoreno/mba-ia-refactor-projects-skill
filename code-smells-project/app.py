import logging

from flask import Flask
from flask_cors import CORS

import config
from database import Database
from models import pedidos, produtos, usuarios
from routes import register_routes


def create_app() -> Flask:
    logging.basicConfig(level=logging.INFO)

    db = Database(config.DATABASE_PATH).connect()
    produtos.init(db)
    usuarios.init(db)
    pedidos.init(db)

    app = Flask(__name__)
    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["DEBUG"] = config.DEBUG
    CORS(app)

    register_routes(app)

    return app


app = create_app()

if __name__ == "__main__":
    print("=" * 50)
    print("SERVIDOR INICIADO")
    print("Rodando em http://localhost:5000")
    print("=" * 50)

    app.run(host="0.0.0.0", port=5000, debug=config.DEBUG)
