from flask import Blueprint, request, jsonify
from extensions import db
from models import Announcement
from auth_utils import require_auth

bp = Blueprint('announcements', __name__)


@bp.get('')
def list_announcements():
    items = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return jsonify(announcements=[a.to_dict() for a in items])


@bp.post('')
@require_auth('admin')
def create_announcement():
    data    = request.get_json(force=True)
    title   = (data.get('title')   or '').strip()
    content = (data.get('content') or '').strip()
    if not title:
        return jsonify(error='Title is required'), 400
    a = Announcement(title=title, content=content)
    db.session.add(a)
    db.session.commit()
    return jsonify(announcement=a.to_dict()), 201


@bp.delete('/<int:aid>')
@require_auth('admin')
def delete_announcement(aid):
    a = Announcement.query.get_or_404(aid)
    db.session.delete(a)
    db.session.commit()
    return jsonify(ok=True)
