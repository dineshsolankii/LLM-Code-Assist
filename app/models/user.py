from datetime import datetime
from flask_login import UserMixin
from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    picture_url = db.Column(db.String(512), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    preferences = db.Column(db.JSON, default=lambda: {
        'theme': 'dark',
        'editor_font_size': 14,
        'line_numbers': True,
        'word_wrap': True,
        'auto_save': True,
        'auto_indent': True,
    })

    # Relationships
    projects = db.relationship('Project', backref='owner', lazy='dynamic',
                               cascade='all, delete-orphan')
    tasks = db.relationship('Task', backref='user', lazy='dynamic')
    chat_history = db.relationship('ChatHistory', backref='user', lazy='dynamic',
                                   cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'picture_url': self.picture_url,
            'preferences': self.preferences or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }
