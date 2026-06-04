from flask import Blueprint, request, jsonify, g
from extensions import db
from models import CartItem, Product
from auth_utils import require_auth

bp = Blueprint('cart', __name__)


@bp.get('')
@require_auth('buyer')
def get_cart():
    items = CartItem.query.filter_by(buyer_id=g.user_id).all()
    return jsonify(
        cart=[i.to_dict() for i in items],
        count=sum(i.qty for i in items),
    )


@bp.get('/count')
@require_auth('buyer')
def cart_count():
    items = CartItem.query.filter_by(buyer_id=g.user_id).all()
    return jsonify(count=sum(i.qty for i in items))


@bp.post('')
@require_auth('buyer')
def add_to_cart():
    data       = request.get_json(force=True)
    product_id = int(data.get('productId', 0))
    qty        = int(data.get('qty', 1))

    product = Product.query.get(product_id)
    if not product:
        return jsonify(error='Product not found'), 404
    if product.stock < qty:
        return jsonify(error='Not enough stock'), 400

    item = CartItem.query.filter_by(buyer_id=g.user_id, product_id=product_id).first()
    if item:
        item.qty += qty
    else:
        item = CartItem(buyer_id=g.user_id, product_id=product_id, qty=qty)
        db.session.add(item)
    db.session.commit()

    total_count = sum(i.qty for i in CartItem.query.filter_by(buyer_id=g.user_id).all())
    return jsonify(ok=True, count=total_count)


@bp.put('/<int:product_id>')
@require_auth('buyer')
def update_qty(product_id):
    qty  = int(request.get_json(force=True).get('qty', 0))
    item = CartItem.query.filter_by(buyer_id=g.user_id, product_id=product_id).first()
    if not item:
        return jsonify(error='Not in cart'), 404
    if qty <= 0:
        db.session.delete(item)
    else:
        product = Product.query.get(product_id)
        if product and qty > product.stock:
            return jsonify(error='Not enough stock'), 400
        item.qty = qty
    db.session.commit()

    total_count = sum(i.qty for i in CartItem.query.filter_by(buyer_id=g.user_id).all())
    return jsonify(ok=True, count=total_count)


@bp.delete('/<int:product_id>')
@require_auth('buyer')
def remove_from_cart(product_id):
    item = CartItem.query.filter_by(buyer_id=g.user_id, product_id=product_id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
    total_count = sum(i.qty for i in CartItem.query.filter_by(buyer_id=g.user_id).all())
    return jsonify(ok=True, count=total_count)
