from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
import intelligence
import cloudinary.uploader
from database import db
from models import CloudFile
import os
import datetime

api_bp = Blueprint('api', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'mp4', 'pdf', 'docx', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@api_bp.route("/upload", methods=["POST"])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        try:
            # Resource ID includes subfolder for organization
            # We use public_id to track it for deletion later
            result = cloudinary.uploader.upload(file, 
                folder=f"nexora_vault/user_{current_user.id}",
                resource_type="auto"
            )
            
            file_url = result['secure_url']
            public_id = result['public_id']
            
            new_file = CloudFile(
                user_id=current_user.id,
                file_name=file.filename,
                file_type=file.mimetype,
                file_url=file_url,
                public_id=public_id,
                provider='cloudinary'
            )
            db.session.add(new_file)
            db.session.commit()
            
            return jsonify({
                "success": True, 
                "url": file_url, 
                "provider": "cloudinary",
                "message": "Artifact secured in Cloudinary."
            })
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
            
    return jsonify({"error": "Invalid file type. Allowed: jpg, png, mp4, pdf, docx, xlsx"}), 400

@api_bp.route("/api/delete-file/<int:file_id>", methods=["DELETE"])
@login_required
def delete_file(file_id):
    file_record = CloudFile.query.get_or_404(file_id)
    
    # Security: Ensure user owns the file
    if file_record.user_id != current_user.id:
        return jsonify({"error": "Unauthorized access to artifact"}), 403
    
    try:
        # 1. Remove from Cloudinary
        # We need to specify resource_type if it's not an image
        resource_type = "image"
        if "video" in file_record.file_type: resource_type = "video"
        elif "pdf" in file_record.file_type or "doc" in file_record.file_type: resource_type = "raw"
        
        cloudinary.uploader.destroy(file_record.public_id, resource_type=resource_type)
        
        # 2. Remove from DB
        db.session.delete(file_record)
        db.session.commit()
        
        return jsonify({"success": True, "message": "Artifact purged from vault."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route("/api/chat", methods=["POST"])
@login_required
def chat_api():
    data = request.json
    user_msg = data.get("message")
    history = data.get("history", [])
    
    brain = intelligence.AcademicBrain(db.session)
    response_text = brain.get_ai_advice(user_msg, history)
    
    return jsonify({"response": response_text})
