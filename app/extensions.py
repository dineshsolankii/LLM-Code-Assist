import os
import redis
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_caching import Cache
from flask_session import Session
from flask_socketio import SocketIO
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
oauth = OAuth()
cache = Cache()
sess = Session()
socketio = SocketIO()
cors = CORS()

# Redis client (initialized in init_extensions)
redis_client = None


def init_extensions(app):
    """Initialize all Flask extensions with the app."""
    global redis_client

    db.init_app(app)
    migrate.init_app(app, db)

    # Login manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login_page'

    # Cache
    cache.init_app(app)

    # Session
    redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
    try:
        app.config['SESSION_REDIS'] = redis.from_url(redis_url)
        redis_client = redis.from_url(redis_url, decode_responses=True)
    except Exception:
        app.logger.warning('Redis not available, falling back to filesystem sessions')
        app.config['SESSION_TYPE'] = 'filesystem'
        redis_client = None

    sess.init_app(app)

    # CORS
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}, r"/auth/*": {"origins": "*"}})

    # SocketIO
    message_queue = app.config.get('SOCKETIO_MESSAGE_QUEUE')
    try:
        socketio.init_app(
            app,
            message_queue=message_queue,
            async_mode='eventlet',
            cors_allowed_origins="*",
            logger=False,
            engineio_logger=False,
        )
    except Exception:
        socketio.init_app(
            app,
            async_mode='threading',
            cors_allowed_origins="*",
        )

    # OAuth
    oauth.init_app(app)
    if app.config.get('GOOGLE_CLIENT_ID'):
        oauth.register(
            name='google',
            client_id=app.config['GOOGLE_CLIENT_ID'],
            client_secret=app.config['GOOGLE_CLIENT_SECRET'],
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={'scope': 'openid email profile'},
        )

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return db.session.get(User, int(user_id))
