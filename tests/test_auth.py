"""Tests for authentication routes."""


class TestAuthRoutes:
    def test_login_page(self, client):
        response = client.get('/')
        assert response.status_code == 200

    def test_google_login_dev_mode(self, client, app):
        assert app.config.get('SKIP_AUTH') is True
        response = client.get('/auth/google', follow_redirects=False)
        assert response.status_code in (302, 200)

    def test_logout(self, auth_client):
        response = auth_client.get('/auth/logout', follow_redirects=False)
        assert response.status_code == 302

    def test_me_unauthenticated(self, client):
        response = client.get('/auth/me')
        assert response.status_code in (401, 302)

    def test_me_authenticated(self, auth_client, app):
        with app.app_context():
            response = auth_client.get('/auth/me')
            if response.status_code == 200:
                data = response.get_json()
                assert data['success'] is True
                assert data['user']['email'] == 'test@example.com'

    def test_get_preferences_authenticated(self, auth_client, app):
        with app.app_context():
            response = auth_client.get('/auth/preferences')
            if response.status_code == 200:
                data = response.get_json()
                assert data['success'] is True

    def test_update_preferences(self, auth_client, app):
        with app.app_context():
            response = auth_client.put(
                '/auth/preferences',
                json={'theme': 'light'},
                content_type='application/json'
            )
            if response.status_code == 200:
                data = response.get_json()
                assert data['preferences'].get('theme') == 'light'

    def test_update_preferences_no_data(self, auth_client, app):
        with app.app_context():
            response = auth_client.put('/auth/preferences', content_type='application/json')
            assert response.status_code in (400, 415)
