from flask import Blueprint, request, jsonify, g
from extensions import db
from models import User, Product, SellerReview, Review, Order, OrderItem
from auth_utils import require_auth

bp = Blueprint('sellers', __name__)


def _seller_summary(seller):
    # Rating = average of ALL product reviews across the seller's catalog.
    # Total review count = sum of reviews across all products.
    product_reviews = (db.session.query(Review)
                       .join(Product, Product.id == Review.product_id)
                       .filter(Product.seller_id == seller.id)
                       .all())
    avg = round(sum(r.rating for r in product_reviews) / len(product_reviews), 1) if product_reviews else 0
    product_count = Product.query.filter_by(seller_id=seller.id).count()
    shop_reviews = SellerReview.query.filter_by(seller_id=seller.id).count()
    return {
        'id':              seller.id,
        'username':        seller.username,
        'shopName':        seller.shop_name or seller.username,
        'avgRating':       avg,
        'reviewCount':     len(product_reviews),
        'productCount':    product_count,
        'shopReviewCount': shop_reviews,
    }


@bp.get('')
def list_sellers():
    sellers = User.query.filter_by(role='seller', enabled=True).all()
    return jsonify(sellers=[_seller_summary(s) for s in sellers])


@bp.get('/<int:sid>')
def get_seller(sid):
    seller = User.query.filter_by(id=sid, role='seller').first_or_404()
    return jsonify(seller=_seller_summary(seller))


@bp.get('/<int:sid>/products')
def list_seller_products(sid):
    User.query.filter_by(id=sid, role='seller').first_or_404()
    products = Product.query.filter_by(seller_id=sid).all()
    return jsonify(products=[p.to_dict() for p in products])


@bp.get('/<int:sid>/reviews')
def list_seller_reviews(sid):
    User.query.filter_by(id=sid, role='seller').first_or_404()
    reviews = (SellerReview.query
               .filter_by(seller_id=sid)
               .order_by(SellerReview.created_at.desc())
               .all())
    return jsonify(reviews=[r.to_dict() for r in reviews])


@bp.post('/<int:sid>/reviews')
@require_auth('buyer')
def create_seller_review(sid):
    User.query.filter_by(id=sid, role='seller').first_or_404()

    bought = (db.session.query(OrderItem)
              .join(Order, Order.id == OrderItem.order_id)
              .filter(Order.buyer_id == g.user_id, OrderItem.seller_id == sid)
              .first())
    if not bought:
        return jsonify(error='You can only review sellers you have bought from.'), 403

    existing = SellerReview.query.filter_by(seller_id=sid, user_id=g.user_id).first()
    if existing:
        return jsonify(error='You have already reviewed this seller.'), 409

    data    = request.get_json(force=True)
    rating  = int(data.get('rating',  0))
    comment = (data.get('comment') or '').strip()

    if not 1 <= rating <= 5:
        return jsonify(error='Rating must be between 1 and 5.'), 400
    if not comment:
        return jsonify(error='Comment cannot be empty.'), 400

    r = SellerReview(seller_id=sid, user_id=g.user_id, username=g.username,
                     rating=rating, comment=comment)
    db.session.add(r)
    db.session.commit()
    return jsonify(review=r.to_dict()), 201
