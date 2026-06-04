from flask import Flask
from sqlalchemy import text
from config import Config
from extensions import db
from seed import seed_db
from routes import auth, products, cart, orders, wallet, admin, announcements, sellers, ai


# Lightweight migrations for SQLite — adds new columns to existing tables.
MIGRATIONS = [
    "ALTER TABLE products ADD COLUMN original_price FLOAT",
]


def run_migrations():
    for sql in MIGRATIONS:
        try:
            db.session.execute(text(sql))
            db.session.commit()
        except Exception:
            db.session.rollback()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    app.register_blueprint(auth.bp,          url_prefix='/api/auth')
    app.register_blueprint(products.bp,      url_prefix='/api/products')
    app.register_blueprint(cart.bp,          url_prefix='/api/cart')
    app.register_blueprint(orders.bp,        url_prefix='/api/orders')
    app.register_blueprint(wallet.bp,        url_prefix='/api/wallet')
    app.register_blueprint(admin.bp,         url_prefix='/api/admin')
    app.register_blueprint(announcements.bp, url_prefix='/api/announcements')
    app.register_blueprint(sellers.bp,       url_prefix='/api/sellers')
    app.register_blueprint(ai.bp,            url_prefix='/api/ai')

    with app.app_context():
        db.create_all()
        run_migrations()
        seed_db()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000)
