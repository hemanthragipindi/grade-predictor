from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user
from database import db
from models import Subject, Component, Marks, CAMarks, SyllabusFile, AssessmentProgress, StudyLog
from logic.grading import get_grade, is_practical, calc_ca_score
import math
import datetime
import os
import json

academic_bp = Blueprint('academic', __name__)

def get_subject_score_and_grade(subject_id):
    sub = Subject.query.get(subject_id)
    components = Component.query.filter_by(subject_id=subject_id).all()
    score = 0
    for comp in components:
        if comp.component_name != "Continuous Assessment":
            m = Marks.query.filter_by(subject_id=subject_id, component_id=comp.id).first()
            if m and comp.max_marks > 0:
                score += (m.marks_obtained / comp.max_marks) * comp.weight
        else:
            ca_rows = CAMarks.query.filter_by(subject_id=subject_id).all()
            if ca_rows:
                ca_score_contrib, _, _ = calc_ca_score(sub, ca_rows, comp.weight)
                score += math.ceil(ca_score_contrib)

    score = round(score, 2)
    grade, gpa = get_grade(score, sub.subject_code)
    return score, grade, gpa

@academic_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for('academic.dashboard'))
    return render_template("landing.html")

@academic_bp.route("/dashboard")
@login_required
def dashboard():
    from intelligence import AcademicBrain
    brain = AcademicBrain(db.session, current_user.id)
    subjects = Subject.query.filter_by(user_id=current_user.id).all()
    
    total_points = 0
    total_credits = 0
    high_count = 0

    for sub in subjects:
        score, grade, gpa = get_subject_score_and_grade(sub.id)
        credits = sub.credits if sub.credits else 0
        total_points += gpa*credits
        total_credits += credits
        if score < 60: high_count += 1
    
    cgpa = round(total_points/total_credits, 2) if total_credits > 0 else 0.0
    gpa_tier = brain.analyze_gpa_tier(cgpa)
    cog_load = brain.get_cognitive_load()
    identity = brain.get_user_identity()
    meta_insights = brain.get_meta_behavior_analysis()

    assessments_raw = AssessmentProgress.query.filter_by(subject_id=Subject.id).join(Subject).filter(Subject.user_id == current_user.id).all()
    assessments = []
    for a in assessments_raw:
        total_topics = len(a.topics) if a.topics else 0
        completed_topics = sum(1 for t in a.topics if t.get('completed')) if a.topics else 0
        progress = (completed_topics / total_topics * 100) if total_topics > 0 else 0
        sub = Subject.query.get(a.subject_id)
        assessments.append({
            "subject_code": sub.subject_code,
            "progress": round(progress, 1),
            "unit": a.unit_number
        })

    return render_template(
        "dashboard.html",
        cgpa=cgpa,
        subject_count=len(subjects),
        high_risk_count=high_count,
        gpa_tier=gpa_tier,
        cog_load=cog_load,
        identity=identity,
        meta_insights=meta_insights,
        assessments=assessments
    )

@academic_bp.route("/course-matrix")
@login_required
def active_matrix():
    from intelligence import AcademicBrain
    brain = AcademicBrain(db.session, current_user.id)
    subjects = Subject.query.filter_by(user_id=current_user.id).all()
    results = []
    
    for sub in subjects:
        score, grade, gpa = get_subject_score_and_grade(sub.id)
        results.append({
            "subject": sub,
            "score": score,
            "grade": grade,
            "gpa": gpa,
            "priority": "High" if score < 60 else "Medium" if score < 80 else "Low",
            "sensitivity": round(brain.gpa_sensitivity(sub.id), 3),
            "risk": brain.predict_failure_risk(sub.id)
        })

    return render_template("matrix.html", results=results)

@academic_bp.route("/analytics")
@login_required
def analytics():
    from intelligence import AcademicBrain
    brain = AcademicBrain(db.session, current_user.id)
    subjects = Subject.query.filter_by(user_id=current_user.id).all()
    
    total_points = 0
    total_credits = 0
    for sub in subjects:
        _, _, gpa = get_subject_score_and_grade(sub.id)
        total_points += gpa * (sub.credits or 0)
        total_credits += (sub.credits or 0)
    
    cgpa = round(total_points/total_credits, 2) if total_credits > 0 else 0.0
    
    return render_template("analytics.html",
        cgpa=cgpa,
        best_action=brain.get_best_action(),
        roi_analysis=brain.get_roi_analysis(),
        drop_vs_improve=brain.get_drop_vs_improve(),
        impact_metrics=brain.get_impact_metrics(),
        timeline=brain.get_insight_timeline(),
        radar_data=brain.get_subject_mastery_radar()
    )

@academic_bp.route("/history")
@login_required
def history():
    subjects = Subject.query.filter_by(user_id=current_user.id).all()
    history_data = []
    total_points = 0
    total_credits = 0
    
    for sub in subjects:
        score, grade, gpa = get_subject_score_and_grade(sub.id)
        history_data.append({
            "subject_code": sub.subject_code,
            "subject_name": sub.subject_name,
            "credits": sub.credits,
            "score": score,
            "grade": grade,
            "status": "COMPLETED" if score > 0 else "PENDING"
        })
        total_points += gpa * (sub.credits or 0)
        total_credits += (sub.credits or 0)
    
    cgpa = round(total_points/total_credits, 2) if total_credits > 0 else 0.0
    
    return render_template("history.html", subjects=history_data, cgpa=cgpa, total_credits=total_credits)

@academic_bp.route("/log_study", methods=["POST"])
@login_required
def log_study():
    data = request.json
    subject_code = data.get("subject_code")
    duration = data.get("duration")
    
    sub = Subject.query.filter_by(user_id=current_user.id, subject_code=subject_code).first()
    if not sub: return jsonify({"error": "Subject not found"}), 404
    
    new_log = StudyLog(user_id=current_user.id, subject_id=sub.id, duration_hours=float(duration))
    db.session.add(new_log)
    db.session.commit()
    
    return jsonify({"success": True, "message": "Neural focus logged.", "new_streak": 5})

@academic_bp.route("/assistant")
@login_required
def assistant():
    return render_template("assistant.html")

@academic_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    settings_path = os.path.join(os.getcwd(), 'backend', 'instance', 'settings.json')
    
    if request.method == "POST":
        # Simplified settings persistence for demo
        current_settings = {}
        if os.path.exists(settings_path):
            with open(settings_path, 'r') as f: current_settings = json.load(f)
            
        form_data = request.form.to_dict()
        current_settings.update(form_data)
        
        with open(settings_path, 'w') as f: json.dump(current_settings, f)
        flash("Architecture parameters updated.", "success")
        return redirect(url_for('academic.settings'))

    current_settings = {}
    if os.path.exists(settings_path):
        with open(settings_path, 'r') as f: current_settings = json.load(f)
        
    return render_template("settings.html", settings=current_settings)

@academic_bp.route("/subject/<int:subject_id>", methods=["GET", "POST"])
@login_required
def subject_page(subject_id):
    subject = Subject.query.get(subject_id)
    if not subject or subject.user_id != current_user.id:
        return redirect(url_for("academic.dashboard"))

    if request.method == "POST":
        for key in request.form:
            if key.startswith("marks_"):
                comp_id = int(key.split("_")[1])
                val = float(request.form[key]) if request.form[key] else 0
                m = Marks.query.filter_by(subject_id=subject_id, component_id=comp_id).first()
                if not m:
                    m = Marks(subject_id=subject_id, component_id=comp_id)
                    db.session.add(m)
                m.marks_obtained = val
        
        ca_marks = request.form.getlist("ca_marks[]")
        ca_max = request.form.getlist("ca_max[]")
        ca_weights = request.form.getlist("ca_weights[]")
        
        CAMarks.query.filter_by(subject_id=subject_id).delete()
        for i in range(len(ca_marks)):
            mk = float(ca_marks[i]) if ca_marks[i] else 0
            mx = float(ca_max[i]) if ca_max[i] else 0
            wt = float(ca_weights[i]) if i < len(ca_weights) and ca_weights[i] else 0
            if mx > 0 or mk > 0:
                db.session.add(CAMarks(subject_id=subject_id, marks=mk, max_marks=mx, weight=wt))
        
        db.session.commit()
        flash("Matrix parameters synchronized.", "success")
        return redirect(url_for("academic.subject_page", subject_id=subject_id))

    components = Component.query.filter_by(subject_id=subject_id).all()
    marks_raw = Marks.query.filter_by(subject_id=subject_id).all()
    entered_marks = {m.component_id: m.marks_obtained for m in marks_raw}
    ca_data = CAMarks.query.filter_by(subject_id=subject_id).all()
    ca_list = [{"marks": c.marks, "max": c.max_marks, "weight": c.weight} for c in ca_data]
    
    score, grade, gpa = get_subject_score_and_grade(subject_id)
    
    return render_template(
        "subject.html",
        subject=subject,
        components=components,
        entered_marks=entered_marks,
        ca_data=ca_list,
        score=score,
        grade=grade,
        is_prac=is_practical(subject),
        edit_mode=request.args.get("edit") == "1"
    )

@academic_bp.route("/semester/<int:semester_id>")
@login_required
def semester_page(semester_id):
    from intelligence import AcademicBrain
    brain = AcademicBrain(db.session, current_user.id)
    subjects = Subject.query.filter_by(user_id=current_user.id, semester=semester_id).all()
    
    results = []
    total_points = 0
    total_credits = 0
    for sub in subjects:
        score, grade, gpa = get_subject_score_and_grade(sub.id)
        results.append({
            "subject": sub,
            "score": score,
            "grade": grade,
            "gpa": gpa,
            "priority": "High" if score < 60 else "Medium",
            "rec": "Focus on mid-term recovery." if score < 60 else "Maintain structural integrity."
        })
        total_points += gpa * (sub.credits or 0)
        total_credits += (sub.credits or 0)
    
    tgpa = round(total_points/total_credits, 2) if total_credits > 0 else 0.0
    
    return render_template("semester.html", 
        semester_id=semester_id, 
        results=results, 
        tgpa=tgpa,
        analytics_data=[{"name": r['subject'].subject_code, "risk": r['score'], "sensitivity": r['gpa']} for r in results]
    )

@academic_bp.route("/cloud-drive")
@login_required
def cloud_drive():
    from models import CloudFile
    files = CloudFile.query.filter_by(user_id=current_user.id).order_by(CloudFile.timestamp.desc()).all()
    return render_template("cloud_drive.html", files=files)
