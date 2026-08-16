import logging

from sqlalchemy import func

from database import db
from models.category import Category
from models.task import Task
from services.errors import ServiceError

logger = logging.getLogger(__name__)


def list_categories():
    categories = Category.query.all()
    counts = dict(
        db.session.query(Task.category_id, func.count(Task.id))
        .group_by(Task.category_id)
        .all()
    )

    result = []
    for c in categories:
        cat_data = c.to_dict()
        cat_data['task_count'] = counts.get(c.id, 0)
        result.append(cat_data)
    return result


def create_category(data):
    if not data:
        raise ServiceError('Dados inválidos')

    name = data.get('name')
    if not name:
        raise ServiceError('Nome é obrigatório')

    category = Category()
    category.name = name
    category.description = data.get('description', '')
    category.color = data.get('color', '#000000')

    try:
        db.session.add(category)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar categoria: {e}")
        raise ServiceError('Erro ao criar categoria', 500)

    return category.to_dict()


def update_category(cat_id, data):
    cat = Category.query.get(cat_id)
    if not cat:
        raise ServiceError('Categoria não encontrada', 404)

    if 'name' in data:
        cat.name = data['name']
    if 'description' in data:
        cat.description = data['description']
    if 'color' in data:
        cat.color = data['color']

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar categoria {cat_id}: {e}")
        raise ServiceError('Erro ao atualizar', 500)

    return cat.to_dict()


def delete_category(cat_id):
    cat = Category.query.get(cat_id)
    if not cat:
        raise ServiceError('Categoria não encontrada', 404)

    try:
        db.session.delete(cat)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao deletar categoria {cat_id}: {e}")
        raise ServiceError('Erro ao deletar', 500)
