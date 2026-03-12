from app import app
from database import db
from models import User, Subject, Component, Marks, CAMarks
from werkzeug.security import generate_password_hash
from sqlalchemy import text

def migrate():
    with app.app_context():
        # Check if users table exists
        result = db.session.execute(text("SELECT to_regclass('public.users');")).scalar()
        if not result:
            print("Creating users table...")
            User.__table__.create(db.engine)
            
            # Create default admin user
            admin = User(username='admin', password_hash=generate_password_hash('password'))
            db.session.add(admin)
            db.session.commit()
            print("Created default user 'admin' with password 'password'")
            
            # Add user_id column to existing tables and assign to admin
            tables = ['subjects', 'components', 'marks', 'ca_marks']
            for table in tables:
                print(f"Adding user_id to {table}...")
                db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS user_id INTEGER;"))
                db.session.execute(text(f"UPDATE {table} SET user_id = :admin_id WHERE user_id IS NULL;"), {"admin_id": admin.id})
                db.session.execute(text(f"ALTER TABLE {table} ALTER COLUMN user_id SET NOT NULL;"))
                
                # Add foreign key constraint if not exists
                try:
                    db.session.execute(text(f"""
                        ALTER TABLE {table} 
                        ADD CONSTRAINT fk_{table}_user_id 
                        FOREIGN KEY (user_id) REFERENCES users(id);
                    """))
                except Exception as e:
                    print(f"Foreign key constraint already exists or error: {e}")
                    db.session.rollback()
                finally:
                    db.session.commit()
            
            print("Migration successful! Existing data assigned to 'admin'.")
        else:
            print("Users table already exists. No migration needed.")

if __name__ == "__main__":
    migrate()
