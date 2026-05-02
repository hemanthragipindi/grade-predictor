import os
import datetime
import logging
from flask import Flask
from database import db
from models import User
from flask_login import LoginManager
from sqlalchemy import text, inspect
from flask_cors import CORS
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

# Setup logging to see errors on Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize App with explicit Frontend paths
app = Flask(__name__, 
            template_folder='../frontend/templates', 
            static_folder='../frontend/static')

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'nexora-fallback-key-123')
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(minutes=20)

# Use absolute path for DB and ensure instance folder exists
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')

try:
    if not os.path.exists(INSTANCE_DIR):
        os.makedirs(INSTANCE_DIR)
        logger.info(f"Created instance directory at {INSTANCE_DIR}")
except Exception as e:
    logger.error(f"Failed to create instance directory: {e}")

db_path = os.path.join(INSTANCE_DIR, 'grades.db')
# For Linux absolute paths, we need 4 slashes: sqlite:////path/to/db
if db_path.startswith('/'):
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
else:
    # Windows absolute path
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

CORS(app) 
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, '../frontend/static/uploads')

# Cloudinary Setup
cloudinary.config(
    cloud_name = os.getenv("CLOUDINARY_NAME"),
    api_key = os.getenv("CLOUDINARY_KEY"),
    api_secret = os.getenv("CLOUDINARY_SECRET")
)

# Ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Initialize Extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register Blueprints
from routes.auth import auth_bp
from routes.academic import academic_bp
from routes.api import api_bp
from routes.admin import admin_bp

app.register_blueprint(auth_bp)
app.register_blueprint(academic_bp)
app.register_blueprint(api_bp)
app.register_blueprint(admin_bp)

@app.context_processor
def inject_globals():
    return {'current_hour': datetime.datetime.now().hour}

# Auto-Migrations
with app.app_context():
    try:
        db.create_all()
        inspector = inspect(db.engine)
        
        # ca_marks.weight migration
        if 'ca_marks' in inspector.get_table_names():
            cols = [c['name'] for c in inspector.get_columns('ca_marks')]
            if 'weight' not in cols:
                db.session.execute(text("ALTER TABLE ca_marks ADD COLUMN weight FLOAT DEFAULT 0.0;"))
                db.session.commit()

        # users.created_at migration
        if 'users' in inspector.get_table_names():
            cols = [c['name'] for c in inspector.get_columns('users')]
            if 'created_at' not in cols:
                db.session.execute(text("ALTER TABLE users ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;"))
                db.session.commit()

        # cloud_files.public_id migration
        if 'cloud_files' in inspector.get_table_names():
            cols = [c['name'] for c in inspector.get_columns('cloud_files')]
            if 'public_id' not in cols:
                db.session.execute(text("ALTER TABLE cloud_files ADD COLUMN public_id VARCHAR(255);"))
                db.session.commit()
    except Exception as e:
        logger.error(f"Database Initialization/Migration Error: {e}")
        db.session.rollback()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
