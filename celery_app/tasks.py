"""Celery task definitions."""
import logging
from datetime import datetime, timedelta
from celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=2, name='celery_app.tasks.analyze_requirements')
def analyze_requirements(self, requirements_text, user_id, socket_sid=None):
    """Analyze project requirements in background."""
    try:
        from utils.model_manager import ModelManager
        from utils.rag_system import RAGSystem
        from agents.requirement_analyzer import RequirementAnalyzer

        mm = ModelManager()
        rag = RAGSystem()
        analyzer = RequirementAnalyzer(mm, rag)
        result = analyzer.analyze(requirements_text)

        # Emit via SocketIO if sid provided
        if socket_sid:
            try:
                from flask_socketio import SocketIO
                import os
                sio = SocketIO(message_queue=os.environ.get('SOCKETIO_MESSAGE_QUEUE', 'redis://localhost:6379/3'))
                sio.emit('analysis_result', {'success': True, 'analysis': result}, room=socket_sid)
            except Exception as e:
                logger.warning(f'Could not emit via SocketIO: {e}')

        return result

    except Exception as exc:
        logger.error(f'Analysis task failed: {exc}')
        raise self.retry(exc=exc, countdown=5)


@celery_app.task(bind=True, max_retries=1, name='celery_app.tasks.generate_project_code')
def generate_project_code(self, project_name, analysis_data, framework, user_id):
    """Generate project code in background."""
    try:
        from utils.model_manager import ModelManager
        from utils.rag_system import RAGSystem
        from utils.file_manager import FileManager
        from agents.project_creator import ProjectCreator
        from agents.code_generator import CodeGenerator
        import os

        base_dir = os.environ.get('PROJECTS_DIR', os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'projects'))

        mm = ModelManager()
        rag = RAGSystem()
        fm = FileManager(base_dir)

        creator = ProjectCreator(mm, rag, fm)
        project_path = creator.create_project(analysis_data, framework, project_name)

        main_file = 'app.py' if framework in ('flask', 'gradio', 'streamlit') else 'main.py'
        generator = CodeGenerator(mm, rag, fm)
        generator.generate(project_name, main_file, analysis_data)

        return {'success': True, 'project_path': project_path, 'project_name': project_name}

    except Exception as exc:
        logger.error(f'Code generation task failed: {exc}')
        raise self.retry(exc=exc, countdown=10)


@celery_app.task(bind=True, name='celery_app.tasks.customize_code')
def customize_code(self, project_name, file_path, current_code, request_text, user_id):
    """Customize code in background."""
    try:
        from utils.model_manager import ModelManager
        from utils.rag_system import RAGSystem
        from agents.customizer import CodeCustomizer

        mm = ModelManager()
        rag = RAGSystem()
        customizer = CodeCustomizer(mm, rag)
        result = customizer.customize(
            project_name=project_name,
            file_path=file_path,
            current_code=current_code,
            customization_request=request_text,
        )
        return {'success': True, 'code': result}

    except Exception as exc:
        logger.error(f'Customization task failed: {exc}')
        return {'success': False, 'error': str(exc)}


@celery_app.task(name='celery_app.tasks.cleanup_stale_tasks')
def cleanup_stale_tasks():
    """Mark stale running tasks as failed."""
    try:
        from app import create_app
        from app.extensions import db
        from app.models.task import Task

        app = create_app()
        with app.app_context():
            cutoff = datetime.utcnow() - timedelta(minutes=15)
            stale = Task.query.filter(
                Task.status == 'running',
                Task.started_at < cutoff,
            ).all()
            for t in stale:
                t.status = 'failure'
                t.error_message = 'Task timed out'
                t.completed_at = datetime.utcnow()
            db.session.commit()
            if stale:
                logger.info(f'Cleaned up {len(stale)} stale tasks')
    except Exception as e:
        logger.error(f'Cleanup error: {e}')


@celery_app.task(name='celery_app.tasks.refresh_model_cache')
def refresh_model_cache():
    """Refresh available models in Redis cache."""
    try:
        from utils.model_manager import ModelManager
        mm = ModelManager()
        models = mm.list_models()
        if mm.redis and models.get('models'):
            import json
            mm.redis.setex('cache:models', 300, json.dumps(models))
            logger.info(f'Refreshed model cache: {len(models.get("models", []))} models')
    except Exception as e:
        logger.error(f'Model cache refresh error: {e}')
