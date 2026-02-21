"""Celery application factory."""
import os
from celery import Celery

celery_app = Celery(
    'llm_code_assist',
    broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/1'),
    backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2'),
)
celery_app.config_from_object('celery_app.celeryconfig')


def init_celery(app=None):
    """Bind Celery to Flask app context."""
    if app:
        celery_app.conf.update(app.config)

        class ContextTask(celery_app.Task):
            abstract = True

            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)

        celery_app.Task = ContextTask

    return celery_app
