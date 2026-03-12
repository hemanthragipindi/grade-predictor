import os

class Config:
    # Use DATABASE_URL environment variable if it exists (for online hosting platforms),
    # otherwise fallback to the local PostgreSQL database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', "postgresql://postgres:Hemanth713@localhost/grade_tracker")
    
    # Fix for SQLAlchemy 1.4+ dialiect issues with render's database URLs
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False