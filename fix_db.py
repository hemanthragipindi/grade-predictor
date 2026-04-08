from app import app
from database import db

with app.app_context():
    # Use raw SQL to drop the table if it exists
    # This will allow db.create_all() to recreate it with the correct schema
    db.session.execute(db.text("DROP TABLE IF EXISTS syllabus"))
    db.session.commit()
    # Now create the tables again (only missing ones will be created)
    db.create_all()
    print("Database schema for 'syllabus' table has been successfully reset.")
