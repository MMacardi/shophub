"""
AI shopping assistant — Aliyun DashScope (OpenAI-compatible) + tool use.

Flow:
- Frontend POSTs the running message list to /api/ai/chat
- The model decides which tools to call (search_products, get_product_details,
  get_seller_reviews, add_to_cart, checkout_now)
- We execute the tool calls server-side (cart/checkout use the buyer's JWT)
- We loop until the model returns a final text reply
"""
import json
import re
import ssl
import time
import urllib.request
import urllib.error

from flask import Blueprint, request, jsonify, g
from extensions import db
from models import Product, Review, User, SellerReview, CartItem, Order, OrderItem, Wallet
from auth_utils import decode_token
from config import Config

bp = Blueprint('ai', __name__)


SYSTEM_PROMPT = """You are ShopHub's AI shopping assistant.

You help buyers find products, compare them, see reviews, add items to cart and
check out. You can call tools to search the catalog and perform cart actions.

Guidelines:
- Always reply in English.
- When the user describes what they want, call `search_products` first.

Search tips — this is important:
- The catalog has only ~50 products, so prefer SHORT, GENERIC queries (1–2 words)
  over long descriptive ones. The search ranks by relevance, so a short query
  returns the best candidates anyway.
- BAD query: "low sugar protein bar for fitness". GOOD query: "protein bar".
- BAD query: "warm winter coat for cold weather". GOOD query: "coat".
- If a search returns 0 results, DO NOT repeat almost the same query. Simplify
  to the most generic noun (e.g. "snack", "shoes", "skirt") or switch to a
  category like "Food", "Sports", "Fashion", "Electronics", "Home", "Beauty".
- After you have the candidates, YOU pick the best one based on the user's
  full intent (price, rating, low-sugar / high-protein / etc.) by reading the
  product description in the result — do not re-search just to narrow down.

Recommending:
- Pick ONE best match and explain WHY: price, rating, stock, key features.
  Briefly mention the seller's shop name and rating.
- Quote 1–2 short customer reviews of the product when relevant.
- ALWAYS end your recommendation message with the product's price on its own
  line, formatted exactly like: `**Price: ¥<amount>**` (e.g. `**Price: ¥99**`).
  If there is a discount, show both like: `**Price: ¥99 (was ¥149)**`.
- Before adding anything to cart, ASK the user to confirm.
- After the item is added to cart and the user wants to pay:
  1. Call `get_wallet_balance` to fetch their current balance.
  2. Tell the user: "Your wallet balance is ¥X. The total is ¥Y. Shall I pay now?"
  3. Only call `checkout_now` AFTER the user explicitly confirms.
- If the user asks how much money they have, call `get_wallet_balance`.

Cart management:
- To remove an item, call `remove_from_cart` (or `update_cart_qty` with qty=0).
- To change the quantity, call `update_cart_qty`.
- To empty the whole cart, call `clear_cart` (ask the user first).
- NEVER claim you removed/updated an item without actually calling a tool.
  If you say "Done, removed X" the user expects the cart to actually change.

Things to NEVER show the user:
- Internal product IDs, seller IDs, review IDs, order IDs from tool results.
  These are for your tool calls only — keep them out of the chat reply.
  Refer to products by NAME only.
  ❌ BAD: "Protein Bar Variety Box — ID: 50, ¥99"
  ✅ GOOD: "Protein Bar Variety Box — ¥99"
- Raw JSON, field names like `sellerId`, `avgRating`, etc.
- Any debug output or note that you "called a tool".

Strict rules:
- NEVER invent product IDs, prices, names, or reviews. Only use data returned
  by the tools in THIS conversation.
- When calling `get_product_details`, `add_to_cart`, or `get_seller_reviews`,
  use ONLY ids you received from `search_products` earlier in this conversation.
- If you don't know an id, call `search_products` again — do not guess.
- If a tool call fails (e.g. user not logged in, low balance, product not found),
  explain clearly and suggest what to do.
- Keep replies short and friendly. Prices are in ¥ (yuan).
"""


SELLER_PROMPT = """You are signed in as a SELLER. Besides shopping tools, you
can manage your own catalog:

- `list_my_products` — show all your products with id, name, price, stock.
- `update_my_product` — change name / description / price / stock / category /
  emoji / originalPrice on one of YOUR products. Pass only the fields the user
  wants changed.
- `create_my_product` — add a brand new product to your shop.
- `delete_my_product` — remove one of your products (always confirm first).
- `polish_product_description` — given a rough description + product name +
  category, returns an improved marketing-friendly version. Use this when the
  user asks you to "make the description better" or similar.
- `get_seller_orders` — show the seller's recent orders.

Seller workflow rules:
- Before mutating anything (update / create / delete), summarise the change and
  ASK the user to confirm.
- After a successful mutation, briefly state what changed (don't dump JSON).
- When the user says "add a new product" but only gives partial info, ask
  follow-up questions to gather: name, category, price, stock — emoji and
  description can be inferred or asked optionally.
- You may freely call `polish_product_description` and propose the improved
  text — but only call `update_my_product` once the user accepts it.
"""


# ── Tool definitions exposed to the model ─────────────────────────
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "Search the catalog. Returns up to 8 matching products with id, name, price, rating, stock and seller info.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query":     {"type": "string", "description": "Free-text query, e.g. 'wireless earbuds'"},
                    "category":  {"type": "string", "description": "Optional category filter: Electronics / Fashion / Home / Beauty / Sports / Food / Toys"},
                    "max_price": {"type": "number", "description": "Optional maximum price in yuan"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_details",
            "description": "Get full details for one product: description, up to 5 latest reviews, and seller summary with the seller's average rating.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer"},
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_seller_reviews",
            "description": "Get up to 5 latest reviews about a seller (overall shop reputation).",
            "parameters": {
                "type": "object",
                "properties": {
                    "seller_id": {"type": "integer"},
                },
                "required": ["seller_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_to_cart",
            "description": "Add a product to the logged-in buyer's cart. Requires the user to be signed in as a buyer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer"},
                    "qty":        {"type": "integer", "description": "Quantity, default 1"},
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_cart_qty",
            "description": "Change the quantity of an item already in the buyer's cart. Pass qty=0 to remove the item entirely.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer"},
                    "qty":        {"type": "integer", "description": "New quantity. 0 removes the item."},
                },
                "required": ["product_id", "qty"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remove_from_cart",
            "description": "Remove a product from the buyer's cart entirely (regardless of quantity).",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer"},
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "clear_cart",
            "description": "Remove ALL items from the buyer's cart. Ask the user to confirm before calling.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "checkout_now",
            "description": "Pay for everything currently in the cart from the buyer's wallet balance. Only call after the user has agreed to pay.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "view_cart",
            "description": "Look at what is currently in the buyer's cart and the total price.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_wallet_balance",
            "description": "Get the buyer's current wallet balance in yuan. Always call this before checkout, or whenever the user asks how much money they have.",
            "parameters": {"type": "object", "properties": {}},
        },
    },

    # ── Seller-only tools ──────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "list_my_products",
            "description": "Seller only. Returns the seller's own products with id, name, category, price, stock and a short description preview.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_my_product",
            "description": "Seller only. Edit one of the seller's own products. Pass only the fields the user actually wants changed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id":    {"type": "integer"},
                    "name":          {"type": "string"},
                    "category":      {"type": "string"},
                    "price":         {"type": "number"},
                    "originalPrice": {"type": "number", "description": "Original (pre-discount) price. Pass 0 to clear it."},
                    "stock":         {"type": "integer"},
                    "emoji":         {"type": "string"},
                    "description":   {"type": "string"},
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_my_product",
            "description": "Seller only. Create a brand new product under the current seller's shop.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name":          {"type": "string"},
                    "category":      {"type": "string", "description": "Electronics / Fashion / Home / Beauty / Sports / Food / Toys / Other"},
                    "price":         {"type": "number"},
                    "originalPrice": {"type": "number"},
                    "stock":         {"type": "integer"},
                    "emoji":         {"type": "string"},
                    "description":   {"type": "string"},
                },
                "required": ["name", "category", "price", "stock"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_my_product",
            "description": "Seller only. Permanently delete one of the seller's products. Always ask the user to confirm before calling.",
            "parameters": {
                "type": "object",
                "properties": {"product_id": {"type": "integer"}},
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "polish_product_description",
            "description": "Seller only. Rewrite a product description into clearer, marketing-friendly copy. Returns the improved text — do not auto-save it, propose to the user first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name":     {"type": "string"},
                    "category": {"type": "string"},
                    "hint":     {"type": "string", "description": "The seller's rough notes about the product."},
                },
                "required": ["name", "hint"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_seller_orders",
            "description": "Seller only. Returns the seller's recent orders (latest 10) with totals and items.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


# ── Helpers ───────────────────────────────────────────────────────
def _current_user():
    """Decode JWT if present. Returns User or None — anonymous use is OK for search."""
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    try:
        payload = decode_token(auth[7:])
        return User.query.get(payload['sub'])
    except Exception:
        return None


def _product_card(p):
    reviews = Review.query.filter_by(product_id=p.id).all()
    avg = round(sum(r.rating for r in reviews) / len(reviews), 1) if reviews else 0
    seller_reviews = SellerReview.query.filter_by(seller_id=p.seller_id).all()
    seller_avg = round(sum(r.rating for r in seller_reviews) / len(seller_reviews), 1) if seller_reviews else 0
    return {
        'id':              p.id,
        'name':            p.name,
        'category':        p.category,
        'price':           p.price,
        'originalPrice':   p.original_price,
        'stock':           p.stock,
        'avgRating':       avg,
        'reviewCount':     len(reviews),
        'sellerId':        p.seller_id,
        'sellerName':      p.seller.shop_name or p.seller.username,
        'sellerRating':    seller_avg,
        'sellerReviewCount': len(seller_reviews),
    }


# ── Tool implementations ──────────────────────────────────────────
# Common stop-words we strip from queries so things like
# "I want a low sugar protein bar" still match "Protein Bar".
_STOP = {
    'a','an','the','for','with','and','or','of','in','on','at','to','my','me',
    'i','want','need','looking','please','some','any','that','this','it','is',
    'are','can','you','recommend','show','find','get','give','help','something',
    'thing','things','sweet','snack','snacks',
}


def _tokens(q):
    raw = re.split(r'[^a-z0-9]+', (q or '').lower())
    return [t for t in raw if len(t) >= 3 and t not in _STOP]


def tool_search_products(args, user):
    q = (args.get('query') or '').strip().lower()
    category = (args.get('category') or '').strip()
    max_price = args.get('max_price')

    query = Product.query.filter(Product.stock > 0)
    if category:
        query = query.filter(Product.category.ilike(category))

    tokens = _tokens(q)
    if tokens:
        # Match products where ANY meaningful token appears in name/category/description.
        # Ranking below prefers products matching MORE tokens.
        clauses = []
        for t in tokens:
            pattern = f'%{t}%'
            clauses.append(db.or_(
                Product.name.ilike(pattern),
                Product.category.ilike(pattern),
                Product.description.ilike(pattern),
            ))
        query = query.filter(db.or_(*clauses))
    elif q:
        # No useful tokens left after stop-word removal — fall back to raw substring.
        pattern = f'%{q}%'
        query = query.filter(db.or_(
            Product.name.ilike(pattern),
            Product.category.ilike(pattern),
            Product.description.ilike(pattern),
        ))

    products = query.all()
    if max_price:
        try:
            cap = float(max_price)
            products = [p for p in products if p.price <= cap]
        except (TypeError, ValueError):
            pass

    # Rank: (1) most tokens matched, (2) higher rating, (3) more stock, (4) cheaper
    def _score(p):
        text = ((p.name or '') + ' ' + (p.category or '') + ' ' + (p.description or '')).lower()
        match_count = sum(1 for t in tokens if t in text)
        reviews = Review.query.filter_by(product_id=p.id).all()
        avg = (sum(r.rating for r in reviews) / len(reviews)) if reviews else 0
        return (-match_count, -avg, -p.stock, p.price)

    products.sort(key=_score)
    cards = [_product_card(p) for p in products[:8]]
    return {'count': len(cards), 'products': cards, 'tokens': tokens}


def tool_get_product_details(args, user):
    pid = int(args.get('product_id', 0))
    p = Product.query.get(pid)
    if not p:
        return {'error': f'Product {pid} not found.'}
    reviews = (Review.query.filter_by(product_id=pid)
               .order_by(Review.created_at.desc())
               .limit(5).all())
    card = _product_card(p)
    card['description'] = p.description
    card['reviews'] = [{
        'username': r.username, 'rating': r.rating, 'comment': r.comment,
    } for r in reviews]
    return card


def tool_get_seller_reviews(args, user):
    sid = int(args.get('seller_id', 0))
    seller = User.query.filter_by(id=sid, role='seller').first()
    if not seller:
        return {'error': f'Seller {sid} not found.'}
    reviews = (SellerReview.query.filter_by(seller_id=sid)
               .order_by(SellerReview.created_at.desc())
               .limit(5).all())
    all_reviews = SellerReview.query.filter_by(seller_id=sid).all()
    avg = round(sum(r.rating for r in all_reviews) / len(all_reviews), 1) if all_reviews else 0
    return {
        'sellerId':   sid,
        'shopName':   seller.shop_name or seller.username,
        'avgRating':  avg,
        'reviewCount': len(all_reviews),
        'reviews': [{
            'username': r.username, 'rating': r.rating, 'comment': r.comment,
        } for r in reviews],
    }


def tool_add_to_cart(args, user):
    if not user or user.role != 'buyer':
        return {'error': 'Please sign in as a buyer first to add items to cart.'}
    pid = int(args.get('product_id', 0))
    qty = int(args.get('qty', 1) or 1)
    p = Product.query.get(pid)
    if not p:
        return {'error': f'Product {pid} not found.'}
    if p.stock < qty:
        return {'error': f'Only {p.stock} in stock for "{p.name}".'}
    item = CartItem.query.filter_by(buyer_id=user.id, product_id=pid).first()
    if item:
        item.qty += qty
    else:
        item = CartItem(buyer_id=user.id, product_id=pid, qty=qty)
        db.session.add(item)
    db.session.commit()
    total_count = sum(i.qty for i in CartItem.query.filter_by(buyer_id=user.id).all())
    return {
        'ok': True,
        'message': f'Added {qty} × "{p.name}" to your cart.',
        'cartCount': total_count,
    }


def tool_update_cart_qty(args, user):
    if not user or user.role != 'buyer':
        return {'error': 'Please sign in as a buyer first.'}
    pid = int(args.get('product_id', 0))
    qty = int(args.get('qty', 0))
    item = CartItem.query.filter_by(buyer_id=user.id, product_id=pid).first()
    if not item:
        return {'error': f'Product {pid} is not in your cart.'}
    name = item.product.name if item.product else f'product {pid}'
    if qty <= 0:
        db.session.delete(item)
        db.session.commit()
        total_count = sum(i.qty for i in CartItem.query.filter_by(buyer_id=user.id).all())
        return {'ok': True, 'removed': True, 'message': f'Removed "{name}" from cart.', 'cartCount': total_count}
    p = Product.query.get(pid)
    if p and qty > p.stock:
        return {'error': f'Only {p.stock} of "{name}" in stock.'}
    item.qty = qty
    db.session.commit()
    total_count = sum(i.qty for i in CartItem.query.filter_by(buyer_id=user.id).all())
    return {'ok': True, 'message': f'Quantity of "{name}" set to {qty}.', 'cartCount': total_count}


def tool_remove_from_cart(args, user):
    if not user or user.role != 'buyer':
        return {'error': 'Please sign in as a buyer first.'}
    pid = int(args.get('product_id', 0))
    item = CartItem.query.filter_by(buyer_id=user.id, product_id=pid).first()
    if not item:
        return {'error': f'Product {pid} was not in your cart.'}
    name = item.product.name if item.product else f'product {pid}'
    db.session.delete(item)
    db.session.commit()
    total_count = sum(i.qty for i in CartItem.query.filter_by(buyer_id=user.id).all())
    return {'ok': True, 'message': f'Removed "{name}" from cart.', 'cartCount': total_count}


def tool_clear_cart(args, user):
    if not user or user.role != 'buyer':
        return {'error': 'Please sign in as a buyer first.'}
    items = CartItem.query.filter_by(buyer_id=user.id).all()
    if not items:
        return {'ok': True, 'message': 'Cart was already empty.', 'cartCount': 0}
    for i in items:
        db.session.delete(i)
    db.session.commit()
    return {'ok': True, 'message': f'Removed all {len(items)} item(s) from cart.', 'cartCount': 0}


def tool_view_cart(args, user):
    if not user or user.role != 'buyer':
        return {'error': 'Please sign in as a buyer first.'}
    items = CartItem.query.filter_by(buyer_id=user.id).all()
    if not items:
        return {'empty': True, 'items': [], 'total': 0}
    lines = []
    total = 0
    for ci in items:
        p = Product.query.get(ci.product_id)
        if not p:
            continue
        lines.append({
            'productId': p.id, 'name': p.name, 'qty': ci.qty,
            'price': p.price, 'lineTotal': round(p.price * ci.qty, 2),
        })
        total += p.price * ci.qty
    wallet = Wallet.query.get(user.id)
    return {
        'items': lines,
        'total': round(total, 2),
        'walletBalance': wallet.balance if wallet else 0,
    }


def tool_get_wallet_balance(args, user):
    if not user or user.role != 'buyer':
        return {'error': 'Please sign in as a buyer first.'}
    wallet = Wallet.query.get(user.id)
    return {
        'balance': round(wallet.balance, 2) if wallet else 0,
        'currency': 'CNY',
    }


def tool_checkout_now(args, user):
    if not user or user.role != 'buyer':
        return {'error': 'Please sign in as a buyer first.'}
    items = CartItem.query.filter_by(buyer_id=user.id).all()
    if not items:
        return {'error': 'Your cart is empty.'}

    wallet = Wallet.query.get(user.id)
    if not wallet:
        return {'error': 'Wallet not found.'}

    total = 0
    lines = []
    for ci in items:
        p = Product.query.get(ci.product_id)
        if not p:
            return {'error': f'Product {ci.product_id} no longer exists.'}
        if p.stock < ci.qty:
            return {'error': f'Not enough stock for "{p.name}".'}
        total += p.price * ci.qty
        lines.append((ci, p))

    if wallet.balance < total:
        return {
            'error': f'Insufficient wallet balance. Needed ¥{total:.2f}, have ¥{wallet.balance:.2f}. Top up first.',
        }

    order = Order(buyer_id=user.id, status='completed', total=total)
    db.session.add(order)
    db.session.flush()
    for ci, p in lines:
        db.session.add(OrderItem(
            order_id=order.id, product_id=p.id, seller_id=p.seller_id,
            name=p.name, price=p.price, qty=ci.qty,
        ))
        p.stock = max(0, p.stock - ci.qty)
        db.session.delete(ci)
    wallet.balance -= total
    db.session.commit()
    return {
        'ok': True,
        'orderId': order.id,
        'total': round(total, 2),
        'newWalletBalance': round(wallet.balance, 2),
        'message': f'Order #{order.id} paid. ¥{total:.2f} deducted from your wallet.',
    }


# ── Seller-only tool implementations ─────────────────────────────
ALLOWED_CATEGORIES = {'Electronics','Fashion','Home','Beauty','Sports','Food','Toys','Other'}


def _my_product(user, pid):
    p = Product.query.get(int(pid))
    if not p:
        return None, {'error': f'Product {pid} not found.'}
    if p.seller_id != user.id:
        return None, {'error': "That product isn't in your shop."}
    return p, None


def tool_list_my_products(args, user):
    if not user or user.role != 'seller':
        return {'error': 'Please sign in as a seller first.'}
    products = Product.query.filter_by(seller_id=user.id).all()
    return {
        'count': len(products),
        'products': [{
            'id':            p.id,
            'name':          p.name,
            'category':      p.category,
            'price':         p.price,
            'originalPrice': p.original_price,
            'stock':         p.stock,
            'emoji':         p.emoji,
            'descriptionPreview': (p.description or '')[:120],
        } for p in products],
    }


def tool_update_my_product(args, user):
    if not user or user.role != 'seller':
        return {'error': 'Please sign in as a seller first.'}
    p, err = _my_product(user, args.get('product_id'))
    if err:
        return err

    changed = {}
    if 'name' in args and args['name']:
        p.name = str(args['name']).strip(); changed['name'] = p.name
    if 'category' in args and args['category']:
        cat = str(args['category']).strip()
        if cat not in ALLOWED_CATEGORIES:
            return {'error': f'Category must be one of {sorted(ALLOWED_CATEGORIES)}.'}
        p.category = cat; changed['category'] = cat
    if 'price' in args and args['price'] is not None:
        try:
            v = float(args['price'])
            if v <= 0: return {'error': 'Price must be greater than 0.'}
            p.price = v; changed['price'] = v
        except (TypeError, ValueError):
            return {'error': 'Invalid price.'}
    if 'originalPrice' in args:
        raw = args['originalPrice']
        if raw in (None, 0, '', '0'):
            p.original_price = None; changed['originalPrice'] = None
        else:
            try:
                v = float(raw)
                if v <= p.price:
                    return {'error': 'originalPrice must be higher than the sale price.'}
                p.original_price = v; changed['originalPrice'] = v
            except (TypeError, ValueError):
                return {'error': 'Invalid originalPrice.'}
    if 'stock' in args and args['stock'] is not None:
        try:
            v = int(args['stock'])
            if v < 0: return {'error': 'Stock cannot be negative.'}
            p.stock = v; changed['stock'] = v
        except (TypeError, ValueError):
            return {'error': 'Invalid stock.'}
    if 'emoji' in args and args['emoji']:
        p.emoji = str(args['emoji']).strip()[:4]; changed['emoji'] = p.emoji
    if 'description' in args and args['description'] is not None:
        p.description = str(args['description']).strip(); changed['description'] = p.description[:80] + ('…' if len(p.description) > 80 else '')

    if not changed:
        return {'error': 'Nothing to update — pass at least one field besides product_id.'}

    db.session.commit()
    return {'ok': True, 'productId': p.id, 'name': p.name, 'changed': changed}


def tool_create_my_product(args, user):
    if not user or user.role != 'seller':
        return {'error': 'Please sign in as a seller first.'}
    name = str(args.get('name') or '').strip()
    category = str(args.get('category') or '').strip()
    try:
        price = float(args.get('price', 0))
    except (TypeError, ValueError):
        return {'error': 'Invalid price.'}
    try:
        stock = int(args.get('stock', 0))
    except (TypeError, ValueError):
        return {'error': 'Invalid stock.'}

    if not name or not category or price <= 0 or stock < 0:
        return {'error': 'name, category, price (>0) and stock (>=0) are required.'}
    if category not in ALLOWED_CATEGORIES:
        return {'error': f'Category must be one of {sorted(ALLOWED_CATEGORIES)}.'}

    original_price = None
    if args.get('originalPrice') not in (None, '', 0, '0'):
        try:
            op = float(args['originalPrice'])
            if op > price: original_price = op
        except (TypeError, ValueError):
            pass

    p = Product(
        seller_id=user.id,
        name=name, category=category, price=price,
        original_price=original_price, stock=stock,
        emoji=(str(args.get('emoji') or '📦').strip()[:4]),
        description=str(args.get('description') or '').strip(),
    )
    db.session.add(p)
    db.session.commit()
    return {
        'ok': True, 'productId': p.id, 'name': p.name,
        'message': f'Created "{p.name}" — ¥{p.price}, stock {p.stock}.',
    }


def tool_delete_my_product(args, user):
    if not user or user.role != 'seller':
        return {'error': 'Please sign in as a seller first.'}
    p, err = _my_product(user, args.get('product_id'))
    if err:
        return err
    name = p.name
    db.session.delete(p)
    db.session.commit()
    return {'ok': True, 'message': f'Deleted "{name}".'}


def tool_get_seller_orders(args, user):
    if not user or user.role != 'seller':
        return {'error': 'Please sign in as a seller first.'}
    orders = (Order.query
              .join(OrderItem, Order.id == OrderItem.order_id)
              .filter(OrderItem.seller_id == user.id)
              .distinct()
              .order_by(Order.created_at.desc())
              .limit(10).all())
    out = []
    for o in orders:
        out.append({
            'orderId':   o.id,
            'buyer':     o.buyer.username,
            'total':     round(o.total, 2),
            'createdAt': o.created_at.isoformat()[:10],
            'items': [{'name': i.name, 'qty': i.qty, 'price': i.price}
                      for i in o.items if i.seller_id == user.id],
        })
    return {'count': len(out), 'orders': out}


def tool_polish_product_description(args, user):
    """Calls DashScope to enhance a rough description. Seller only."""
    if not user or user.role != 'seller':
        return {'error': 'Please sign in as a seller first.'}
    name = (args.get('name') or '').strip()
    category = (args.get('category') or '').strip()
    hint = (args.get('hint') or '').strip()
    if not name or not hint:
        return {'error': 'name and hint are required.'}
    try:
        improved = polish_description(name=name, category=category, hint=hint)
        return {'ok': True, 'improvedDescription': improved}
    except Exception as ex:
        return {'error': f'Polish failed: {ex}'}


TOOL_DISPATCH = {
    'search_products':            tool_search_products,
    'get_product_details':        tool_get_product_details,
    'get_seller_reviews':         tool_get_seller_reviews,
    'add_to_cart':                tool_add_to_cart,
    'update_cart_qty':            tool_update_cart_qty,
    'remove_from_cart':           tool_remove_from_cart,
    'clear_cart':                 tool_clear_cart,
    'checkout_now':               tool_checkout_now,
    'view_cart':                  tool_view_cart,
    'get_wallet_balance':         tool_get_wallet_balance,
    'list_my_products':           tool_list_my_products,
    'update_my_product':          tool_update_my_product,
    'create_my_product':          tool_create_my_product,
    'delete_my_product':          tool_delete_my_product,
    'get_seller_orders':          tool_get_seller_orders,
    'polish_product_description': tool_polish_product_description,
}


# ── DashScope HTTP call ──────────────────────────────────────────
def _call_dashscope(messages, max_attempts=3, use_tools=True):
    if not Config.DASHSCOPE_API_KEY:
        raise RuntimeError('DASHSCOPE_API_KEY is not set. Add it to backend/.env')
    payload = {
        'model':    Config.DASHSCOPE_MODEL,
        'messages': messages,
        'temperature': 0.4,
    }
    if use_tools:
        payload['tools'] = TOOLS
        payload['tool_choice'] = 'auto'
    body = json.dumps(payload).encode('utf-8')
    headers = {
        'Content-Type':  'application/json',
        'Authorization': f'Bearer {Config.DASHSCOPE_API_KEY}',
    }

    last_err = None
    for attempt in range(1, max_attempts + 1):
        req = urllib.request.Request(Config.DASHSCOPE_URL, data=body, headers=headers, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8', errors='ignore')
            # 4xx is permanent (bad key, bad request) — don't retry
            if 400 <= e.code < 500:
                raise RuntimeError(f'DashScope HTTP {e.code}: {err_body}')
            last_err = RuntimeError(f'DashScope HTTP {e.code}: {err_body}')
        except (urllib.error.URLError, ssl.SSLError, TimeoutError, ConnectionError) as e:
            # Transient network / SSL errors — retry
            last_err = RuntimeError(f'DashScope network error (attempt {attempt}/{max_attempts}): {e}')
        if attempt < max_attempts:
            time.sleep(0.6 * attempt)  # 0.6s, 1.2s
    raise last_err if last_err else RuntimeError('DashScope call failed')


# ── Description polish (plain-text, no tool-use) ─────────────────
def polish_description(name, category, hint):
    """One-shot call: turn a rough hint into a polished product description."""
    sys_msg = (
        "You are an expert e-commerce copywriter for ShopHub. Given a product "
        "name, category, and rough notes from a seller, write a clear, concise "
        "marketing-friendly description in ENGLISH. "
        "Rules: 2–4 sentences, 60–110 words, no marketing hype like 'amazing'/"
        "'best ever', no emojis, no headings, no bullet points. Focus on "
        "materials, features and benefits. Output ONLY the description text — "
        "no prefix like 'Here's...'."
    )
    user_msg = f"Product name: {name}\nCategory: {category or '(unspecified)'}\nSeller notes: {hint}"
    resp = _call_dashscope(
        [{'role': 'system', 'content': sys_msg},
         {'role': 'user',   'content': user_msg}],
        use_tools=False,
    )
    text = (resp['choices'][0]['message'].get('content') or '').strip()
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1]
    return text


# ── Endpoint: AI description polish (called by seller form) ──────
@bp.post('/generate-description')
def generate_description_endpoint():
    user = _current_user()
    if not user or user.role != 'seller':
        return jsonify(error='Sellers only.'), 403
    data = request.get_json(force=True) or {}
    name = (data.get('name') or '').strip()
    category = (data.get('category') or '').strip()
    hint = (data.get('hint') or data.get('description') or '').strip()
    if not name:
        return jsonify(error='name is required.'), 400
    if not hint:
        return jsonify(error='Write a rough description first — the AI will improve it.'), 400
    try:
        improved = polish_description(name=name, category=category, hint=hint)
        return jsonify(description=improved)
    except Exception as ex:
        return jsonify(error=str(ex)), 500


# ── Endpoint ─────────────────────────────────────────────────────
@bp.post('/chat')
def chat():
    user = _current_user()
    data = request.get_json(force=True) or {}
    history = data.get('messages') or []

    base_prompt = SYSTEM_PROMPT
    role_note = ""
    if user and user.role == 'seller':
        base_prompt = SYSTEM_PROMPT + "\n\n" + SELLER_PROMPT
        role_note = (
            f"\n\nThe current user is signed in as SELLER '{user.username}' "
            f"(id={user.id}, shop='{user.shop_name or user.username}'). "
            f"You may use the seller-management tools for THIS user only."
        )
    elif user:
        role_note = (
            f"\n\nThe current user is signed in as buyer '{user.username}' "
            f"(id={user.id}). You may use cart and checkout tools. "
            f"Seller-management tools will fail for this user."
        )
    else:
        role_note = (
            "\n\nThe user is NOT signed in. You can search and recommend, "
            "but adding to cart, checking out or managing products will fail "
            "until they sign in."
        )

    messages = [{'role': 'system', 'content': base_prompt + role_note}]
    messages.extend(history)

    try:
        for _ in range(6):  # at most 6 tool-call rounds per turn
            resp = _call_dashscope(messages)
            choice = resp['choices'][0]
            msg = choice['message']
            messages.append(msg)

            tool_calls = msg.get('tool_calls') or []
            if not tool_calls:
                return jsonify(reply=msg.get('content') or '', messages=messages[1:])

            for call in tool_calls:
                name = call['function']['name']
                try:
                    args = json.loads(call['function'].get('arguments') or '{}')
                except json.JSONDecodeError:
                    args = {}
                fn = TOOL_DISPATCH.get(name)
                result = fn(args, user) if fn else {'error': f'Unknown tool {name}'}
                messages.append({
                    'role':         'tool',
                    'tool_call_id': call['id'],
                    'name':         name,
                    'content':      json.dumps(result, ensure_ascii=False),
                })
        return jsonify(reply='(too many tool calls, aborting)', messages=messages[1:])
    except Exception as ex:
        return jsonify(error=str(ex)), 500
