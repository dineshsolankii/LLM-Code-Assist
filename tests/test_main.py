"""Tests for main routes."""


class TestMainRoutes:
    def test_health_check(self, client):
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'ok'

    def test_get_frameworks(self, auth_client, app):
        with app.app_context():
            response = auth_client.get('/api/frameworks')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert len(data['frameworks']) >= 4
            ids = [f['id'] for f in data['frameworks']]
            assert 'python' in ids
            assert 'flask' in ids

    def test_index_with_skip_auth(self, client, app):
        with app.app_context():
            response = client.get('/')
            assert response.status_code == 200
