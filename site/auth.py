from flask import session
import hashlib

def init_auth(app):
    app.secret_key = 'your-very-secret-key-123'

def authorize_user(user_id):
    session['user_id'] = user_id
    session['auth_hash'] = _generate_auth_hash(user_id)

def is_authenticated():
    if 'user_id' in session and 'auth_hash' in session:
        return session['auth_hash'] == _generate_auth_hash(session['user_id'])
    return False

def get_current_user():
    return session.get('user_id') if is_authenticated() else None

def _generate_auth_hash(user_id):
    secret_salt = "your-app-salt-456"
    return hashlib.sha256(f"{user_id}{secret_salt}".encode()).hexdigest()