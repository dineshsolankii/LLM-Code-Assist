from datetime import datetime
from app.extensions import db


class ChatHistory(db.Model):
    __tablename__ = 'chat_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True, index=True)
    role = db.Column(db.String(50), nullable=False)  # 'user' or 'assistant'
    message = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(50), default='chat')  # requirements, customization, chat, error
    metadata_json = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'role': self.role,
            'message': self.message,
            'message_type': self.message_type,
            'metadata': self.metadata_json,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
