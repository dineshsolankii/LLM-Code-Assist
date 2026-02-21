from datetime import datetime
from app.extensions import db


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    celery_task_id = db.Column(db.String(255), unique=True, index=True)
    task_type = db.Column(db.String(100), nullable=False)  # analyze, generate, execute, customize
    status = db.Column(db.String(50), default='pending')  # pending, running, success, failure, revoked
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    # Task data
    input_data = db.Column(db.JSON)
    result_data = db.Column(db.JSON)
    error_message = db.Column(db.Text)

    # Timing
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)

    # Progress tracking (0-100)
    progress = db.Column(db.Integer, default=0)
    progress_message = db.Column(db.String(255), default='')

    def to_dict(self):
        return {
            'id': self.id,
            'celery_task_id': self.celery_task_id,
            'task_type': self.task_type,
            'status': self.status,
            'project_id': self.project_id,
            'progress': self.progress,
            'progress_message': self.progress_message,
            'result_data': self.result_data,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
