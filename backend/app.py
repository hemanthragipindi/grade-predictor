import sys
import os

# Essential Environment Tweaks
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
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
    app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=3650) # Practically forever

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

app = create_app()

if __name__ == "__main__":
    # Ensure instance folder exists
    instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
    
    print("Nexora Backend starting up...")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
