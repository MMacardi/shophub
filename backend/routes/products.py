from flask import Blueprint, request, jsonify, g
from extensions import db
from models import Product, Review, Order, OrderItem
from auth_utils import require_auth, decode_token

bp = Blueprint('products', __name__)


@bp.get('')
def list_products():
    q        = (request.args.get('q')        or '').strip().lower()
    category = (request.args.get('category') or '').strip()
    my       = request.args.get('seller') == 'my'

    if my:
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return jsonify(error='Unauthorized'), 401
        from auth_utils import decode_token
        try:
            payload = decode_token(auth[7:])
            seller_id = payload['sub']
        except Exception:
            return jsonify(error='Unauthorized'), 401
        query = Product.query.filter_by(seller_id=seller_id)
    else:
        query = Product.query.filter(Product.stock > 0)

    if category:
        query = query.filter_by(category=category)
    if q:
        query = query.filter(
            db.or_(
                Product.name.ilike(f'%{q}%'),
                Product.category.ilike(f'%{q}%'),
            )
        )

    return jsonify(products=[p.to_dict() for p in query.all()])


@bp.get('/<int:pid>')
def get_product(pid):
    p = Product.query.get_or_404(pid)
    return jsonify(product=p.to_dict())


def _parse_original_price(data, fallback=None):
    raw = data.get('originalPrice')
    if raw in (None, '', 0, '0'):
        return None
    try:
        v = float(raw)
        return v if v > 0 else None
    except (TypeError, ValueError):
        return fallback


@bp.post('')
@require_auth('seller')
def create_product():
    data = request.get_json(force=True)
    p = Product(
        seller_id=g.user_id,
        name=          (data.get('name')        or '').strip(),
        category=      (data.get('category')    or '').strip(),
        price=         float(data.get('price',  0)),
        original_price=_parse_original_price(data),
        stock=         int(data.get('stock',    0)),
        emoji=         (data.get('emoji')       or '📦').strip(),
        description=   (data.get('description') or '').strip(),
    )
    if not p.name or not p.category or p.price <= 0:
        return jsonify(error='name, category and price are required'), 400
    db.session.add(p)
    db.session.commit()
    return jsonify(product=p.to_dict()), 201


@bp.put('/<int:pid>')
@require_auth('seller')
def update_product(pid):
    p = Product.query.get_or_404(pid)
    if p.seller_id != g.user_id:
        return jsonify(error='Forbidden'), 403
    data = request.get_json(force=True)
    p.name           = (data.get('name')        or p.name).strip()
    p.category       = (data.get('category')    or p.category).strip()
    p.price          = float(data.get('price',  p.price))
    p.original_price = _parse_original_price(data, fallback=p.original_price)
    p.stock          = int(data.get('stock',    p.stock))
    p.emoji          = (data.get('emoji')       or p.emoji).strip()
    p.description    = (data.get('description', p.description) or '').strip()
    db.session.commit()
    return jsonify(product=p.to_dict())


@bp.delete('/<int:pid>')
@require_auth('seller')
def delete_product(pid):
    p = Product.query.get_or_404(pid)
    if p.seller_id != g.user_id:
        return jsonify(error='Forbidden'), 403
    db.session.delete(p)
    db.session.commit()
    return jsonify(ok=True)


# ── Reviews ───────────────────────────────────────────────

@bp.get('/<int:pid>/reviews')
def list_reviews(pid):
    Product.query.get_or_404(pid)
    reviews = Review.query.filter_by(product_id=pid).order_by(Review.created_at.desc()).all()
    return jsonify(reviews=[r.to_dict() for r in reviews])


@bp.post('/<int:pid>/reviews')
@require_auth('buyer')
def create_review(pid):
    Product.query.get_or_404(pid)

    bought = (db.session.query(OrderItem)
              .join(Order, Order.id == OrderItem.order_id)
              .filter(Order.buyer_id == g.user_id, OrderItem.product_id == pid)
              .first())
    if not bought:
        return jsonify(error='You can only review products you have purchased.'), 403

    existing = Review.query.filter_by(product_id=pid, user_id=g.user_id).first()
    if existing:
        return jsonify(error='You have already reviewed this product.'), 409

    data    = request.get_json(force=True)
    rating  = int(data.get('rating',  0))
    comment = (data.get('comment') or '').strip()

    if not 1 <= rating <= 5:
        return jsonify(error='Rating must be between 1 and 5.'), 400
    if not comment:
        return jsonify(error='Comment cannot be empty.'), 400

    r = Review(product_id=pid, user_id=g.user_id, username=g.username,
               rating=rating, comment=comment)
    db.session.add(r)
    db.session.commit()
    return jsonify(review=r.to_dict()), 201


@bp.delete('/<int:pid>/reviews/<int:rid>')
@require_auth('buyer', 'admin')
def delete_review(pid, rid):
    r = Review.query.get_or_404(rid)
    if g.role != 'admin' and r.user_id != g.user_id:
        return jsonify(error='Forbidden'), 403
    db.session.delete(r)
    db.session.commit()
    return jsonify(ok=True)
