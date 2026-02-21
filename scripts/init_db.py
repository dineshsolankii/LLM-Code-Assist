#!/usr/bin/env python
"""Initialize database with seed data."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.user import User


def init_db():
    app = create_app(os.environ.get('FLASK_ENV', 'development'))
    with app.app_context():
        db.create_all()

        # Create dev user if SKIP_AUTH
        if app.config.get('SKIP_AUTH'):
            dev_user = User.query.filter_by(email='dev@localhost').first()
            if not dev_user:
                dev_user = User(
                    google_id='dev-user-001',
                    email='dev@localhost',
                    name='Developer',
                    picture_url='',
                )
                db.session.add(dev_user)
                db.session.commit()
                print('Created dev user: dev@localhost')

        print('Database initialized successfully.')


if __name__ == '__main__':
    init_db()
