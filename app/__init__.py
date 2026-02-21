import os
import logging
from flask import Flask
from app.config import config_map
from app.extensions import init_extensions, db, socketio

os.environ['TOKENIZERS_PARALLELISM'] = 'false'


def create_app(config_name=None):
    """Application factory."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'),
        template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
    )

    # Load config
    cfg = config_map.get(config_name, config_map['development'])
    app.config.from_object(cfg)

    # Ensure directories exist
    os.makedirs(app.config['PROJECTS_DIR'], exist_ok=True)
    os.makedirs(os.path.join(app.config['BASE_DIR'], 'data'), exist_ok=True)

    # Logging
    _setup_logging(app)

    # Extensions
    init_extensions(app)

    # Register blueprints
    _register_blueprints(app)

    # Register socket events
    _register_socket_events(app)

    # Create database tables
    with app.app_context():
        from app.models import user, project, task, chat_history  # noqa: F401
        db.create_all()

    app.logger.info(f'LLM Code Assist started [{config_name}]')
    return app


def _setup_logging(app):
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('app.log'),
            logging.StreamHandler(),
        ],
    )


def _register_blueprints(app):
    from app.api.auth import auth_bp
    from app.api.projects import projects_bp
    from app.api.files import files_bp
    from app.api.analysis import analysis_bp
    from app.api.tasks import tasks_bp
    from app.api.main import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(tasks_bp)


def _register_socket_events(app):
    from app.sockets import execution, analysis  # noqa: F401
