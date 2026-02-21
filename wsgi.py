"""WSGI entry point for production (gunicorn)."""
from app import create_app
from app.extensions import socketio

app = create_app('production')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8001)
