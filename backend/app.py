import sys
import os
# Add the current directory to sys.path to resolve internal imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import datetime
import logging
import traceback
from flask import Flask, jsonify
from database import db
from models import User
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
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

from config import config_by_name

# Initialize extensions outside for global access if needed
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address)

def create_app(config_name='dev'):
    if os.getenv('RENDER'):
        config_name = 'prod'
        
    app = Flask(__name__, 
                template_folder='../frontend/templates', 
                static_folder='../frontend/static')

    app.config.from_object(config_by_name[config_name])
    
    app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False
    app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(minutes=60)

    # Initialize Extensions
    db.init_app(app)
    CORS(app)
    oauth.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)
    
    oauth.register(
        name='google',
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Cloudinary
    cloudinary.config(
        cloud_name = app.config['CLOUDINARY_NAME'],
        api_key = app.config['CLOUDINARY_KEY'],
        api_secret = app.config['CLOUDINARY_SECRET']
    )

    # Blueprints
    from routes.auth import auth_bp
    from routes.academic import academic_bp
    from routes.api import api_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(academic_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    @app.context_processor
    def inject_globals():
        return {'current_hour': datetime.datetime.now().hour}

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({
            "success": False,
            "error": "Internal Server Error",
            "message": str(e) if not os.getenv('RENDER') else "Contact Support"
        }), 500

    @app.route('/health')
    def health_check():
        return jsonify({"status": "OK", "timestamp": datetime.datetime.now().isoformat()}), 200

    return app

try:
    app = create_app()

    # Database Synchronization and Migrations with Retry Logic
    with app.app_context():
        import time
        max_retries = 5
        for i in range(max_retries):
            try:
                db.create_all()
                inspector = inspect(db.engine)
                
                # Migration Helpers
                def add_column(table, column, type_str):
                    try:
                        cols = [c['name'] for c in inspector.get_columns(table)]
                        if column not in cols:
                            # Fix for Postgres compatibility
                            if os.getenv('RENDER') and 'DATETIME' in type_str.upper():
                                type_str = type_str.upper().replace('DATETIME', 'TIMESTAMP')
                            
                            db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {type_str};"))
                            db.session.commit()
                            print(f"Migration: Added {column} to {table}")
                    except Exception as e:
                        print(f"Column {column} migration skipped: {e}")
                        db.session.rollback()

                if 'ca_marks' in inspector.get_table_names():
                    add_column('ca_marks', 'weight', 'FLOAT DEFAULT 0.0')
                if 'users' in inspector.get_table_names():
                    add_column('users', 'created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
                if 'cloud_files' in inspector.get_table_names():
                    add_column('cloud_files', 'public_id', 'VARCHAR(255)')
                
                print("Database initialized successfully!")
                break
            except Exception as db_e:
                print(f"Database Init Attempt {i+1} failed: {db_e}")
                if i < max_retries - 1:
                    time.sleep(5) # Wait 5 seconds before retrying
                else:
                    print("Warning: Database initialization failed after multiple retries.")
except Exception as e:
    print("CRITICAL: Application failed to start!")
    traceback.print_exc()
    # Still raise the error so Render knows it failed
    raise e

if __name__ == "__main__":
    app.run(debug=True, port=8000)
