from flask import Blueprint, request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User, Wallet
from auth_utils import create_token, require_auth

bp = Blueprint('auth', __name__)


def user_payload(user):
    return {
        'id':       user.id,
        'username': user.username,
        'role':     user.role,
        'shopName': user.shop_name or '',
        'email':    user.email,
    }


@bp.post('/login')
def login():
    data = request.get_json(force=True)
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    user = User.query.filter(
        db.func.lower(User.username) == username.lower()
    ).first()

    if not user or not check_password_hash(user.password, password):
        return jsonify(error='Invalid username or password.'), 401
    if not user.enabled:
        return jsonify(error='Account is disabled. Contact the administrator.'), 403

    return jsonify(token=create_token(user), user=user_payload(user))


@bp.post('/register')
def register():
    data     = request.get_json(force=True)
    username = (data.get('username') or '').strip()
    email    = (data.get('email')    or '').strip()
    password = data.get('password')  or ''
    role     = data.get('role')      or 'buyer'
    shop_name = (data.get('shopName') or '').strip()

    if role not in ('seller', 'buyer'):
        return jsonify(error='Invalid role.'), 400
    if not username or not email or not password:
        return jsonify(error='All fields are required.'), 400
    if len(password) < 6:
        return jsonify(error='Password must be at least 6 characters.'), 400
    if role == 'seller' and not shop_name:
        return jsonify(error='Shop name is required for sellers.'), 400

    if User.query.filter(db.func.lower(User.username) == username.lower()).first():
        return jsonify(error='Username already taken.'), 409
    if User.query.filter(db.func.lower(User.email) == email.lower()).first():
        return jsonify(error='Email already registered.'), 409

    user = User(
        username=username, email=email,
        password=generate_password_hash(password),
        role=role, shop_name=shop_name if role == 'seller' else '',
        enabled=True,
    )
    db.session.add(user)
    db.session.flush()

    wallet = Wallet(user_id=user.id, balance=1000.0)
    db.session.add(wallet)
    db.session.commit()

    return jsonify(token=create_token(user), user=user_payload(user)), 201


@bp.get('/me')
@require_auth()
def me():
    from models import User as U
    user = U.query.get(g.user_id)
    if not user:
        return jsonify(error='User not found'), 404
    return jsonify(user=user_payload(user))
