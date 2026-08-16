from flask import Blueprint, request, jsonify, session, redirect
from app import db
from app.models import User, MachineryOwner
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not all(k in data for k in ['email','password','full_name','role']):
        return jsonify({'error': 'Missing fields'}), 400

    if User.query.filter_by(email=data['email'].lower()).first():
        return jsonify({'error': 'Email already exists'}), 400

    user = User(
        email=data['email'].lower(),
        password_hash=generate_password_hash(data['password']),
        full_name=data['full_name'],
        phone=data.get('phone', ''),
        address=data.get('address', ''),
        role=data['role'],
        location_lat=data.get('location_lat'),
        location_lng=data.get('location_lng')
    )
    
    if data['role'] == 'owner':
        user.is_machinery_owner = True

    db.session.add(user)
    db.session.commit()

    if data['role'] == 'owner':
        owner = MachineryOwner(user_id=user.id)
        db.session.add(owner)
        db.session.commit()

    return jsonify({'message': 'Registered successfully', 'user_id': user.id}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email', '').lower()).first()
    if not user or not check_password_hash(user.password_hash, data.get('password', '')):
        return jsonify({'error': 'Invalid credentials'}), 401

    session['user_id'] = user.id
    session['user_role'] = user.role
    session['is_machinery_owner'] = user.is_machinery_owner

    return jsonify({
        'success': True,
        'user': {
            'id': user.id,
            'email': user.email,
            'full_name': user.full_name,
            'role': user.role,
            'is_machinery_owner': user.is_machinery_owner,
            'location_lat': float(user.location_lat) if user.location_lat else None,
            'location_lng': float(user.location_lng) if user.location_lng else None
        }
    }), 200

@auth_bp.route('/me', methods=['GET'])
def get_me():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({
        'id': user.id,
        'email': user.email,
        'full_name': user.full_name,
        'role': user.role,
        'is_machinery_owner': user.is_machinery_owner,
        'phone': user.phone,
        'address': user.address,
        'location_lat': float(user.location_lat) if user.location_lat else None,
        'location_lng': float(user.location_lng) if user.location_lng else None
    }), 200

@auth_bp.route('/update-profile', methods=['PUT'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    if 'full_name' in data:
        user.full_name = data['full_name']
    if 'phone' in data:
        user.phone = data['phone']
    if 'address' in data:
        user.address = data['address']
    if 'location_lat' in data and data['location_lat'] is not None:
        try:
            user.location_lat = float(data['location_lat'])
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid latitude format'}), 400
    if 'location_lng' in data and data['location_lng'] is not None:
        try:
            user.location_lng = float(data['location_lng'])
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid longitude format'}), 400

    db.session.commit()
    return jsonify({'message': 'Profile updated successfully'}), 200

@auth_bp.route('/become-owner', methods=['POST'])
def become_owner():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    user = User.query.get(session['user_id'])
    if not user or user.role not in ['farmer', 'owner']:
        return jsonify({'error': 'Only farmers or owners can use this'}), 403
    if user.is_machinery_owner:
        return jsonify({'error': 'Already an owner'}), 400

    owner = MachineryOwner(user_id=user.id)
    db.session.add(owner)
    user.is_machinery_owner = True
    session['is_machinery_owner'] = True
    db.session.commit()
    return jsonify({'message': 'Now you are a machinery owner!'}), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out'}), 200

@auth_bp.route('/set-language/<lang>')
def set_language(lang):
    if lang in ['en', 'hi']:
        session['lang'] = lang
    return redirect(request.referrer or '/')