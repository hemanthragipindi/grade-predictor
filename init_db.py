from app import app
from database import db
from models import User, Subject, Component, Marks, CAMarks

with app.app_context():
    print("Dropping all existing tables...")
    db.drop_all()
    print("Creating all tables with new schema (including Users)...")
    db.create_all()
    print("Database initialization complete.")
