from app import create_app, db
import os

app = create_app()

# Create database tables if they don't exist (runs on startup)
with app.app_context():
    db.create_all()
    print("✅ Database tables created successfully!")

if __name__ == '__main__':
    # This block runs only when executing `python run.py` directly.
    # For production (gunicorn), this block is ignored.
    debug_mode = os.environ.get('FLASK_DEBUG', '1') == '1'  # default to True
    app.run(
        debug=debug_mode,
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000))
    )