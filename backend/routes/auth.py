from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from models import User
import re
import os
import traceback
from flask import session

from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask import session, current_app

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("mobile")
        password = request.form.get("password")
        
        clean_mobile = re.sub(r'\D', '', identifier) if identifier else ""
        user = User.query.filter((User.email == identifier) | (User.mobile == clean_mobile)).first()
        
        if user and user.password and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("academic.dashboard"))
        
        flash("Invalid identification or security key", "warning")
    return render_template("auth.html", mode='auth')

@auth_bp.route("/", methods=["GET"])
def landing():
    return render_template("auth.html", mode='landing')

@auth_bp.route("/register", methods=["POST"])
def register():
    name = request.form.get("name")
    email = request.form.get("email")
    mobile = request.form.get("mobile")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")

    if not all([name, email, mobile, password, confirm_password]):
        flash("All fields are mandatory", "warning")
        return redirect(url_for("auth.login"))

    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        flash("Invalid email format", "warning")
        return redirect(url_for("auth.login"))

    clean_mobile = re.sub(r'\D', '', mobile)
    if len(clean_mobile) < 10:
        flash("Mobile must contain 10 digits", "warning")
        return redirect(url_for("auth.login"))
    
    if User.query.filter_by(mobile=clean_mobile).first():
        flash("Mobile number already registered", "warning")
        return redirect(url_for("auth.login"))
    
    if User.query.filter_by(email=email).first():
        flash("Email address already registered", "warning")
        return redirect(url_for("auth.login"))

    if password != confirm_password:
        flash("Passwords do not match!", "warning")
        return redirect(url_for("auth.login"))

    hashed_pass = generate_password_hash(password)
    new_user = User(name=name, email=email, mobile=clean_mobile, password=hashed_pass)
    
    if User.query.count() == 0:
        new_user.is_admin = True

    try:
        db.session.add(new_user)
        db.session.commit()
        flash("Registration Successful. Please Login.", "success")
    except Exception as e:
        db.session.rollback()
        flash("Database Error: Identity could not be saved.", "warning")
    
    return redirect(url_for("auth.login"))

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))

@auth_bp.route("/google")
def google_login():
    from extensions import oauth
    scheme = 'https' if os.getenv('RENDER') else 'http'
    redirect_uri = url_for('auth.google_callback', _external=True, _scheme=scheme)
    return oauth.google.authorize_redirect(redirect_uri)

@auth_bp.route("/google/callback")
def google_callback():
    from extensions import oauth
    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get('userinfo')
        if not user_info:
            user_info = oauth.google.get('https://www.googleapis.com/oauth2/v3/userinfo').json()
            
        if not user_info:
            flash("Google authentication failed.", "warning")
            return redirect(url_for("auth.login"))
        
        email = user_info.get('email')
        name = user_info.get('name')
        
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(name=name, email=email, mobile=None, password=None)
            db.session.add(user)
            db.session.commit()
        
        login_user(user)
        # Check if it was an API request or mobile client
        if request.args.get('mobile') == 'true':
            access_token = create_access_token(identity=user.id)
            return jsonify({"token": access_token, "user": user.to_dict()})
            
        return redirect(url_for("academic.dashboard"))
    except Exception as e:
        print(f"OAuth Error: {traceback.format_exc()}")
        flash("An error occurred during Google authentication.", "error")
        return redirect(url_for("auth.login"))
