import os
import datetime
from flask import Flask
from database import db
from models import User
from flask_login import LoginManager
from sqlalchemy import text, inspect
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

# Initialize App with explicit Frontend paths
app = Flask(__name__, 
            template_folder='../frontend/templates', 
            static_folder='../frontend/static')

app.config['SECRET_KEY'] = 'nexora-secret-key-123'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(minutes=20)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../backend/instance/grades.db'
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
    db.create_all()
    inspector = inspect(db.engine)
    
    # ca_marks.weight migration
    if 'ca_marks' in inspector.get_table_names():
        cols = [c['name'] for c in inspector.get_columns('ca_marks')]
        if 'weight' not in cols:
            try:
                db.session.execute(text("ALTER TABLE ca_marks ADD COLUMN weight FLOAT DEFAULT 0.0;"))
                db.session.commit()
            except: db.session.rollback()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
