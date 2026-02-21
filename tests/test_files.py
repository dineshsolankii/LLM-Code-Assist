"""Tests for file operation endpoints."""
import os


class TestFileRoutes:
    def test_list_files(self, auth_client, app, test_project_dir):
        with app.app_context():
            response = auth_client.get('/api/project/test-project/files')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            names = [f['name'] for f in data['files']]
            assert 'main.py' in names

    def test_get_file_content(self, auth_client, app, test_project_dir):
        with app.app_context():
            response = auth_client.get('/api/project/test-project/file?path=main.py')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'Hello, World!' in data['content']

    def test_get_nonexistent_file(self, auth_client, app, test_project_dir):
        with app.app_context():
            response = auth_client.get('/api/project/test-project/file?path=notexist.py')
            assert response.status_code == 404

    def test_save_file(self, auth_client, app, test_project_dir):
        with app.app_context():
            response = auth_client.post(
                '/api/project/test-project/file',
                json={'path': 'new_file.py', 'content': 'print("new")'},
                content_type='application/json'
            )
            assert response.status_code == 200
            assert response.get_json()['success'] is True
            assert os.path.exists(os.path.join(test_project_dir, 'new_file.py'))

    def test_save_file_missing_content(self, auth_client, app, test_project_dir):
        with app.app_context():
            response = auth_client.post(
                '/api/project/test-project/file',
                json={'path': 'test.py'},
                content_type='application/json'
            )
            assert response.status_code == 400

    def test_path_traversal_read_blocked(self, auth_client, app, test_project_dir):
        with app.app_context():
            response = auth_client.get('/api/project/test-project/file?path=../../etc/passwd')
            assert response.status_code == 403

    def test_path_traversal_write_blocked(self, auth_client, app, test_project_dir):
        with app.app_context():
            response = auth_client.post(
                '/api/project/test-project/file',
                json={'path': '../../etc/evil.py', 'content': 'bad'},
                content_type='application/json'
            )
            assert response.status_code == 403
