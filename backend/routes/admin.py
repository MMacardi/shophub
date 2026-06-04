from flask import Blueprint, jsonify, g
from werkzeug.security import generate_password_hash
from extensions import db
from models import User, Product, Order
from auth_utils import require_auth

bp = Blueprint('admin', __name__)


@bp.get('/stats')
@require_auth('admin')
def stats():
    users    = User.query.filter(User.role != 'admin').all()
    products = Product.query.count()
    orders   = Order.query.count()
    disabled = sum(1 for u in users if not u.enabled)
    return jsonify(
        totalUsers=len(users),
        sellers=   sum(1 for u in users if u.role == 'seller'),
        buyers=    sum(1 for u in users if u.role == 'buyer'),
        products=  products,
        orders=    orders,
        disabled=  disabled,
    )


@bp.get('/users')
@require_auth('admin')
def list_users():
    users = User.query.filter(User.role != 'admin').order_by(User.created_at.desc()).all()
    return jsonify(users=[{
        'id':        u.id,
        'username':  u.username,
        'email':     u.email,
        'role':      u.role,
        'shopName':  u.shop_name or '',
        'enabled':   u.enabled,
        'createdAt': u.created_at.isoformat(),
    } for u in users])


@bp.post('/users/<int:uid>/toggle')
@require_auth('admin')
def toggle_user(uid):
    user = User.query.get_or_404(uid)
    if user.role == 'admin':
        return jsonify(error='Cannot modify admin'), 403
    user.enabled = not user.enabled
    db.session.commit()
    return jsonify(ok=True, enabled=user.enabled, username=user.username)


@bp.post('/users/<int:uid>/reset-password')
@require_auth('admin')
def reset_password(uid):
    user = User.query.get_or_404(uid)
    if user.role == 'admin':
        return jsonify(error='Cannot modify admin'), 403
    user.password = generate_password_hash('123456')
    db.session.commit()
    return jsonify(ok=True, username=user.username)
