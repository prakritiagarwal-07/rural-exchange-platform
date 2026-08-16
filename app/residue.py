from flask import Blueprint, request, jsonify, session
from app import db
from app.models import ResidueListing, ResidueOrder, User
from decimal import Decimal
from math import radians, sin, cos, sqrt, atan2

residue_bp = Blueprint('residue', __name__)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

# ---------- Add Listing ----------
@residue_bp.route('/', methods=['POST'])
def add_listing():
    if 'user_id' not in session:
        return jsonify({'error': 'Login required'}), 401
    user = User.query.get(session['user_id'])
    if user.role != 'farmer':
        return jsonify({'error': 'Only farmers can list'}), 403

    data = request.get_json()
    if not all(k in data for k in ['residue_type','quantity_kg','price_per_kg']):
        return jsonify({'error': 'Missing fields'}), 400

    listing = ResidueListing(
        farmer_id=user.id,
        residue_type=data['residue_type'],
        quantity_kg=Decimal(str(data['quantity_kg'])),
        price_per_kg=Decimal(str(data['price_per_kg'])),
        location_lat=data.get('location_lat'),
        location_lng=data.get('location_lng'),
        address=data.get('address', ''),
        description=data.get('description', '')
    )
    db.session.add(listing)
    db.session.commit()
    return jsonify({'message': 'Listing added', 'id': listing.id}), 201

# ---------- List Available Residue (for buyers) ----------
@residue_bp.route('/', methods=['GET'])
def list_residue():
    type_filter = request.args.get('type')
    lat = request.args.get('lat')
    lng = request.args.get('lng')
    radius = request.args.get('radius', 50)
    sort = request.args.get('sort', 'distance')

    query = ResidueListing.query.filter_by(available=True)
    if type_filter:
        query = query.filter_by(residue_type=type_filter)

    listings = query.all()

    if lat and lng:
        lat_f = float(lat); lng_f = float(lng)
        filtered = []
        for l in listings:
            if l.location_lat is not None and l.location_lng is not None:
                dist = haversine(lat_f, lng_f, float(l.location_lat), float(l.location_lng))
                if dist <= float(radius):
                    l.distance = dist
                    filtered.append(l)
        listings = filtered
    else:
        for l in listings:
            l.distance = None

    if sort == 'distance' and lat and lng:
        listings.sort(key=lambda l: l.distance if hasattr(l, 'distance') else float('inf'))

    return jsonify([{
        'id': l.id, 'residue_type': l.residue_type,
        'quantity_kg': float(l.quantity_kg), 'price_per_kg': float(l.price_per_kg),
        'farmer_id': l.farmer_id, 'farmer_name': l.farmer.full_name,
        'address': l.address, 'description': l.description,
        'location_lat': float(l.location_lat) if l.location_lat else None,
        'location_lng': float(l.location_lng) if l.location_lng else None,
        'distance': l.distance if hasattr(l, 'distance') else None
    } for l in listings]), 200

# ---------- My Listings (farmer's own) ----------
@residue_bp.route('/mine', methods=['GET'])
def get_my_listings():
    if 'user_id' not in session:
        return jsonify({'error': 'Login required'}), 401
    user = User.query.get(session['user_id'])
    if user.role != 'farmer':
        return jsonify({'error': 'Only farmers can access this'}), 403

    listings = ResidueListing.query.filter_by(farmer_id=user.id).all()
    return jsonify([{
        'id': l.id,
        'residue_type': l.residue_type,
        'quantity_kg': float(l.quantity_kg),
        'price_per_kg': float(l.price_per_kg),
        'available': l.available,
        'address': l.address,
        'description': l.description,
        'created_at': l.created_at.isoformat()
    } for l in listings]), 200

# ---------- Place Order ----------
@residue_bp.route('/<int:id>/order', methods=['POST'])
def place_order(id):
    if 'user_id' not in session:
        return jsonify({'error': 'Login required'}), 401
    user = User.query.get(session['user_id'])
    if user.role != 'buyer':
        return jsonify({'error': 'Only buyers can order'}), 403

    listing = ResidueListing.query.get(id)
    if not listing or not listing.available:
        return jsonify({'error': 'Not available'}), 404

    data = request.get_json()
    qty = Decimal(str(data.get('quantity_kg', 0)))
    if qty <= 0 or qty > listing.quantity_kg:
        return jsonify({'error': 'Invalid quantity'}), 400

    total = qty * listing.price_per_kg
    order = ResidueOrder(
        listing_id=id, buyer_id=user.id,
        quantity_kg=qty, total_price=total
    )
    db.session.add(order)
    db.session.commit()
    return jsonify({'message': 'Order placed', 'id': order.id, 'total': float(total)}), 201

# ---------- Get Orders ----------
@residue_bp.route('/orders', methods=['GET'])
def get_orders():
    if 'user_id' not in session:
        return jsonify({'error': 'Login required'}), 401
    user = User.query.get(session['user_id'])
    
    if user.role == 'buyer':
        orders = ResidueOrder.query.filter_by(buyer_id=user.id).all()
    elif user.role == 'farmer':
        orders = ResidueOrder.query.join(ResidueListing).filter(ResidueListing.farmer_id == user.id).all()
    else:
        return jsonify({'error': 'Unauthorized'}), 403
    return jsonify([{
        'id': o.id, 'residue_type': o.listing.residue_type,
        'quantity_kg': float(o.quantity_kg), 'total_price': float(o.total_price),
        'status': o.status, 'order_date': o.order_date.isoformat()
    } for o in orders]), 200

# ---------- Respond to Order ----------
@residue_bp.route('/orders/<int:id>/respond', methods=['PUT'])
def respond_order(id):
    if 'user_id' not in session:
        return jsonify({'error': 'Login required'}), 401
    order = ResidueOrder.query.get(id)
    if not order:
        return jsonify({'error': 'Not found'}), 404
    
    listing = ResidueListing.query.get(order.listing_id)
    if listing.farmer_id != session['user_id']:
        return jsonify({'error': 'Not authorized'}), 403

    action = request.get_json().get('action')
    if action not in ['accept','reject']:
        return jsonify({'error': 'Invalid action'}), 400
    if order.status != 'pending':
        return jsonify({'error': 'Already processed'}), 400

    if action == 'accept':
        order.status = 'accepted'
        listing.quantity_kg -= order.quantity_kg
        if listing.quantity_kg <= 0:
            listing.available = False
    else:
        order.status = 'rejected'
    db.session.commit()
    return jsonify({'message': f'Order {action}ed'}), 200

# ---------- Close Listing ----------
@residue_bp.route('/<int:id>/close', methods=['PUT'])
def close_listing(id):
    if 'user_id' not in session:
        return jsonify({'error': 'Login required'}), 401
    listing = ResidueListing.query.get(id)
    if not listing:
        return jsonify({'error': 'Not found'}), 404
    if listing.farmer_id != session['user_id']:
        return jsonify({'error': 'Unauthorized'}), 403
    listing.available = False
    db.session.commit()
    return jsonify({'message': 'Listing closed'}), 200