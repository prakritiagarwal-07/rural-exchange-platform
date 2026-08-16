from app import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    location_lat = db.Column(db.DECIMAL(10,8))
    location_lng = db.Column(db.DECIMAL(11,8))
    address = db.Column(db.Text)
    role = db.Column(db.Enum('farmer', 'owner', 'buyer', 'admin'), default='farmer')
    is_machinery_owner = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MachineryOwner(db.Model):
    __tablename__ = 'machinery_owners'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    rating_avg = db.Column(db.DECIMAL(3,2), default=0)
    total_ratings = db.Column(db.Integer, default=0)
    verified = db.Column(db.Boolean, default=False)
    user = db.relationship('User', backref='owner_profile')

class Machinery(db.Model):
    __tablename__ = 'machinery'
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('machinery_owners.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    rental_price_per_day = db.Column(db.DECIMAL(10,2), nullable=False)
    availability = db.Column(db.Boolean, default=True)
    location_lat = db.Column(db.DECIMAL(10,8), nullable=False)
    location_lng = db.Column(db.DECIMAL(11,8), nullable=False)
    address = db.Column(db.Text)
    image_urls = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    owner = db.relationship('MachineryOwner', backref='machinery_list')

class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    machinery_id = db.Column(db.Integer, db.ForeignKey('machinery.id'), nullable=False)
    farmer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    total_price = db.Column(db.DECIMAL(10,2), nullable=False)
    status = db.Column(db.Enum('pending','accepted','rejected','completed','cancelled'), default='pending')
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    machinery = db.relationship('Machinery', backref='bookings')
    farmer = db.relationship('User', backref='my_bookings')

class ResidueListing(db.Model):
    __tablename__ = 'residue_listings'
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    residue_type = db.Column(db.String(50), nullable=False)
    quantity_kg = db.Column(db.DECIMAL(10,2), nullable=False)
    price_per_kg = db.Column(db.DECIMAL(10,2), nullable=False)
    location_lat = db.Column(db.DECIMAL(10,8))
    location_lng = db.Column(db.DECIMAL(11,8))
    address = db.Column(db.Text)
    description = db.Column(db.Text)
    available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    farmer = db.relationship('User', backref='residue_listings')

class ResidueOrder(db.Model):
    __tablename__ = 'residue_orders'
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('residue_listings.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quantity_kg = db.Column(db.DECIMAL(10,2), nullable=False)
    total_price = db.Column(db.DECIMAL(10,2), nullable=False)
    status = db.Column(db.Enum('pending','accepted','rejected','completed'), default='pending')
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    listing = db.relationship('ResidueListing', backref='orders')
    buyer = db.relationship('User', backref='residue_orders')