from datetime import datetime
from extensions import db


class User(db.Model):
    __tablename__ = 'users'
    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(80), unique=True, nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(256), nullable=False)
    role       = db.Column(db.String(20), nullable=False)  # admin / seller / buyer
    shop_name  = db.Column(db.String(120), default='')
    enabled    = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    products   = db.relationship('Product', backref='seller', lazy=True,
                                 foreign_keys='Product.seller_id')
    cart_items = db.relationship('CartItem', backref='buyer', lazy=True)
    orders     = db.relationship('Order', backref='buyer', lazy=True)
    wallet     = db.relationship('Wallet', backref='owner', uselist=False, lazy=True)


class Product(db.Model):
    __tablename__ = 'products'
    id             = db.Column(db.Integer, primary_key=True)
    seller_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name           = db.Column(db.String(200), nullable=False)
    category       = db.Column(db.String(80), nullable=False)
    price          = db.Column(db.Float, nullable=False)
    original_price = db.Column(db.Float, nullable=True)  # null = no discount
    stock          = db.Column(db.Integer, default=0)
    emoji          = db.Column(db.String(8), default='📦')
    description    = db.Column(db.Text, default='')

    def to_dict(self):
        op = self.original_price if (self.original_price and self.original_price > self.price) else None
        discount_pct = round((op - self.price) / op * 100) if op else 0
        reviews = Review.query.filter_by(product_id=self.id).all()
        avg = round(sum(r.rating for r in reviews) / len(reviews), 1) if reviews else 0
        # Seller-wide rating = average across all the seller's product reviews.
        all_seller_reviews = (db.session.query(Review)
                              .join(Product, Product.id == Review.product_id)
                              .filter(Product.seller_id == self.seller_id)
                              .all())
        seller_avg = round(sum(r.rating for r in all_seller_reviews) / len(all_seller_reviews), 1) if all_seller_reviews else 0
        return {
            'id':                self.id,
            'sellerId':          self.seller_id,
            'sellerName':        self.seller.shop_name or self.seller.username,
            'sellerRating':      seller_avg,
            'sellerReviewCount': len(all_seller_reviews),
            'name':              self.name,
            'category':          self.category,
            'price':             self.price,
            'originalPrice':     op,
            'discountPct':       discount_pct,
            'stock':             self.stock,
            'emoji':             self.emoji,
            'description':       self.description,
            'avgRating':         avg,
            'reviewCount':       len(reviews),
        }


class Review(db.Model):
    __tablename__ = 'reviews'
    id         = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'),    nullable=False)
    username   = db.Column(db.String(80), nullable=False)
    rating     = db.Column(db.Integer, nullable=False)   # 1–5
    comment    = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':        self.id,
            'productId': self.product_id,
            'userId':    self.user_id,
            'username':  self.username,
            'rating':    self.rating,
            'comment':   self.comment,
            'createdAt': self.created_at.isoformat(),
        }


class SellerReview(db.Model):
    __tablename__ = 'seller_reviews'
    id         = db.Column(db.Integer, primary_key=True)
    seller_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    username   = db.Column(db.String(80), nullable=False)
    rating     = db.Column(db.Integer, nullable=False)   # 1–5
    comment    = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':        self.id,
            'sellerId':  self.seller_id,
            'userId':    self.user_id,
            'username':  self.username,
            'rating':    self.rating,
            'comment':   self.comment,
            'createdAt': self.created_at.isoformat(),
        }


class Announcement(db.Model):
    __tablename__ = 'announcements'
    id         = db.Column(db.Integer, primary_key=True)
    title      = db.Column(db.String(200), nullable=False)
    content    = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':        self.id,
            'title':     self.title,
            'content':   self.content,
            'createdAt': self.created_at.isoformat(),
        }


class CartItem(db.Model):
    __tablename__ = 'cart_items'
    id         = db.Column(db.Integer, primary_key=True)
    buyer_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    qty        = db.Column(db.Integer, default=1)

    product = db.relationship('Product')

    def to_dict(self):
        p = self.product
        return {
            'pid': self.product_id,
            'qty': self.qty,
            'product': p.to_dict() if p else None,
        }


class Order(db.Model):
    __tablename__ = 'orders'
    id         = db.Column(db.Integer, primary_key=True)
    buyer_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status     = db.Column(db.String(40), default='completed')
    total      = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('OrderItem', backref='order', lazy=True)

    def to_dict(self):
        return {
            'id':         self.id,
            'buyerId':    self.buyer_id,
            'buyerName':  self.buyer.username,
            'status':     self.status,
            'total':      self.total,
            'createdAt':  self.created_at.isoformat(),
            'items': [{
                'productId': i.product_id,
                'sellerId':  i.seller_id,
                'name':      i.name,
                'price':     i.price,
                'qty':       i.qty,
            } for i in self.items],
        }


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id         = db.Column(db.Integer, primary_key=True)
    order_id   = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    seller_id  = db.Column(db.Integer, nullable=False)
    name       = db.Column(db.String(200), nullable=False)
    price      = db.Column(db.Float, nullable=False)
    qty        = db.Column(db.Integer, nullable=False)


class Wallet(db.Model):
    __tablename__ = 'wallets'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    balance = db.Column(db.Float, default=1000.0)
