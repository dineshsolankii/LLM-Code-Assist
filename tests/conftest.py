import os
import sys
import shutil
import pytest
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db as _db


@pytest.fixture(scope='session')
def app():
    test_app = create_app('testing')
    test_app.config['PROJECTS_DIR'] = tempfile.mkdtemp(prefix='llm_test_')
    test_app.config['WTF_CSRF_ENABLED'] = False
    test_app.config['SERVER_NAME'] = 'localhost'
    yield test_app
    shutil.rmtree(test_app.config['PROJECTS_DIR'], ignore_errors=True)


@pytest.fixture(scope='function')
def db(app):
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.rollback()
        _db.drop_all()


@pytest.fixture(scope='function')
def client(app, db):
    return app.test_client()


@pytest.fixture(scope='function')
def auth_client(app, db):
    from app.models.user import User
    with app.app_context():
        user = User(google_id='test-g-001', email='test@example.com', name='Test User', picture_url='')
        _db.session.add(user)
        _db.session.commit()
        uid = user.id
    client = app.test_client()
    with client.session_transaction() as sess:
        sess['_user_id'] = str(uid)
    return client


@pytest.fixture
def test_project_dir(app):
    projects_dir = app.config['PROJECTS_DIR']
    project_path = os.path.join(projects_dir, 'test-project')
    os.makedirs(project_path, exist_ok=True)
    with open(os.path.join(project_path, 'main.py'), 'w') as f:
        f.write('print("Hello, World!")\n')
    with open(os.path.join(project_path, 'requirements.txt'), 'w') as f:
        f.write('flask>=3.0\n')
    yield project_path
    shutil.rmtree(project_path, ignore_errors=True)
