from datetime import datetime
from flask import Blueprint, redirect, url_for, session, request, jsonify, current_app, render_template
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db, oauth

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login')
def login_page():
    """Show login page or redirect to Google OAuth."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    return render_template('login.html')


@auth_bp.route('/google')
def google_login():
    """Redirect to Google OAuth consent screen."""
    if current_app.config.get('SKIP_AUTH'):
        return _dev_login()

    redirect_uri = url_for('auth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route('/google/callback')
def google_callback():
    """Handle Google OAuth callback."""
    if current_app.config.get('SKIP_AUTH'):
        return _dev_login()

    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get('userinfo')
        if not user_info:
            user_info = oauth.google.userinfo()

        from app.models.user import User

        user = User.query.filter_by(google_id=user_info['sub']).first()
        if not user:
            user = User(
                google_id=user_info['sub'],
                email=user_info['email'],
                name=user_info.get('name', user_info.get('email', '')),
                picture_url=user_info.get('picture', ''),
            )
            db.session.add(user)

        user.last_login = datetime.utcnow()
        db.session.commit()

        login_user(user, remember=True)
        return redirect(url_for('main.index'))

    except Exception as e:
        current_app.logger.error(f'OAuth callback error: {e}')
        return redirect(url_for('auth.login_page'))


@auth_bp.route('/logout')
def logout():
    """Log the user out."""
    logout_user()
    session.clear()
    return redirect(url_for('main.index'))


@auth_bp.route('/me')
@login_required
def me():
    """Return current user info."""
    return jsonify({'success': True, 'user': current_user.to_dict()})


@auth_bp.route('/preferences', methods=['GET'])
@login_required
def get_preferences():
    """Get user preferences."""
    return jsonify({'success': True, 'preferences': current_user.preferences or {}})


@auth_bp.route('/preferences', methods=['PUT'])
@login_required
def update_preferences():
    """Update user preferences."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    prefs = current_user.preferences or {}
    prefs.update(data)
    current_user.preferences = prefs
    db.session.commit()
    return jsonify({'success': True, 'preferences': prefs})


def _dev_login():
    """Create or get a development user (when SKIP_AUTH=true)."""
    from app.models.user import User

    user = User.query.filter_by(email='dev@localhost').first()
    if not user:
        user = User(
            google_id='dev-user-001',
            email='dev@localhost',
            name='Developer',
            picture_url='',
        )
        db.session.add(user)
        db.session.commit()

    user.last_login = datetime.utcnow()
    db.session.commit()
    login_user(user, remember=True)
    return redirect(url_for('main.index'))
