from flask import Blueprint, jsonify, session
from app.models import User, Machinery, Booking, ResidueListing, ResidueOrder

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/stats', methods=['GET'])
def stats():
    if 'user_id' not in session:
        return jsonify({'error': 'Login required'}), 401
    user = User.query.get(session['user_id'])
    if user.role != 'admin':
        return jsonify({'error': 'Admin only'}), 403
    return jsonify({
        'users': User.query.count(),
        'machinery': Machinery.query.count(),
        'bookings': Booking.query.count(),
        'residue_listings': ResidueListing.query.count(),
        'residue_orders': ResidueOrder.query.count()
    }), 200