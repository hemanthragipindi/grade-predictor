from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from database import db
from models import User, Subject, AssessmentProgress
from functools import wraps

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        # Hardcoded Master Credentials
        if username == "ragipindihemanth" and password == "Hemanth@713":
            admin_user = User.query.filter_by(mobile="ADMIN").first()
            if not admin_user:
                admin_user = User(
                    name="Hemanth Ragipindi", 
                    email="admin@nexora.ai", 
                    mobile="ADMIN", 
                    password=generate_password_hash(password),
                    is_admin=True
                )
                db.session.add(admin_user)
                db.session.commit()
            
            login_user(admin_user)
            return redirect(url_for('admin.dashboard'))
        
        flash("Invalid Master Credentials", "warning")
    return render_template("admin/login.html")

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Access Denied: Admin privileges required.", "warning")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    users = User.query.all()
    stats = {
        "total_users": len(users),
        "total_subjects": Subject.query.count(),
        "total_progress": AssessmentProgress.query.count()
    }
    return render_template("admin/dashboard.html", users=users, stats=stats)

@admin_bp.route("/user/<int:user_id>")
@login_required
@admin_required
def view_user(user_id):
    user = User.query.get_or_404(user_id)
    subjects = Subject.query.filter_by(user_id=user.id).all()
    progress = AssessmentProgress.query.filter_by(subject_id=user.id).all() # Simplified for view
    return render_template("admin/user_detail.html", user=user, subjects=subjects, progress=progress)

@admin_bp.route("/make_admin/<int:user_id>")
@login_required
@admin_required
def make_admin(user_id):
    user = User.query.get_or_404(user_id)
    user.is_admin = True
    db.session.commit()
    flash(f"{user.name} is now an Admin", "success")
    return redirect(url_for('admin.dashboard'))
