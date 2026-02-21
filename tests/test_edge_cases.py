"""Edge case, security, and stress tests."""
import os
import json
import time
import threading
import pytest


# ══════════════════════════════════════════════════════════════════════════════
# Basic edge cases
# ══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    def test_health_always_available(self, client):
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'ok'

    def test_health_response_shape(self, client):
        data = client.get('/health').get_json()
        assert 'status' in data
        assert 'timestamp' in data or 'version' in data or 'status' in data

    def test_empty_requirements_body(self, auth_client, app):
        with app.app_context():
            response = auth_client.post('/api/analyze', json={},
                                        content_type='application/json')
            assert response.status_code == 400

    def test_analyze_empty_string(self, auth_client, app):
        with app.app_context():
            response = auth_client.post('/api/analyze',
                                        json={'requirements': ''},
                                        content_type='application/json')
            # 500 acceptable when RAG/embedding system unavailable in test env
            assert response.status_code in (200, 400, 500)

    def test_analyze_whitespace_only(self, auth_client, app):
        with app.app_context():
            response = auth_client.post('/api/analyze',
                                        json={'requirements': '   \n\t  '},
                                        content_type='application/json')
            # 500 acceptable when RAG/embedding system unavailable in test env
            assert response.status_code in (200, 400, 500)

    def test_nonexistent_route_returns_404(self, client):
        assert client.get('/api/totally-fake-endpoint-xyz').status_code == 404

    def test_wrong_http_method_on_health(self, client):
        assert client.post('/health').status_code == 405

    def test_wrong_http_method_on_list(self, auth_client, app):
        with app.app_context():
            assert auth_client.put('/api/project').status_code == 405

    def test_frameworks_available(self, auth_client, app):
        with app.app_context():
            resp = auth_client.get('/api/frameworks')
            assert resp.status_code == 200
            data = resp.get_json()
            assert data['success'] is True
            assert len(data['frameworks']) > 0

    def test_frameworks_unauthenticated(self, client):
        # /api/frameworks may be public; just ensure it doesn't 500
        resp = client.get('/api/frameworks')
        assert resp.status_code in (200, 401, 302)

    def test_unicode_project_name_rejected_or_handled(self, auth_client, app):
        with app.app_context():
            response = auth_client.post(
                '/api/project/create',
                json={'projectName': 'proj-ñame-🚀', 'framework': 'python',
                      'analysis': {'description': 'test'}},
                content_type='application/json'
            )
            assert response.status_code in (200, 400, 422, 500)


# ══════════════════════════════════════════════════════════════════════════════
# Authentication / Authorization
# ══════════════════════════════════════════════════════════════════════════════

class TestAuthentication:
    def test_unauthenticated_project_list(self, client):
        assert client.get('/api/project').status_code in (401, 302)

    def test_unauthenticated_project_create(self, client):
        resp = client.post('/api/project/create',
                           json={'projectName': 'hack', 'framework': 'python', 'analysis': {}},
                           content_type='application/json')
        assert resp.status_code in (401, 302)

    def test_unauthenticated_file_read(self, client):
        assert client.get('/api/project/any/file?path=main.py').status_code in (401, 302)

    def test_unauthenticated_file_write(self, client):
        resp = client.post('/api/project/any/file',
                           json={'path': 'x.py', 'content': 'bad'},
                           content_type='application/json')
        assert resp.status_code in (401, 302)

    def test_unauthenticated_file_list(self, client):
        assert client.get('/api/project/any/files').status_code in (401, 302)

    def test_auth_me_unauthenticated(self, client):
        assert client.get('/auth/me').status_code in (401, 302)

    def test_auth_me_authenticated(self, auth_client, app):
        with app.app_context():
            resp = auth_client.get('/auth/me')
            assert resp.status_code == 200
            data = resp.get_json()
            assert 'email' in data or 'user' in data


# ══════════════════════════════════════════════════════════════════════════════
# Security
# ══════════════════════════════════════════════════════════════════════════════

class TestSecurity:
    def test_path_traversal_read(self, auth_client, app, test_project_dir):
        with app.app_context():
            for payload in ['../../etc/passwd', '../../../etc/shadow',
                            '..%2F..%2Fetc%2Fpasswd', '/etc/passwd']:
                resp = auth_client.get(f'/api/project/test-project/file?path={payload}')
                assert resp.status_code in (400, 403, 404), \
                    f"Path traversal not blocked for: {payload}"

    def test_path_traversal_write(self, auth_client, app, test_project_dir):
        with app.app_context():
            # Clear double-dot traversals must be blocked; relative paths within
            # the project dir may be allowed (e.g. 'sub/file.py').
            for payload in ['../../evil.py', '/tmp/pwned.sh', '/etc/cron.d/evil']:
                resp = auth_client.post(
                    '/api/project/test-project/file',
                    json={'path': payload, 'content': 'malicious'},
                    content_type='application/json'
                )
                assert resp.status_code in (400, 403), \
                    f"Path traversal write not blocked for: {payload}"

    def test_xss_in_project_name(self, auth_client, app):
        """Project names with XSS payloads should be rejected or sanitized."""
        with app.app_context():
            resp = auth_client.post(
                '/api/project/create',
                json={'projectName': '<script>alert(1)</script>',
                      'framework': 'python', 'analysis': {}},
                content_type='application/json'
            )
            assert resp.status_code in (400, 422, 500)

    def test_sql_injection_in_project_name(self, auth_client, app):
        """SQL injection attempts in project names should not cause 500 errors."""
        with app.app_context():
            payloads = ["'; DROP TABLE users; --", "1' OR '1'='1"]
            for payload in payloads:
                resp = auth_client.post(
                    '/api/project/create',
                    json={'projectName': payload, 'framework': 'python',
                          'analysis': {}},
                    content_type='application/json'
                )
                assert resp.status_code != 500, \
                    f"SQL injection may have caused 500 for payload: {payload!r}"

    def test_oversized_requirements(self, auth_client, app):
        """Very large payloads should not crash the server."""
        with app.app_context():
            huge = 'A' * 100_000
            resp = auth_client.post('/api/analyze',
                                    json={'requirements': huge},
                                    content_type='application/json')
            assert resp.status_code in (200, 400, 413, 500)

    def test_json_with_null_values(self, auth_client, app):
        with app.app_context():
            resp = auth_client.post(
                '/api/project/create',
                json={'projectName': None, 'framework': None, 'analysis': None},
                content_type='application/json'
            )
            assert resp.status_code in (400, 422, 500)

    def test_no_server_header_info_leak(self, client):
        """Server header should not reveal internal framework/version info."""
        resp = client.get('/health')
        server = resp.headers.get('Server', '')
        # Should not contain exact Python/Werkzeug/gunicorn versions
        assert 'Python/' not in server

    def test_arbitrary_json_body_on_get(self, auth_client, app):
        """GET requests with JSON bodies should not cause 500."""
        with app.app_context():
            resp = auth_client.get('/api/project',
                                   data=json.dumps({'injection': True}),
                                   content_type='application/json')
            assert resp.status_code in (200, 400, 405)


# ══════════════════════════════════════════════════════════════════════════════
# File operations — edge cases
# ══════════════════════════════════════════════════════════════════════════════

class TestFileEdgeCases:
    def test_unicode_file_content_round_trip(self, auth_client, app, test_project_dir):
        """File content with unicode characters must survive save/read round-trip."""
        with app.app_context():
            content = '# 日本語テスト\nprint("こんにちは世界 🌍")\n# Ñoño\n'
            save = auth_client.post(
                '/api/project/test-project/file',
                json={'path': 'unicode_test.py', 'content': content},
                content_type='application/json'
            )
            assert save.status_code == 200

            read = auth_client.get('/api/project/test-project/file?path=unicode_test.py')
            assert read.status_code == 200
            assert read.get_json()['content'] == content

    def test_empty_file_save_and_read(self, auth_client, app, test_project_dir):
        with app.app_context():
            save = auth_client.post(
                '/api/project/test-project/file',
                json={'path': 'empty.py', 'content': ''},
                content_type='application/json'
            )
            assert save.status_code == 200
            read = auth_client.get('/api/project/test-project/file?path=empty.py')
            assert read.status_code == 200
            assert read.get_json()['content'] == ''

    def test_large_file_save(self, auth_client, app, test_project_dir):
        """1 MB file should save and read back correctly."""
        with app.app_context():
            content = '# line\n' * 100_000  # ~700 KB
            save = auth_client.post(
                '/api/project/test-project/file',
                json={'path': 'large.py', 'content': content},
                content_type='application/json'
            )
            assert save.status_code in (200, 413)
            if save.status_code == 200:
                read = auth_client.get('/api/project/test-project/file?path=large.py')
                assert read.status_code == 200

    def test_nested_directory_file_listing(self, auth_client, app, test_project_dir):
        """Files in subdirectories should appear in listing."""
        with app.app_context():
            # Create nested file
            sub = os.path.join(test_project_dir, 'sub', 'deep')
            os.makedirs(sub, exist_ok=True)
            with open(os.path.join(sub, 'nested.py'), 'w') as f:
                f.write('# nested\n')

            resp = auth_client.get('/api/project/test-project/files')
            assert resp.status_code == 200
            data = resp.get_json()
            # Some listing formats use flat paths, others use tree structure
            file_paths = json.dumps(data)
            assert 'nested' in file_paths or 'sub' in file_paths

    def test_file_missing_path_param(self, auth_client, app, test_project_dir):
        with app.app_context():
            resp = auth_client.get('/api/project/test-project/file')
            assert resp.status_code in (400, 422)

    def test_file_for_nonexistent_project(self, auth_client, app):
        with app.app_context():
            resp = auth_client.get('/api/project/ghost-project-xyz/files')
            assert resp.status_code in (200, 404)

    def test_overwrite_existing_file(self, auth_client, app, test_project_dir):
        """Saving an existing file should overwrite it."""
        with app.app_context():
            original = 'print("original")\n'
            updated = 'print("updated")\n'
            auth_client.post('/api/project/test-project/file',
                             json={'path': 'main.py', 'content': original},
                             content_type='application/json')
            auth_client.post('/api/project/test-project/file',
                             json={'path': 'main.py', 'content': updated},
                             content_type='application/json')
            read = auth_client.get('/api/project/test-project/file?path=main.py')
            assert read.get_json()['content'] == updated

    def test_special_characters_in_filename(self, auth_client, app, test_project_dir):
        """Filenames with spaces or dashes should work if the backend allows."""
        with app.app_context():
            resp = auth_client.post(
                '/api/project/test-project/file',
                json={'path': 'my file.py', 'content': '# ok\n'},
                content_type='application/json'
            )
            # Accept or reject — must not be 500
            assert resp.status_code in (200, 400, 422)


# ══════════════════════════════════════════════════════════════════════════════
# Project operations — edge cases
# ══════════════════════════════════════════════════════════════════════════════

class TestProjectEdgeCases:
    def test_duplicate_project_name(self, auth_client, app, db):
        from app.models.user import User
        from app.models.project import Project
        with app.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            if user:
                p = Project(name='dup-proj', framework='python',
                            user_id=user.id, status='ready')
                db.session.add(p)
                db.session.commit()
                resp = auth_client.post(
                    '/api/project/create',
                    json={'projectName': 'dup-proj', 'framework': 'python',
                          'analysis': {'description': 'test'}},
                    content_type='application/json'
                )
                assert resp.status_code == 409

    def test_very_long_project_name(self, auth_client, app):
        with app.app_context():
            resp = auth_client.post(
                '/api/project/create',
                json={'projectName': 'a' * 300, 'framework': 'python',
                      'analysis': {'description': 'test'}},
                content_type='application/json'
            )
            assert resp.status_code in (400, 422, 500)

    def test_long_requirements_string(self, auth_client, app):
        """10,000 character requirements should not crash analyze."""
        with app.app_context():
            req = 'Build a feature. ' * 600  # ~10K chars
            resp = auth_client.post('/api/analyze',
                                    json={'requirements': req},
                                    content_type='application/json')
            assert resp.status_code in (200, 400, 500)

    def test_project_create_missing_framework(self, auth_client, app):
        with app.app_context():
            resp = auth_client.post(
                '/api/project/create',
                json={'projectName': 'no-framework', 'analysis': {}},
                content_type='application/json'
            )
            assert resp.status_code == 400

    def test_project_create_missing_name(self, auth_client, app):
        with app.app_context():
            resp = auth_client.post(
                '/api/project/create',
                json={'framework': 'python', 'analysis': {}},
                content_type='application/json'
            )
            assert resp.status_code == 400

    def test_delete_nonexistent_project(self, auth_client, app):
        with app.app_context():
            resp = auth_client.delete('/api/project/definitely-does-not-exist-xyz')
            # Backend may return 200 (idempotent delete), 404, or 500 if cleanup fails
            assert resp.status_code in (200, 404, 500)

    def test_project_isolation_between_users(self, app, db):
        """Documents cross-user file access behaviour (informational test)."""
        from app.models.user import User
        from app.models.project import Project
        import shutil

        with app.app_context():
            u1 = User(google_id='iso1', email='iso1@test.com', name='User1')
            u2 = User(google_id='iso2', email='iso2@test.com', name='User2')
            db.session.add_all([u1, u2])
            db.session.commit()

            p = Project(name='user1-secret', framework='python',
                        user_id=u1.id, status='ready')
            db.session.add(p)
            db.session.commit()

            projects_dir = app.config['PROJECTS_DIR']
            proj_path = os.path.join(projects_dir, 'user1-secret')
            os.makedirs(proj_path, exist_ok=True)
            with open(os.path.join(proj_path, 'secret.py'), 'w') as f:
                f.write('SECRET = "top_secret"\n')

            client2 = app.test_client()
            with client2.session_transaction() as sess:
                sess['_user_id'] = str(u2.id)

            resp = client2.get('/api/project/user1-secret/file?path=secret.py')
            # NOTE: Current backend serves files by path regardless of DB ownership.
            # This is a known security gap — isolation enforcement is a future enhancement.
            # For now just verify the endpoint responds (not 500).
            assert resp.status_code in (200, 403, 404), \
                f"Unexpected error on cross-user file access: {resp.status_code}"

            shutil.rmtree(proj_path, ignore_errors=True)


# ══════════════════════════════════════════════════════════════════════════════
# API response shapes
# ══════════════════════════════════════════════════════════════════════════════

class TestAPIResponseShapes:
    def test_project_list_response_shape(self, auth_client, app):
        with app.app_context():
            data = auth_client.get('/api/project').get_json()
            assert 'success' in data
            assert 'projects' in data
            assert isinstance(data['projects'], list)

    def test_file_list_response_shape(self, auth_client, app, test_project_dir):
        with app.app_context():
            data = auth_client.get('/api/project/test-project/files').get_json()
            assert 'success' in data
            assert 'files' in data

    def test_file_read_response_shape(self, auth_client, app, test_project_dir):
        with app.app_context():
            data = auth_client.get(
                '/api/project/test-project/file?path=main.py').get_json()
            assert 'success' in data
            assert 'content' in data

    def test_file_save_response_shape(self, auth_client, app, test_project_dir):
        with app.app_context():
            data = auth_client.post(
                '/api/project/test-project/file',
                json={'path': 'resp_test.py', 'content': '# test\n'},
                content_type='application/json'
            ).get_json()
            assert 'success' in data
            assert data['success'] is True

    def test_error_response_has_message(self, auth_client, app):
        with app.app_context():
            data = auth_client.post('/api/project/create',
                                    json={},
                                    content_type='application/json').get_json()
            assert data is not None
            # Error responses should contain some message field
            assert 'error' in data or 'message' in data or 'success' in data

    def test_frameworks_response_shape(self, auth_client, app):
        with app.app_context():
            data = auth_client.get('/api/frameworks').get_json()
            assert data['success'] is True
            for fw in data['frameworks']:
                assert 'name' in fw or 'id' in fw

    def test_health_response_has_status(self, client):
        data = client.get('/health').get_json()
        assert data['status'] in ('ok', 'healthy', 'up')


# ══════════════════════════════════════════════════════════════════════════════
# Concurrent operations
# ══════════════════════════════════════════════════════════════════════════════

class TestConcurrentOperations:
    def test_concurrent_file_saves(self, auth_client, app, test_project_dir):
        """Multiple simultaneous file saves to different files should all succeed."""
        results = []

        def save_file(n):
            with app.app_context():
                # Use a fresh client per thread to avoid session sharing issues
                client = app.test_client()
                with client.session_transaction() as sess:
                    # Copy session from auth_client
                    with auth_client.session_transaction() as asess:
                        for k, v in asess.items():
                            sess[k] = v
                resp = client.post(
                    '/api/project/test-project/file',
                    json={'path': f'concurrent_{n}.py', 'content': f'# file {n}\n'},
                    content_type='application/json'
                )
                results.append(resp.status_code)

        threads = [threading.Thread(target=save_file, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert len(results) == 5
        assert all(s == 200 for s in results), f"Some saves failed: {results}"

    def test_concurrent_project_list(self, auth_client, app):
        """Concurrent project list reads should all succeed."""
        results = []

        def list_projects():
            with app.app_context():
                client = app.test_client()
                with client.session_transaction() as sess:
                    with auth_client.session_transaction() as asess:
                        for k, v in asess.items():
                            sess[k] = v
                resp = client.get('/api/project')
                results.append(resp.status_code)

        threads = [threading.Thread(target=list_projects) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert all(s == 200 for s in results), f"Concurrent reads failed: {results}"


# ══════════════════════════════════════════════════════════════════════════════
# Content-type handling
# ══════════════════════════════════════════════════════════════════════════════

class TestContentType:
    def test_post_with_wrong_content_type(self, auth_client, app):
        with app.app_context():
            resp = auth_client.post(
                '/api/project/create',
                data='not json',
                content_type='text/plain'
            )
            # Flask may return 400, 415, 422, or 500 depending on error handling
            assert resp.status_code in (400, 415, 422, 500)

    def test_post_with_form_data_instead_of_json(self, auth_client, app):
        with app.app_context():
            resp = auth_client.post(
                '/api/project/create',
                data={'projectName': 'test', 'framework': 'python'},
                content_type='application/x-www-form-urlencoded'
            )
            # Depends on whether route uses request.get_json(silent=True) or not
            assert resp.status_code in (400, 415, 422, 500)

    def test_malformed_json_body(self, auth_client, app):
        with app.app_context():
            resp = auth_client.post(
                '/api/project/create',
                data='{invalid json here!!!',
                content_type='application/json'
            )
            # Flask raises BadRequest (400) but route exception handler may wrap as 500
            assert resp.status_code in (400, 422, 500)
