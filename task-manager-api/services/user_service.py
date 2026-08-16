import logging

from database import db
from models.user import User
from models.task import Task
from services.errors import ServiceError
from utils.helpers import validate_email

logger = logging.getLogger(__name__)

VALID_ROLES = ['user', 'admin', 'manager']
MIN_PASSWORD_LENGTH = 4


def _require_valid_email(email):
    if not validate_email(email):
        raise ServiceError('Email inválido')


def _require_unique_email(email, exclude_user_id=None):
    existing = User.query.filter_by(email=email).first()
    if existing and existing.id != exclude_user_id:
        raise ServiceError('Email já cadastrado', 409)


def _require_valid_role(role):
    if role not in VALID_ROLES:
        raise ServiceError('Role inválido')


def list_users():
    users = User.query.all()
    result = []
    for u in users:
        user_data = u.to_dict()
        user_data['task_count'] = len(u.tasks)
        result.append(user_data)
    return result


def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        raise ServiceError('Usuário não encontrado', 404)

    data = user.to_dict()
    tasks = Task.query.filter_by(user_id=user_id).all()
    data['tasks'] = [t.to_dict() for t in tasks]
    return data


def create_user(data):
    if not data:
        raise ServiceError('Dados inválidos')

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user')

    if not name:
        raise ServiceError('Nome é obrigatório')
    if not email:
        raise ServiceError('Email é obrigatório')
    if not password:
        raise ServiceError('Senha é obrigatória')

    _require_valid_email(email)

    if len(password) < MIN_PASSWORD_LENGTH:
        raise ServiceError('Senha deve ter no mínimo 4 caracteres')

    _require_unique_email(email)
    _require_valid_role(role)

    user = User()
    user.name = name
    user.email = email
    user.set_password(password)
    user.role = role

    try:
        db.session.add(user)
        db.session.commit()
        logger.info(f"Usuário criado: {user.id} - {user.name}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar usuário: {e}")
        raise ServiceError('Erro ao criar usuário', 500)

    return user.to_dict()


def update_user(user_id, data):
    user = User.query.get(user_id)
    if not user:
        raise ServiceError('Usuário não encontrado', 404)

    if not data:
        raise ServiceError('Dados inválidos')

    if 'name' in data:
        user.name = data['name']

    if 'email' in data:
        _require_valid_email(data['email'])
        _require_unique_email(data['email'], exclude_user_id=user_id)
        user.email = data['email']

    if 'password' in data:
        if len(data['password']) < MIN_PASSWORD_LENGTH:
            raise ServiceError('Senha muito curta')
        user.set_password(data['password'])

    if 'role' in data:
        _require_valid_role(data['role'])
        user.role = data['role']

    if 'active' in data:
        user.active = data['active']

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar usuário {user_id}: {e}")
        raise ServiceError('Erro ao atualizar', 500)

    return user.to_dict()


def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        raise ServiceError('Usuário não encontrado', 404)

    tasks = Task.query.filter_by(user_id=user_id).all()
    for t in tasks:
        db.session.delete(t)

    try:
        db.session.delete(user)
        db.session.commit()
        logger.info(f"Usuário deletado: {user_id}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao deletar usuário {user_id}: {e}")
        raise ServiceError('Erro ao deletar', 500)


def get_user_tasks(user_id):
    user = User.query.get(user_id)
    if not user:
        raise ServiceError('Usuário não encontrado', 404)

    tasks = Task.query.filter_by(user_id=user_id).all()
    result = []
    for t in tasks:
        task_data = t.to_dict()
        task_data['overdue'] = t.is_overdue()
        result.append(task_data)
    return result


def login(data):
    if not data:
        raise ServiceError('Dados inválidos')

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        raise ServiceError('Email e senha são obrigatórios')

    user = User.query.filter_by(email=email).first()
    if not user:
        raise ServiceError('Credenciais inválidas', 401)

    if not user.check_password(password):
        raise ServiceError('Credenciais inválidas', 401)

    if not user.active:
        raise ServiceError('Usuário inativo', 403)

    return {
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': 'fake-jwt-token-' + str(user.id)
    }
