import os
import datetime
import logging
import traceback
from flask import Flask, jsonify
from database import db
from models import User
from flask_login import LoginManager
from sqlalchemy import text, inspect
from flask_cors import CORS
import cloudinary
import cloudinary.uploader
from authlib.integrations.flask_client import OAuth
from extensions import oauth
from dotenv import load_dotenv

load_dotenv()

# OAuth Security: allow insecure transport for local dev only
if not os.getenv('RENDER'):
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Professional logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__, 
                template_folder='../frontend/templates', 
                static_folder='../frontend/static')

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'nexora-fallback-key-123')
    app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(minutes=20)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Database Pathing
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
    if not os.path.exists(INSTANCE_DIR):
        os.makedirs(INSTANCE_DIR)
    
    db_path = os.path.join(INSTANCE_DIR, 'grades.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

    # Initialize Extensions
    db.init_app(app)
    CORS(app)
    oauth.init_app(app)
    
    oauth.register(
        name='google',
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except: return None

    # Cloudinary
    cloudinary.config(
        cloud_name = os.getenv("CLOUDINARY_NAME"),
        api_key = os.getenv("CLOUDINARY_KEY"),
        api_secret = os.getenv("CLOUDINARY_SECRET")
    )

    # Blueprints
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

    # Error Handler for Debugging on Render
    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({
            "error": "Internal Server Error",
            "traceback": traceback.format_exc()
        }), 500

    return app

app = create_app()

# Auto-Migrations logic
with app.app_context():
    try:
        db.create_all()
        inspector = inspect(db.engine)
        
        # Migration Helpers
        def add_column(table, column, type_str):
            cols = [c['name'] for c in inspector.get_columns(table)]
            if column not in cols:
                db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {type_str};"))
                db.session.commit()
                logger.info(f"Migration: Added {column} to {table}")

        if 'ca_marks' in inspector.get_table_names():
            add_column('ca_marks', 'weight', 'FLOAT DEFAULT 0.0')
        if 'users' in inspector.get_table_names():
            add_column('users', 'created_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP')
        if 'cloud_files' in inspector.get_table_names():
            add_column('cloud_files', 'public_id', 'VARCHAR(255)')
            
    except Exception as e:
        logger.error(f"Migration Failure: {e}")
        db.session.rollback()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
