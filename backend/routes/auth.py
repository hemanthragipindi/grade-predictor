from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from models import User
import re

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        raw_mobile = request.form.get("mobile")
        mobile = re.sub(r'\D', '', raw_mobile) if raw_mobile else None
        password = request.form.get("password")
        
        user = User.query.filter_by(mobile=mobile).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("academic.dashboard"))
        
        flash("Invalid identification or security key", "warning")
    return render_template("auth.html")

@auth_bp.route("/api/check-mobile", methods=["POST"])
def check_mobile():
    data = request.json
    raw_mobile = data.get("mobile")
    mobile = re.sub(r'\D', '', raw_mobile) if raw_mobile else None
    user = User.query.filter_by(mobile=mobile).first()
    if user:
        return jsonify({"exists": True})
    return jsonify({"exists": False})

@auth_bp.route("/register", methods=["POST"])
def register():
    name = request.form.get("name")
    email = request.form.get("email")
    mobile = request.form.get("mobile")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")

    # 1. Basic Validations
    if not all([name, email, mobile, password, confirm_password]):
        flash("All fields are mandatory", "warning")
        return redirect(url_for("auth.login"))

    # 2. Email Validation
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        flash("Invalid email format", "warning")
        return redirect(url_for("auth.login"))

    # 3. Mobile Validation (10 digits after country code)
    # This logic assumes user might enter something like +91 1234567890
    clean_mobile = re.sub(r'\D', '', mobile)
    if len(clean_mobile) < 10:
        flash("Mobile must contain 10 digits", "warning")
        return redirect(url_for("auth.login"))
    
    # Check uniqueness
    if User.query.filter_by(mobile=mobile).first():
        flash("Mobile number already registered", "warning")
        return redirect(url_for("auth.login"))

    # 4. Password Validation
    if password != confirm_password:
        flash("Passwords do not match!", "warning")
        return redirect(url_for("auth.login"))

    # 5. Success Flow
    hashed_pass = generate_password_hash(password)
    new_user = User(name=name, email=email, mobile=clean_mobile, password=hashed_pass)
    
    # Auto-promote first user to Admin
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
