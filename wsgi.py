from app import create_app, db

app = create_app()

# This creates all tables (users, machinery, bookings, etc.)
# when the app starts on Render.
with app.app_context():
    db.create_all()
    print("✅ Database tables created/verified successfully!")

# Gunicorn will use this 'app' object