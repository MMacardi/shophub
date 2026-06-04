from flask import Blueprint, jsonify, g
from extensions import db
from models import CartItem, Order, OrderItem, Product, Wallet
from auth_utils import require_auth

bp = Blueprint('orders', __name__)


@bp.get('')
@require_auth('buyer', 'seller')
def get_orders():
    if g.role == 'buyer':
        orders = Order.query.filter_by(buyer_id=g.user_id).order_by(Order.created_at.desc()).all()
        return jsonify(orders=[o.to_dict() for o in orders])

    # seller: orders that contain their products
    orders = (Order.query
              .join(OrderItem, Order.id == OrderItem.order_id)
              .filter(OrderItem.seller_id == g.user_id)
              .distinct()
              .order_by(Order.created_at.desc())
              .all())
    return jsonify(orders=[o.to_dict() for o in orders])


@bp.post('')
@require_auth('buyer')
def checkout():
    cart_items = CartItem.query.filter_by(buyer_id=g.user_id).all()
    if not cart_items:
        return jsonify(error='Cart is empty'), 400

    wallet = Wallet.query.get(g.user_id)
    if not wallet:
        return jsonify(error='Wallet not found'), 400

    total = 0
    line_items = []
    for ci in cart_items:
        p = Product.query.get(ci.product_id)
        if not p:
            return jsonify(error=f'Product {ci.product_id} no longer exists'), 400
        if p.stock < ci.qty:
            return jsonify(error=f'Not enough stock for {p.name}'), 400
        line_total = p.price * ci.qty
        total     += line_total
        line_items.append((ci, p))

    if wallet.balance < total:
        return jsonify(error='Insufficient wallet balance'), 400

    order = Order(buyer_id=g.user_id, status='completed', total=total)
    db.session.add(order)
    db.session.flush()

    for ci, p in line_items:
        db.session.add(OrderItem(
            order_id=order.id, product_id=p.id, seller_id=p.seller_id,
            name=p.name, price=p.price, qty=ci.qty,
        ))
        p.stock = max(0, p.stock - ci.qty)
        db.session.delete(ci)

    wallet.balance -= total
    db.session.commit()

    return jsonify(order=order.to_dict()), 201
