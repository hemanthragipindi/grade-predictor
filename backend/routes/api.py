from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from flask_jwt_extended import jwt_required, get_jwt_identity
import intelligence
import cloudinary.uploader
from database import db
from models import User, CloudFile, Subject, Component, Marks, CAMarks, StudyLog
import os
import datetime
import re
from functools import wraps

from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash

api_bp = Blueprint('api', __name__)

@api_bp.route("/login", methods=["POST"])
def api_login():
    data = request.get_json()
    identifier = data.get("identifier") or data.get("mobile")
    password = data.get("password")
    
    clean_mobile = re.sub(r'\D', '', identifier) if identifier else ""
    user = User.query.filter((User.email == identifier) | (User.mobile == clean_mobile)).first()
    
    if user and user.password and check_password_hash(user.password, password):
        access_token = create_access_token(identity=user.id)
        return jsonify({
            "success": True,
            "token": access_token,
            "user": user.to_dict()
        })
    
    return jsonify({"success": False, "message": "Invalid credentials"}), 401

@api_bp.route("/register", methods=["POST"])
def api_register():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    mobile = data.get("mobile")
    password = data.get("password")

    if not all([name, email, mobile, password]):
        return jsonify({"success": False, "message": "Missing required fields"}), 400

    clean_mobile = re.sub(r'\D', '', mobile)
    if User.query.filter((User.email == email) | (User.mobile == clean_mobile)).first():
        return jsonify({"success": False, "message": "Email or Mobile already registered"}), 409

    hashed_pass = generate_password_hash(password)
    new_user = User(name=name, email=email, mobile=clean_mobile, password=hashed_pass)
    
    db.session.add(new_user)
    db.session.commit()
    
    access_token = create_access_token(identity=new_user.id)
    return jsonify({
        "success": True,
        "token": access_token,
        "user": new_user.to_dict()
    }), 201

@api_bp.route("/google", methods=["POST"])
def api_google_login():
    data = request.get_json()
    id_token = data.get("id_token")
    if not id_token:
        return jsonify({"success": False, "message": "ID Token required"}), 400
    
    # Mocking user info for demo purposes
    email = data.get("email")
    name = data.get("name")
    
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(name=name, email=email, mobile=None, password=None)
        db.session.add(user)
        db.session.commit()
    
    access_token = create_access_token(identity=user.id)
    return jsonify({
        "success": True,
        "token": access_token,
        "user": user.to_dict()
    })

def hybrid_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # 1. Try Flask-Login (Session)
        if current_user.is_authenticated:
            return f(current_user.id, *args, **kwargs)
        
        # 2. Try JWT
        try:
            from flask_jwt_extended import verify_jwt_in_request
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            return f(user_id, *args, **kwargs)
        except:
            return jsonify({"success": False, "message": "Authentication required"}), 401
    return decorated

@api_bp.route("/dashboard", methods=["GET"])
@hybrid_auth
def get_dashboard(user_id):
    from intelligence import AcademicBrain
    brain = AcademicBrain(db.session, user_id)
    subjects = Subject.query.filter_by(user_id=user_id).all()
    
    total_points = 0
    total_credits = 0
    high_risk_count = 0
    
    # Simple GPA logic for API
    for sub in subjects:
        from logic.scoring import get_subject_score_and_grade
        score, grade, gpa = get_subject_score_and_grade(sub.id)
        total_points += gpa * (sub.credits or 0)
        total_credits += (sub.credits or 0)
        if score < 60: high_risk_count += 1

    cgpa = round(total_points/total_credits, 2) if total_credits > 0 else 0.0
    
    return jsonify({
        "success": True,
        "data": {
            "cgpa": cgpa,
            "subject_count": len(subjects),
            "high_risk_count": high_risk_count,
            "gpa_tier": brain.analyze_gpa_tier(cgpa),
            "cognitive_load": brain.get_cognitive_load(),
            "insights": brain.get_meta_behavior_analysis()[:3]
        }
    })

@api_bp.route("/version", methods=["GET"])
def get_version():
    return jsonify({
        "version": "1.0.1",
        "apk_url": "https://github.com/hemanthragipindi/grade-predictor/releases/latest/download/app-release.apk",
        "force_update": True
    })

@api_bp.route("/subjects", methods=["GET", "POST"])
@hybrid_auth
def manage_subjects(user_id):
    if request.method == "GET":
        subjects = Subject.query.filter_by(user_id=user_id).all()
        return jsonify({
            "success": True,
            "data": [s.to_dict() for s in subjects]
        })
    
    data = request.get_json()
    new_sub = Subject(
        user_id=user_id,
        subject_code=data.get("subject_code"),
        subject_name=data.get("subject_name"),
        credits=data.get("credits"),
        semester=data.get("semester", 2)
    )
    db.session.add(new_sub)
    db.session.commit()
    return jsonify({"success": True, "data": new_sub.to_dict()}), 201

@api_bp.route("/predictions", methods=["GET"])
@hybrid_auth
def get_predictions(user_id):
    from intelligence import AcademicBrain
    brain = AcademicBrain(db.session, user_id)
    subjects = Subject.query.filter_by(user_id=user_id).all()
    
    results = []
    from logic.scoring import get_subject_score_and_grade
    for sub in subjects:
        score, grade, gpa = get_subject_score_and_grade(sub.id)
        results.append({
            "subject_code": sub.subject_code,
            "current_score": score,
            "predicted_grade": grade,
            "risk": brain.predict_failure_risk(sub.id)
        })
    
    return jsonify({"success": True, "data": results})

@api_bp.route("/upload", methods=["POST"])
@hybrid_auth
def upload_file(user_id):
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '' or not file:
        return jsonify({"error": "No selected file"}), 400
    
    # Validation
    allowed_ext = {'png', 'jpg', 'jpeg', 'mp4', 'pdf', 'docx', 'xlsx'}
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if ext not in allowed_ext:
        return jsonify({"error": "Unsupported file type"}), 400

    try:
        result = cloudinary.uploader.upload(file, 
            folder=f"nexora_vault/user_{user_id}",
            resource_type="auto"
        )
        
        new_file = CloudFile(
            user_id=user_id,
            file_name=file.filename,
            file_type=file.mimetype,
            file_url=result['secure_url'],
            public_id=result['public_id'],
            provider='cloudinary'
        )
        db.session.add(new_file)
        db.session.commit()
        
        return jsonify({"success": True, "data": new_file.to_dict()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route("/files", methods=["GET"])
@hybrid_auth
def get_files(user_id):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    files_query = CloudFile.query.filter_by(user_id=user_id).order_by(CloudFile.timestamp.desc())
    pagination = files_query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        "success": True,
        "data": [f.to_dict() for f in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page
    })

@api_bp.route("/files/<int:file_id>", methods=["DELETE"])
@hybrid_auth
def delete_file(user_id, file_id):
    file_record = CloudFile.query.filter_by(id=file_id, user_id=user_id).first_or_404()
    
    try:
        resource_type = "image"
        if "video" in file_record.file_type: resource_type = "video"
        elif any(x in file_record.file_type for x in ["pdf", "doc", "sheet"]): resource_type = "raw"
        
        cloudinary.uploader.destroy(file_record.public_id, resource_type=resource_type)
        db.session.delete(file_record)
        db.session.commit()
        
        return jsonify({"success": True, "message": "File deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
