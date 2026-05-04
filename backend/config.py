import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'nexora-dev-key-777')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)
    
    # Cloudinary
    CLOUDINARY_NAME = os.getenv("CLOUDINARY_NAME")
    CLOUDINARY_KEY = os.getenv("CLOUDINARY_KEY")
    CLOUDINARY_SECRET = os.getenv("CLOUDINARY_SECRET")

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/grades.db'

class ProductionConfig(Config):
    DEBUG = False
    # Use environment variable, with a fallback to avoid startup crash
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    
    if SQLALCHEMY_DATABASE_URI:
        if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
            SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
    else:
        # Fallback to local sqlite to prevent RuntimeError
        SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/prod_fallback.db'

config_by_name = {
    'dev': DevelopmentConfig,
    'prod': ProductionConfig
}
