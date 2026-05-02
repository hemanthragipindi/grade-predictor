from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        mobile = request.form.get("mobile")
        password = request.form.get("password")
        user = User.query.filter_by(mobile=mobile).first()
        if user and check_password_hash(user.password, password):
            session.permanent = True
            login_user(user)
            if user.is_admin:
                return redirect(url_for("admin.dashboard"))
            return redirect(url_for("academic.dashboard"))
        flash("Invalid mobile or password", "warning")
    return render_template("auth.html")

@auth_bp.route("/register", methods=["POST"])
def register():
    name = request.form.get("name")
    email = request.form.get("email")
    mobile = request.form.get("mobile")
    password = request.form.get("password")
    
    if User.query.filter_by(mobile=mobile).first():
        flash("Mobile number already registered", "warning")
        return redirect(url_for('auth.login'))
        
    hashed_pass = generate_password_hash(password)
    
    # First user becomes admin
    is_first = User.query.count() == 0
    new_user = User(name=name, email=email, mobile=mobile, password=hashed_pass, is_admin=is_first)
    
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('auth.login') + "?registered=success")

@auth_bp.route("/check_mobile")
def check_mobile():
    mobile = request.args.get("mobile")
    user = User.query.filter_by(mobile=mobile).first()
    return jsonify({"exists": bool(user)})

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
