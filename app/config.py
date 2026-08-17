import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-12345'
    
    # Get DATABASE_URL from environment (Render sets this automatically for PostgreSQL)
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    # If DATABASE_URL starts with 'postgresql://', SQLAlchemy handles it natively.
    # If it starts with 'mysql://', we convert it to 'mysql+pymysql://'
    if DATABASE_URL and DATABASE_URL.startswith('mysql://'):
        DATABASE_URL = DATABASE_URL.replace('mysql://', 'mysql+pymysql://', 1)
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///default.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False