import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify, g
from config import Config


def create_token(user):
    payload = {
        'sub':      user.id,
        'role':     user.role,
        'username': user.username,
        'exp':      datetime.now(timezone.utc) + timedelta(days=7),
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm='HS256')


def decode_token(token):
    return jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])


def require_auth(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth = request.headers.get('Authorization', '')
            if not auth.startswith('Bearer '):
                return jsonify(error='Unauthorized'), 401
            try:
                payload = decode_token(auth[7:])
                g.user_id  = payload['sub']
                g.role     = payload['role']
                g.username = payload['username']
                if roles and g.role not in roles:
                    return jsonify(error='Forbidden'), 403
            except Exception:
                return jsonify(error='Unauthorized'), 401
            return f(*args, **kwargs)
        return decorated
    return decorator
