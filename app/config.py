import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-12345'
    
    # Read the database URL from the environment (Render will set this)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:root@localhost/rural_exchange'
    
    # If your DATABASE_URL starts with 'mysql://', replace it with 'mysql+pymysql://'
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('mysql://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('mysql://', 'mysql+pymysql://', 1)
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False