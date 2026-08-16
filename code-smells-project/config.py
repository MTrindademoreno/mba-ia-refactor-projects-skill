import os

SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
DEBUG: bool = os.getenv("DEBUG", "True") == "True"
DATABASE_PATH: str = os.getenv("DATABASE_PATH", "loja.db")
