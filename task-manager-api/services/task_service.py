import logging
from datetime import datetime
from sqlalchemy.orm import joinedload

from database import db
from models.task import Task
from models.user import User
from models.category import Category
from services.errors import ServiceError

logger = logging.getLogger(__name__)

VALID_STATUSES = ['pending', 'in_progress', 'done', 'cancelled']
MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200


def _validate_title_length(title):
    if len(title) < MIN_TITLE_LENGTH:
        raise ServiceError('Título muito curto')
    if len(title) > MAX_TITLE_LENGTH:
        raise ServiceError('Título muito longo')


def _validate_status(status):
    if status not in VALID_STATUSES:
        raise ServiceError('Status inválido')


def _validate_priority(priority):
    if priority < 1 or priority > 5:
        raise ServiceError('Prioridade deve ser entre 1 e 5')


def _require_user(user_id):
    if user_id and not User.query.get(user_id):
        raise ServiceError('Usuário não encontrado', 404)


def _require_category(category_id):
    if category_id and not Category.query.get(category_id):
        raise ServiceError('Categoria não encontrada', 404)


def _parse_due_date(due_date, error_message='Formato de data inválido. Use YYYY-MM-DD'):
    try:
        return datetime.strptime(due_date, '%Y-%m-%d')
    except (ValueError, TypeError):
        raise ServiceError(error_message)


def _normalize_tags(tags):
    if isinstance(tags, list):
        return ','.join(tags)
    return tags


def _serialize_task_summary(task):
    data = task.to_dict()
    data['overdue'] = task.is_overdue()
    data['user_name'] = task.user.name if task.user else None
    data['category_name'] = task.category.name if task.category else None
    return data


def list_tasks():
    try:
        tasks = Task.query.options(
            joinedload(Task.user), joinedload(Task.category)
        ).all()
        return [_serialize_task_summary(t) for t in tasks]
    except Exception as e:
        logger.error(f"Erro ao listar tasks: {e}")
        raise ServiceError('Erro interno', 500)


def get_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        raise ServiceError('Task não encontrada', 404)

    data = task.to_dict()
    data['overdue'] = task.is_overdue()
    return data


def create_task(data):
    if not data:
        raise ServiceError('Dados inválidos')

    title = data.get('title')
    if not title:
        raise ServiceError('Título é obrigatório')
    _validate_title_length(title)

    status = data.get('status', 'pending')
    _validate_status(status)

    priority = data.get('priority', 3)
    _validate_priority(priority)

    user_id = data.get('user_id')
    _require_user(user_id)

    category_id = data.get('category_id')
    _require_category(category_id)

    task = Task()
    task.title = title
    task.description = data.get('description', '')
    task.status = status
    task.priority = priority
    task.user_id = user_id
    task.category_id = category_id

    due_date = data.get('due_date')
    if due_date:
        task.due_date = _parse_due_date(due_date)

    tags = data.get('tags')
    if tags:
        task.tags = _normalize_tags(tags)

    try:
        db.session.add(task)
        db.session.commit()
        logger.info(f"Task criada: {task.id} - {task.title}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar task: {e}")
        raise ServiceError('Erro ao criar task', 500)

    return task.to_dict()


def update_task(task_id, data):
    task = Task.query.get(task_id)
    if not task:
        raise ServiceError('Task não encontrada', 404)

    if not data:
        raise ServiceError('Dados inválidos')

    if 'title' in data:
        _validate_title_length(data['title'])
        task.title = data['title']

    if 'description' in data:
        task.description = data['description']

    if 'status' in data:
        _validate_status(data['status'])
        task.status = data['status']

    if 'priority' in data:
        _validate_priority(data['priority'])
        task.priority = data['priority']

    if 'user_id' in data:
        _require_user(data['user_id'])
        task.user_id = data['user_id']

    if 'category_id' in data:
        _require_category(data['category_id'])
        task.category_id = data['category_id']

    if 'due_date' in data:
        if data['due_date']:
            task.due_date = _parse_due_date(data['due_date'], 'Formato de data inválido')
        else:
            task.due_date = None

    if 'tags' in data:
        task.tags = _normalize_tags(data['tags'])

    task.updated_at = datetime.utcnow()

    try:
        db.session.commit()
        logger.info(f"Task atualizada: {task.id}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar task {task_id}: {e}")
        raise ServiceError('Erro ao atualizar', 500)

    return task.to_dict()


def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        raise ServiceError('Task não encontrada', 404)

    try:
        db.session.delete(task)
        db.session.commit()
        logger.info(f"Task deletada: {task_id}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao deletar task {task_id}: {e}")
        raise ServiceError('Erro ao deletar', 500)


def search_tasks(query, status, priority, user_id):
    tasks = Task.query

    if query:
        tasks = tasks.filter(
            db.or_(
                Task.title.like(f'%{query}%'),
                Task.description.like(f'%{query}%')
            )
        )

    if status:
        tasks = tasks.filter(Task.status == status)

    if priority:
        tasks = tasks.filter(Task.priority == int(priority))

    if user_id:
        tasks = tasks.filter(Task.user_id == int(user_id))

    return [t.to_dict() for t in tasks.all()]


def task_stats():
    total = Task.query.count()
    pending = Task.query.filter_by(status='pending').count()
    in_progress = Task.query.filter_by(status='in_progress').count()
    done = Task.query.filter_by(status='done').count()
    cancelled = Task.query.filter_by(status='cancelled').count()

    overdue_count = sum(1 for t in Task.query.all() if t.is_overdue())

    return {
        'total': total,
        'pending': pending,
        'in_progress': in_progress,
        'done': done,
        'cancelled': cancelled,
        'overdue': overdue_count,
        'completion_rate': round((done / total) * 100, 2) if total > 0 else 0
    }
