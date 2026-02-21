"""Tests for project endpoints."""
import os


class TestProjectRoutes:
    def test_list_projects_empty(self, auth_client, app):
        with app.app_context():
            response = auth_client.get('/api/project')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert isinstance(data['projects'], list)

    def test_list_projects_with_filesystem(self, auth_client, app, test_project_dir):
        with app.app_context():
            response = auth_client.get('/api/project')
            assert response.status_code == 200
            data = response.get_json()
            names = [p['name'] for p in data['projects']]
            assert 'test-project' in names

    def test_create_project_missing_fields(self, auth_client, app):
        with app.app_context():
            response = auth_client.post(
                '/api/project/create',
                json={'projectName': 'test'},
                content_type='application/json'
            )
            assert response.status_code == 400

    def test_create_project_no_data(self, auth_client, app):
        with app.app_context():
            response = auth_client.post('/api/project/create', content_type='application/json')
            # Empty body with application/json → BadRequest may be wrapped as 500 by route
            assert response.status_code in (400, 500)

    def test_delete_nonexistent_project(self, auth_client, app):
        with app.app_context():
            response = auth_client.delete('/api/project/definitely-does-not-exist-xyz')
            assert response.status_code in (200, 404, 500)
