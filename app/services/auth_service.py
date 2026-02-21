"""Authentication service layer."""
from datetime import datetime
from app.extensions import db
from app.models.user import User


def get_or_create_user(google_id, email, name, picture_url=''):
    """Find existing user by Google ID or create a new one."""
    user = User.query.filter_by(google_id=google_id).first()
    if not user:
        user = User(
            google_id=google_id,
            email=email,
            name=name,
            picture_url=picture_url,
        )
        db.session.add(user)
    user.last_login = datetime.utcnow()
    db.session.commit()
    return user
