class Config:
    SECRET_KEY = 'dev-secret-key-12345'  # Used for session signing
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:root@localhost/rural_exchange'
    SQLALCHEMY_TRACK_MODIFICATIONS = False