from datetime import datetime
from app.extensions import db


class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text, default='')
    framework = db.Column(db.String(50), nullable=False, default='python')
    status = db.Column(db.String(50), default='created')  # created, generating, ready, error
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Analysis results stored as JSON
    analysis_data = db.Column(db.JSON)
    requirements_text = db.Column(db.Text, default='')

    # Filesystem path (relative to PROJECTS_DIR)
    path = db.Column(db.String(512), default='')

    # Relationships
    tasks = db.relationship('Task', backref='project', lazy='dynamic')

    __table_args__ = (
        db.UniqueConstraint('name', 'user_id', name='uq_project_name_user'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'framework': self.framework,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'analysis_data': self.analysis_data,
            'requirements_text': self.requirements_text,
            'path': self.path,
        }
