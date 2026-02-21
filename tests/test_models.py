"""Tests for database models — CRUD, constraints, relationships, and transitions."""
import pytest
from datetime import datetime, timezone


# ══════════════════════════════════════════════════════════════════════════════
# User model
# ══════════════════════════════════════════════════════════════════════════════

class TestUserModel:
    def test_create_user(self, app, db):
        from app.models.user import User
        with app.app_context():
            user = User(google_id='g001', email='u@test.com', name='Test')
            db.session.add(user)
            db.session.commit()
            assert user.id is not None
            assert user.is_active is True

    def test_user_to_dict(self, app, db):
        from app.models.user import User
        with app.app_context():
            user = User(google_id='g002', email='dict@test.com', name='Dict User')
            db.session.add(user)
            db.session.commit()
            d = user.to_dict()
            assert d['email'] == 'dict@test.com'
            assert 'preferences' in d

    def test_default_preferences(self, app, db):
        from app.models.user import User
        with app.app_context():
            user = User(google_id='g003', email='prefs@test.com', name='Prefs')
            db.session.add(user)
            db.session.commit()
            assert user.preferences is not None
            assert user.preferences.get('theme') == 'dark'

    def test_unique_email_constraint(self, app, db):
        from app.models.user import User
        with app.app_context():
            db.session.add(User(google_id='g4a', email='dup@test.com', name='A'))
            db.session.commit()
            db.session.add(User(google_id='g4b', email='dup@test.com', name='B'))
            with pytest.raises(Exception):
                db.session.commit()
            db.session.rollback()

    def test_unique_google_id_constraint(self, app, db):
        from app.models.user import User
        with app.app_context():
            db.session.add(User(google_id='same-gid', email='aa@test.com', name='A'))
            db.session.commit()
            db.session.add(User(google_id='same-gid', email='bb@test.com', name='B'))
            with pytest.raises(Exception):
                db.session.commit()
            db.session.rollback()

    def test_update_preferences(self, app, db):
        from app.models.user import User
        with app.app_context():
            user = User(google_id='g005', email='upref@test.com', name='U')
            db.session.add(user)
            db.session.commit()

            user.preferences = {**user.preferences, 'font_size': 16, 'tab_size': 4}
            db.session.commit()

            fresh = db.session.get(User, user.id)
            assert fresh.preferences['font_size'] == 16
            assert fresh.preferences['tab_size'] == 4
            # Original keys preserved
            assert 'theme' in fresh.preferences

    def test_preferences_persist_across_sessions(self, app, db):
        from app.models.user import User
        with app.app_context():
            user = User(google_id='g006', email='persist@test.com', name='P')
            user.preferences = {'theme': 'light', 'font_size': 14}
            db.session.add(user)
            db.session.commit()
            uid = user.id

        # Re-query in a fresh context
        with app.app_context():
            fresh = db.session.get(User, uid)
            assert fresh.preferences['theme'] == 'light'
            assert fresh.preferences['font_size'] == 14

    def test_user_created_at_set_automatically(self, app, db):
        from app.models.user import User
        with app.app_context():
            user = User(google_id='g007', email='ts@test.com', name='TS')
            db.session.add(user)
            db.session.commit()
            assert user.created_at is not None
            assert isinstance(user.created_at, datetime)

    def test_user_name_and_picture_optional(self, app, db):
        from app.models.user import User
        with app.app_context():
            user = User(google_id='g008', email='noname@test.com',
                        name='Min User', picture_url=None)
            db.session.add(user)
            db.session.commit()
            assert user.id is not None

    def test_cascade_delete_projects(self, app, db):
        """Deleting a user should cascade-delete their projects."""
        from app.models.user import User
        from app.models.project import Project
        with app.app_context():
            user = User(google_id='g009', email='cascade@test.com', name='Cas')
            db.session.add(user)
            db.session.commit()

            p = Project(name='will-be-deleted', framework='python',
                        user_id=user.id, status='ready')
            db.session.add(p)
            db.session.commit()
            pid = p.id

            db.session.delete(user)
            db.session.commit()

            # Project should no longer exist
            assert db.session.get(Project, pid) is None

    def test_to_dict_excludes_sensitive_fields(self, app, db):
        from app.models.user import User
        with app.app_context():
            user = User(google_id='g010', email='safe@test.com', name='Safe')
            db.session.add(user)
            db.session.commit()
            d = user.to_dict()
            # google_id should not leak out in public dict
            assert 'google_id' not in d


# ══════════════════════════════════════════════════════════════════════════════
# Project model
# ══════════════════════════════════════════════════════════════════════════════

class TestProjectModel:
    def _make_user(self, db, suffix):
        from app.models.user import User
        user = User(google_id=f'pg{suffix}', email=f'p{suffix}@test.com', name=f'P{suffix}')
        db.session.add(user)
        db.session.commit()
        return user

    def test_create_project(self, app, db):
        from app.models.project import Project
        with app.app_context():
            user = self._make_user(db, 'c1')
            proj = Project(name='my-proj', framework='flask',
                           user_id=user.id, status='ready')
            db.session.add(proj)
            db.session.commit()
            assert proj.id is not None

    def test_project_to_dict(self, app, db):
        from app.models.project import Project
        with app.app_context():
            user = self._make_user(db, 'd1')
            proj = Project(name='dict-proj', framework='python', user_id=user.id)
            db.session.add(proj)
            db.session.commit()
            d = proj.to_dict()
            assert d['name'] == 'dict-proj'
            assert d['framework'] == 'python'

    def test_unique_project_per_user(self, app, db):
        from app.models.project import Project
        with app.app_context():
            user = self._make_user(db, 'u1')
            db.session.add(Project(name='same', framework='python', user_id=user.id))
            db.session.commit()
            db.session.add(Project(name='same', framework='flask', user_id=user.id))
            with pytest.raises(Exception):
                db.session.commit()
            db.session.rollback()

    def test_same_name_different_users_allowed(self, app, db):
        """Two different users can have a project with the same name."""
        from app.models.user import User
        from app.models.project import Project
        with app.app_context():
            u1 = User(google_id='diff1', email='d1@test.com', name='D1')
            u2 = User(google_id='diff2', email='d2@test.com', name='D2')
            db.session.add_all([u1, u2])
            db.session.commit()
            db.session.add(Project(name='shared-name', framework='python', user_id=u1.id))
            db.session.add(Project(name='shared-name', framework='python', user_id=u2.id))
            db.session.commit()  # Should not raise

    def test_project_default_status(self, app, db):
        from app.models.project import Project
        with app.app_context():
            user = self._make_user(db, 'ds1')
            proj = Project(name='status-test', framework='python', user_id=user.id)
            db.session.add(proj)
            db.session.commit()
            # Default status should be 'pending' or 'creating' or similar
            assert proj.status is not None

    def test_project_created_at(self, app, db):
        from app.models.project import Project
        with app.app_context():
            user = self._make_user(db, 'ts1')
            proj = Project(name='ts-proj', framework='python', user_id=user.id)
            db.session.add(proj)
            db.session.commit()
            assert proj.created_at is not None

    def test_project_to_dict_required_fields(self, app, db):
        from app.models.project import Project
        with app.app_context():
            user = self._make_user(db, 'rf1')
            proj = Project(name='field-check', framework='flask', user_id=user.id)
            db.session.add(proj)
            db.session.commit()
            d = proj.to_dict()
            for field in ('name', 'framework', 'status'):
                assert field in d, f"Missing field '{field}' in project.to_dict()"

    def test_user_projects_relationship(self, app, db):
        """User.projects should return all of the user's projects."""
        from app.models.user import User
        from app.models.project import Project
        with app.app_context():
            user = User(google_id='rel1', email='rel@test.com', name='Rel')
            db.session.add(user)
            db.session.commit()
            for i in range(3):
                db.session.add(Project(name=f'rel-proj-{i}', framework='python',
                                       user_id=user.id))
            db.session.commit()
            # Support both list and AppenderQuery (SQLAlchemy 1.x vs 2.x)
            projects = list(user.projects) if not isinstance(user.projects, list) else user.projects
            assert len(projects) == 3


# ══════════════════════════════════════════════════════════════════════════════
# Task model
# ══════════════════════════════════════════════════════════════════════════════

class TestTaskModel:
    def _make_user_and_project(self, db, tag):
        from app.models.user import User
        from app.models.project import Project
        user = User(google_id=f'tm{tag}', email=f'tm{tag}@test.com', name=f'TM{tag}')
        db.session.add(user)
        db.session.commit()
        proj = Project(name=f'task-proj-{tag}', framework='python', user_id=user.id)
        db.session.add(proj)
        db.session.commit()
        return user, proj

    def test_create_task(self, app, db):
        from app.models.task import Task
        with app.app_context():
            user, proj = self._make_user_and_project(db, 'c1')
            task = Task(project_id=proj.id, user_id=user.id,
                        task_type='generate', status='pending')
            db.session.add(task)
            db.session.commit()
            assert task.id is not None

    def test_task_status_pending_to_running(self, app, db):
        from app.models.task import Task
        with app.app_context():
            user, proj = self._make_user_and_project(db, 'pr1')
            task = Task(project_id=proj.id, user_id=user.id,
                        task_type='analyze', status='pending')
            db.session.add(task)
            db.session.commit()
            task.status = 'running'
            db.session.commit()
            assert db.session.get(Task, task.id).status == 'running'

    def test_task_status_running_to_success(self, app, db):
        from app.models.task import Task
        with app.app_context():
            user, proj = self._make_user_and_project(db, 'rs1')
            task = Task(project_id=proj.id, user_id=user.id,
                        task_type='generate', status='running')
            db.session.add(task)
            db.session.commit()
            task.status = 'success'
            db.session.commit()
            assert db.session.get(Task, task.id).status == 'success'

    def test_task_status_running_to_failure(self, app, db):
        from app.models.task import Task
        with app.app_context():
            user, proj = self._make_user_and_project(db, 'rf1')
            task = Task(project_id=proj.id, user_id=user.id,
                        task_type='generate', status='running')
            db.session.add(task)
            db.session.commit()
            task.status = 'failure'
            task.error_message = 'LLM timed out'
            db.session.commit()
            t = db.session.get(Task, task.id)
            assert t.status == 'failure'
            assert 'timed out' in (t.error_message or '')

    def test_task_to_dict(self, app, db):
        from app.models.task import Task
        with app.app_context():
            user, proj = self._make_user_and_project(db, 'td1')
            task = Task(project_id=proj.id, user_id=user.id,
                        task_type='customize', status='pending')
            db.session.add(task)
            db.session.commit()
            d = task.to_dict()
            assert 'status' in d
            assert 'task_type' in d

    def test_task_created_at(self, app, db):
        from app.models.task import Task
        with app.app_context():
            user, proj = self._make_user_and_project(db, 'ts1')
            task = Task(project_id=proj.id, user_id=user.id,
                        task_type='analyze', status='pending')
            db.session.add(task)
            db.session.commit()
            assert task.created_at is not None

    def test_task_celery_id_stored(self, app, db):
        from app.models.task import Task
        with app.app_context():
            user, proj = self._make_user_and_project(db, 'cel1')
            task = Task(project_id=proj.id, user_id=user.id,
                        task_type='generate', status='pending',
                        celery_task_id='celery-uuid-1234')
            db.session.add(task)
            db.session.commit()
            t = db.session.get(Task, task.id)
            assert t.celery_task_id == 'celery-uuid-1234'

    def test_multiple_tasks_per_project(self, app, db):
        from app.models.task import Task
        with app.app_context():
            user, proj = self._make_user_and_project(db, 'mt1')
            for i in range(4):
                db.session.add(Task(project_id=proj.id, user_id=user.id,
                                    task_type='generate', status='pending'))
            db.session.commit()
            tasks = Task.query.filter_by(project_id=proj.id).all()
            assert len(tasks) == 4


# ══════════════════════════════════════════════════════════════════════════════
# Chat history model
# ══════════════════════════════════════════════════════════════════════════════

class TestChatHistoryModel:
    def test_create_chat_message(self, app, db):
        try:
            from app.models.chat_history import ChatHistory
        except ImportError:
            pytest.skip("ChatHistory model not available")

        from app.models.user import User
        from app.models.project import Project
        with app.app_context():
            user = User(google_id='ch1', email='ch@test.com', name='CH')
            db.session.add(user)
            db.session.commit()
            proj = Project(name='chat-proj', framework='python', user_id=user.id)
            db.session.add(proj)
            db.session.commit()

            msg = ChatHistory(
                project_id=proj.id,
                user_id=user.id,
                role='user',
                message='Hello AI!'
            )
            db.session.add(msg)
            db.session.commit()
            assert msg.id is not None

    def test_chat_history_ordering(self, app, db):
        try:
            from app.models.chat_history import ChatHistory
        except ImportError:
            pytest.skip("ChatHistory model not available")

        from app.models.user import User
        from app.models.project import Project
        with app.app_context():
            user = User(google_id='cho1', email='cho@test.com', name='CHO')
            db.session.add(user)
            db.session.commit()
            proj = Project(name='chat-order', framework='python', user_id=user.id)
            db.session.add(proj)
            db.session.commit()

            roles = ['user', 'assistant', 'user', 'assistant']
            for role in roles:
                db.session.add(ChatHistory(
                    project_id=proj.id, user_id=user.id,
                    role=role, message=f'Message from {role}'
                ))
            db.session.commit()

            msgs = ChatHistory.query.filter_by(project_id=proj.id)\
                                    .order_by(ChatHistory.created_at).all()
            assert len(msgs) == 4
            assert msgs[0].role == 'user'
            assert msgs[1].role == 'assistant'
