from flask import Blueprint, request, jsonify, g
from extensions import db
from models import Wallet
from auth_utils import require_auth

bp = Blueprint('wallet', __name__)


@bp.get('')
@require_auth()
def get_wallet():
    wallet = Wallet.query.get(g.user_id)
    balance = wallet.balance if wallet else 0
    return jsonify(balance=balance)


@bp.post('/topup')
@require_auth('buyer')
def topup():
    amount = float(request.get_json(force=True).get('amount', 0))
    if amount <= 0:
        return jsonify(error='Amount must be positive'), 400

    wallet = Wallet.query.get(g.user_id)
    if not wallet:
        wallet = Wallet(user_id=g.user_id, balance=0)
        db.session.add(wallet)

    wallet.balance += amount
    db.session.commit()
    return jsonify(balance=wallet.balance)
