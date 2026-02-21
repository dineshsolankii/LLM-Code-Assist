import logging
from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from app.models.task import Task

logger = logging.getLogger(__name__)

tasks_bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')


@tasks_bp.route('/<int:task_id>', methods=['GET'])
@login_required
def get_task(task_id):
    """Get task status and progress."""
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if not task:
        return jsonify({'success': False, 'error': 'Task not found'}), 404
    return jsonify({'success': True, 'task': task.to_dict()})


@tasks_bp.route('/<int:task_id>/cancel', methods=['POST'])
@login_required
def cancel_task(task_id):
    """Cancel a running task."""
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if not task:
        return jsonify({'success': False, 'error': 'Task not found'}), 404

    if task.celery_task_id:
        try:
            from celery_app import celery_app
            celery_app.control.revoke(task.celery_task_id, terminate=True)
            task.status = 'revoked'
            from app.extensions import db
            db.session.commit()
        except Exception as e:
            logger.error(f'Error revoking task: {e}')
            return jsonify({'success': False, 'error': str(e)}), 500

    return jsonify({'success': True, 'task': task.to_dict()})


@tasks_bp.route('', methods=['GET'])
@login_required
def list_tasks():
    """List recent tasks for current user."""
    tasks = Task.query.filter_by(user_id=current_user.id).order_by(
        Task.created_at.desc()
    ).limit(50).all()
    return jsonify({'success': True, 'tasks': [t.to_dict() for t in tasks]})
