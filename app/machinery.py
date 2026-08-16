from flask import Blueprint, request, jsonify, session
from app import db
from app.models import Machinery, MachineryOwner, User, Booking
from datetime import datetime
from decimal import Decimal
from math import radians, sin, cos, sqrt, atan2

machinery_bp = Blueprint('machinery', __name__)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def get_current_owner():
    if 'user_id' not in session:
        return None, None
    user = User.query.get(session['user_id'])
    if not user or not user.is_machinery_owner:
        return user, None
    owner = MachineryOwner.query.filter_by(user_id=user.id).first()
    return user, owner

# ---------- ADD MACHINERY ----------
@machinery_bp.route('/', methods=['POST'])
def add_machinery():
    user, owner = get_current_owner()
    if not user or not owner:
        return jsonify({'error': 'You must be a machinery owner'}), 403

    data = request.get_json()
    if not all(k in data for k in ['name','category','rental_price_per_day','location_lat','location_lng']):
        return jsonify({'error': 'Missing fields'}), 400

    machine = Machinery(
        owner_id=owner.id,
        name=data['name'],
        category=data['category'],
        description=data.get('description', ''),
        rental_price_per_day=Decimal(str(data['rental_price_per_day'])),
        availability=data.get('availability', True),
        location_lat=data['location_lat'],
        location_lng=data['location_lng'],
        address=data.get('address', ''),
        image_urls=data.get('image_urls', [])
    )
    db.session.add(machine)
    db.session.commit()
    return jsonify({'message': 'Machine added', 'id': machine.id}), 201

# ---------- LIST ALL AVAILABLE MACHINERY (FOR FARMERS) ----------
@machinery_bp.route('/', methods=['GET'])
def list_machinery():
    category = request.args.get('category')
    lat = request.args.get('lat')
    lng = request.args.get('lng')
    radius = request.args.get('radius', 50)  # default 50 km
    sort = request.args.get('sort', 'distance')

    query = Machinery.query
    if category:
        query = query.filter_by(category=category)

    machines = query.all()

    if lat and lng:
        lat_f = float(lat)
        lng_f = float(lng)
        filtered = []
        for m in machines:
            dist = haversine(lat_f, lng_f, float(m.location_lat), float(m.location_lng))
            if dist <= float(radius):
                m.distance = dist
                filtered.append(m)
        machines = filtered
    else:
        for m in machines:
            m.distance = None

    if sort == 'distance' and lat and lng:
        machines.sort(key=lambda m: m.distance if m.distance is not None else float('inf'))

    return jsonify([{
        'id': m.id,
        'name': m.name,
        'category': m.category,
        'rental_price_per_day': float(m.rental_price_per_day),
        'availability': m.availability,
        'location_lat': float(m.location_lat),
        'location_lng': float(m.location_lng),
        'address': m.address,
        'description': m.description,
        'owner_id': m.owner_id,
        'distance': m.distance if hasattr(m, 'distance') else None
    } for m in machines]), 200

# ---------- GET MACHINERY DETAILS ----------
@machinery_bp.route('/<int:id>', methods=['GET'])
def get_machine(id):
    m = Machinery.query.get(id)
    if not m:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({
        'id': m.id,
        'name': m.name,
        'category': m.category,
        'description': m.description,
        'rental_price_per_day': float(m.rental_price_per_day),
        'availability': m.availability,
        'location_lat': float(m.location_lat),
        'location_lng': float(m.location_lng),
        'address': m.address,
        'image_urls': m.image_urls,
        'owner_id': m.owner_id,
        'created_at': m.created_at.isoformat()
    }), 200

# ---------- BOOK MACHINERY ----------
@machinery_bp.route('/<int:id>/book', methods=['POST'])
def book_machine(id):
    if 'user_id' not in session:
        return jsonify({'error': 'Please login'}), 401
    user = User.query.get(session['user_id'])
    if user.role != 'farmer':
        return jsonify({'error': 'Only farmers can book'}), 403

    machine = Machinery.query.get(id)
    if not machine or not machine.availability:
        return jsonify({'error': 'Not available'}), 400

    data = request.get_json()
    try:
        start = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
    except:
        return jsonify({'error': 'Invalid date format'}), 400
    if start > end:
        return jsonify({'error': 'Start date must be before end date'}), 400

    existing = Booking.query.filter(
        Booking.machinery_id == id,
        Booking.status.in_(['pending','accepted']),
        Booking.start_date <= end,
        Booking.end_date >= start
    ).first()
    if existing:
        return jsonify({'error': 'Already booked for these dates'}), 400

    days = (end - start).days + 1
    total = days * machine.rental_price_per_day
    booking = Booking(
        machinery_id=id,
        farmer_id=user.id,
        start_date=start,
        end_date=end,
        total_price=total,
        status='pending'
    )
    db.session.add(booking)
    db.session.commit()
    return jsonify({'message': 'Booking created', 'id': booking.id, 'total': float(total)}), 201

# ---------- GET BOOKINGS (FARMER OR OWNER) ----------
@machinery_bp.route('/bookings', methods=['GET'])
def get_bookings():
    if 'user_id' not in session:
        return jsonify({'error': 'Login required'}), 401
    user = User.query.get(session['user_id'])
    
    if user.role == 'farmer':
        bookings = Booking.query.filter_by(farmer_id=user.id).all()
    elif user.is_machinery_owner:
        owner = MachineryOwner.query.filter_by(user_id=user.id).first()
        if owner:
            bookings = Booking.query.join(Machinery).filter(Machinery.owner_id == owner.id).all()
        else:
            bookings = []
    else:
        return jsonify({'error': 'Unauthorized'}), 403

    return jsonify([{
        'id': b.id,
        'machinery_id': b.machinery_id,
        'machinery_name': b.machinery.name,
        'farmer_id': b.farmer_id,
        'farmer_name': b.farmer.full_name,
        'start_date': b.start_date.isoformat(),
        'end_date': b.end_date.isoformat(),
        'total_price': float(b.total_price),
        'status': b.status,
        'booking_date': b.booking_date.isoformat()
    } for b in bookings]), 200

# ---------- RESPOND TO BOOKING (ACCEPT/REJECT) ----------
@machinery_bp.route('/bookings/<int:id>/respond', methods=['PUT'])
def respond_booking(id):
    if 'user_id' not in session:
        return jsonify({'error': 'Login required'}), 401
    booking = Booking.query.get(id)
    if not booking:
        return jsonify({'error': 'Not found'}), 404
    
    machine = Machinery.query.get(booking.machinery_id)
    owner = MachineryOwner.query.get(machine.owner_id)
    if owner.user_id != session['user_id']:
        return jsonify({'error': 'Not authorized'}), 403

    action = request.get_json().get('action')
    if action not in ['accept','reject']:
        return jsonify({'error': 'Invalid action'}), 400
    if booking.status != 'pending':
        return jsonify({'error': 'Already processed'}), 400

    booking.status = 'accepted' if action == 'accept' else 'rejected'
    db.session.commit()
    return jsonify({'message': f'Booking {action}ed'}), 200

# ---------- GET MACHINERY OWNED BY CURRENT USER (OWNER DASHBOARD) ----------
@machinery_bp.route('/mine', methods=['GET'])
def get_my_machinery():
    """Return all machinery owned by the logged-in user."""
    if 'user_id' not in session:
        return jsonify({'error': 'Login required'}), 401
    
    user = User.query.get(session['user_id'])
    if not user or not user.is_machinery_owner:
        return jsonify({'error': 'Not a machinery owner'}), 403
    
    owner = MachineryOwner.query.filter_by(user_id=user.id).first()
    if not owner:
        return jsonify({'error': 'Owner profile not found'}), 404
    
    machines = Machinery.query.filter_by(owner_id=owner.id).all()
    
    return jsonify([{
        'id': m.id,
        'name': m.name,
        'category': m.category,
        'description': m.description,
        'rental_price_per_day': float(m.rental_price_per_day),
        'availability': m.availability,
        'location_lat': float(m.location_lat),
        'location_lng': float(m.location_lng),
        'address': m.address,
        'image_urls': m.image_urls,
        'created_at': m.created_at.isoformat()
    } for m in machines]), 200