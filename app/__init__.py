from flask import Flask, render_template, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from app.translations import TRANSLATIONS

db = SQLAlchemy()

def create_app():
    app = Flask(__name__, template_folder='templates')
    app.config.from_object('app.config.Config')
    
    db.init_app(app)
    CORS(app, supports_credentials=True)
    
    @app.context_processor
    def inject_globals():
        lang = session.get('lang', 'en')
        t_dict = TRANSLATIONS.get(lang, TRANSLATIONS['en'])
        
        def translate(key):
            return t_dict.get(key, key)
        
        user = None
        if 'user_id' in session:
            from app.models import User
            user = User.query.get(session['user_id'])
        
        return {
            't': translate,
            't_dict': t_dict,            # <-- raw dictionary
            'lang': lang,
            'current_user': user,
            'is_logged_in': user is not None
        }
    
    from app.auth import auth_bp
    from app.machinery import machinery_bp
    from app.residue import residue_bp
    from app.admin import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(machinery_bp, url_prefix='/api/machinery')
    app.register_blueprint(residue_bp, url_prefix='/api/residue')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    @app.route('/')
    def home():
        return render_template('welcome.html')
    
    @app.route('/login')
    def login_page():
        return render_template('login.html')
    
    @app.route('/register')
    def register_page():
        return render_template('register.html')
    
    @app.route('/profile')
    def profile_page():
        return render_template('profile.html')
    
    @app.route('/farmer-dashboard')
    def farmer_dashboard():
        return render_template('farmer_dashboard.html')
    
    @app.route('/owner-dashboard')
    def owner_dashboard():
        return render_template('owner_dashboard.html')
    
    @app.route('/buyer-dashboard')
    def buyer_dashboard():
        return render_template('buyer_dashboard.html')
    
    @app.route('/admin-dashboard')
    def admin_dashboard():
        return render_template('admin_dashboard.html')
    
    return app