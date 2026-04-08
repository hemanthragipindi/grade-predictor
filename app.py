from flask import Flask, render_template, request, redirect, url_for, jsonify
from config import Config
from database import db
from models import Subject, Component, Marks, CAMarks, SyllabusFile, AssessmentProgress
from werkzeug.utils import secure_filename
import os
import math
import random
from google import genai

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

api_key = os.environ.get("GEMINI_API_KEY")
client = None
if api_key:
    client = genai.Client(api_key=api_key)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///grades.db'
db.init_app(app)

with app.app_context():
    db.create_all()

# -----------------------
# FEATURE FLAGS (Demo Control)
# -----------------------
ENABLE_AI = True
ENABLE_GAMIFICATION = True
ENABLE_STUDY_LOGS = True


# -----------------------
# GRADE SYSTEM
# -----------------------

def get_grade(score, subject_code=None):
    if subject_code == "CSE326":
        if score >= 84: return "O", 10.0
        elif score >= 75: return "A+", 9.0
        elif score >= 65: return "A", 8.0
        elif score >= 55: return "B+", 7.0
        elif score >= 45: return "B", 6.0
        elif score >= 40: return "C", 5.0
        else: return "F", 0.0

    if score >= 90:
        return "O",10.0
    elif score >= 80:
        return "A+",9.0
    elif score >= 70:
        return "A",8.0
    elif score >= 60:
        return "B+",7.0
    elif score >= 50:
        return "B",6.0
    elif score >= 40:
        return "C", 5.0
    else:
        return "F",0.0

def is_practical(subject):
    s = f"{subject.subject_code or ''} {subject.subject_name or ''}".lower()
    # List of practical/special subjects from the screenshot (No Mid-Term)
    practical_codes = ['cse101', 'cse121', 'ece279', 'int306']
    practical_keywords = ['laboratory', 'practical', 'lab']
    
    return any(code in s for code in practical_codes) or any(kw in s for kw in practical_keywords)

def calc_ca_score(subject, ca_rows, comp_weight):
    if is_practical(subject):
        written_ratio = (ca_rows[0].marks / ca_rows[0].max_marks) if len(ca_rows)>0 and ca_rows[0].max_marks>0 else 0
        practice_ratio = (ca_rows[1].marks / ca_rows[1].max_marks) if len(ca_rows)>1 and ca_rows[1].max_marks>0 else 0
        other1_ratio = (ca_rows[2].marks / ca_rows[2].max_marks) if len(ca_rows)>2 and ca_rows[2].max_marks>0 else 0
        other2_ratio = (ca_rows[3].marks / ca_rows[3].max_marks) if len(ca_rows)>3 and ca_rows[3].max_marks>0 else 0
        
        best_other_ratio = max(other1_ratio, other2_ratio)
        
        ca_custom_total = (written_ratio * 20) + (practice_ratio * 15) + (best_other_ratio * 15)
        return (ca_custom_total / 50.0) * comp_weight, round(ca_custom_total, 2), 50.0
    else:
        ca_total = sum(c.marks for c in ca_rows)
        ca_max = sum(c.max_marks for c in ca_rows)
        if ca_max > 0:
            return (ca_total / ca_max) * comp_weight, ca_total, ca_max
        return 0, 0, 0

def get_subject_score_and_grade(subject_id):
    sub = Subject.query.get(subject_id)
    components = Component.query.filter_by(subject_id=subject_id).all()
    score = 0
    for comp in components:
        if comp.component_name == "Attendance":
            # Use entered marks if available, otherwise assume full marks
            mark = Marks.query.filter_by(subject_id=sub.id, component_id=comp.id).first()
            if mark and comp.max_marks > 0:
                score += math.ceil((mark.marks_obtained / comp.max_marks) * comp.weight)
            else:
                score += comp.weight
            continue
        
        if comp.component_name == "Continuous Assessment":
            continue # Calculated separately via CAMarks

        mark = Marks.query.filter_by(
            subject_id=sub.id,
            component_id=comp.id
        ).first()

        if mark:
            score += math.ceil((mark.marks_obtained/comp.max_marks)*comp.weight)

    ca_rows = CAMarks.query.filter_by(subject_id=sub.id).order_by(CAMarks.id).all()
    for comp in components:
        if comp.component_name=="Continuous Assessment":
            ca_score_contrib, _, _ = calc_ca_score(sub, ca_rows, comp.weight)
            score += math.ceil(ca_score_contrib)

    score = round(score,2)
    grade,gpa = get_grade(score, sub.subject_code)
    return score, grade, gpa


# -----------------------
# ADD SUBJECT
# -----------------------

@app.route("/add_subject", methods=["GET", "POST"])
def add_subject():
    if request.method == "POST":
        sub_code = request.form.get("subject_code")
        sub_name = request.form.get("subject_name")
        credits = request.form.get("credits", type=int)
        semester = request.form.get("semester", type=int)
        
        sub = Subject(subject_code=sub_code, subject_name=sub_name, credits=credits, semester=semester)
        db.session.add(sub)
        db.session.commit()
        
        comps = [
            Component(subject_id=sub.id, component_name="Attendance", max_marks=5, weight=5),
            Component(subject_id=sub.id, component_name="Continuous Assessment", max_marks=50, weight=25),
            Component(subject_id=sub.id, component_name="Mid Term Exam", max_marks=20, weight=20),
            Component(subject_id=sub.id, component_name="End Term Exam", max_marks=50, weight=50)
        ]
        db.session.add_all(comps)
        db.session.commit()
        
        return redirect(url_for("subject_page", subject_id=sub.id))
        
    return render_template("add_subject.html")

# -----------------------
# DASHBOARD
# -----------------------

@app.route("/")
def dashboard():
    from intelligence import AcademicBrain
    brain = AcademicBrain(db.session)
    subjects = Subject.query.all()
    
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
    
    # Overview Intelligence
    gpa_tier = brain.analyze_gpa_tier(cgpa)
    cog_load = brain.get_cognitive_load()
    learning_insights = brain.get_learning_insights()
    identity = brain.get_user_identity()
    meta_insights = brain.get_meta_behavior_analysis()

    # Assessment Progress (Real Data)
    assessments_raw = AssessmentProgress.query.all()
    assessments = []
    for a in assessments_raw:
        total_topics = len(a.topics) if a.topics else 0
        completed_topics = sum(1 for t in a.topics if t.get('completed')) if a.topics else 0
        progress = (completed_topics / total_topics * 100) if total_topics > 0 else 0
        sub = Subject.query.get(a.subject_id)
        assessments.append({
            "subject_code": sub.subject_code if sub else "Unknown",
            "progress": round(progress, 1),
            "unit": a.unit_number
        })

    return render_template(
        "dashboard.html",
        cgpa=cgpa,
        total_credits=total_credits,
        subject_count=len(subjects),
        high_risk_count=high_count,
        gpa_tier=gpa_tier,
        cog_load=cog_load,
        learning_insights=learning_insights,
        identity=identity,
        meta_insights=meta_insights,
        assessments=assessments,
        ENABLE_AI=ENABLE_AI,
        ENABLE_GAMIFICATION=ENABLE_GAMIFICATION
    )

@app.route("/course-matrix")
def active_matrix():
    from intelligence import AcademicBrain
    brain = AcademicBrain(db.session)
    subjects = Subject.query.all()
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

@app.route("/semester/<int:semester_id>")
def semester_view(semester_id):
    subjects = Subject.query.filter_by(semester=semester_id).all()
    results = []
    total_points = 0
    total_credits = 0

    for sub in subjects:
        score, grade, gpa = get_subject_score_and_grade(sub.id)
        credits = sub.credits if sub.credits else 0
        total_points += gpa*credits
        total_credits += credits

        if score < 60:
            priority = "High"
            recommendation = "Critical attention required. Invest 4+ extra hours/week."
        elif score < 80:
            priority = "Medium"
            recommendation = "Consolidating knowledge. Target weak topics."
        else:
            priority = "Low"
            recommendation = "Optimization phase. Maintain current habits."

        results.append({
            "subject":sub,
            "score":score,
            "grade":grade,
            "gpa":gpa,
            "priority": priority,
            "recommendation": recommendation
        })

    tgpa = 0
    if total_credits>0:
        tgpa = round(total_points/total_credits,2)

    from intelligence import AcademicBrain
    brain = AcademicBrain(db.session)
    advisor_report = brain.analyze_situation(tgpa)
    risk_sim = brain.risk_simulation()
    
    analytics_data = []
    for r in results:
        sub_id = r['subject'].id
        analytics_data.append({
            "subject_id": sub_id,
            "risk": brain.predict_failure_risk(sub_id),
            "sensitivity": brain.gpa_sensitivity(sub_id)
        })

    return render_template(
        "semester.html",
        semester_id=semester_id,
        results=results,
        tgpa=tgpa,
        analytics=analytics_data,
        advisor=advisor_report,
        risk_sim=risk_sim
    )




@app.route("/assistant")
def assistant():
    return render_template("assistant.html")

@app.route("/analytics")
def analytics():
    subjects = Subject.query.all()
    results = []
    for sub in subjects:
        score, grade, gpa = get_subject_score_and_grade(sub.id)
        results.append({
            "subject": sub,
            "score": score,
            "grade": grade,
            "gpa": gpa
        })
    from intelligence import AcademicBrain
    brain = AcademicBrain(db.session)
    cgpa = 0
    total_points = sum(r['gpa']*r['subject'].credits for r in results)
    total_credits = sum(r['subject'].credits for r in results)
    if total_credits > 0: cgpa = total_points / total_credits

    best_action = brain.get_best_action()
    roi_data = brain.get_roi_analysis()
    decisions = brain.get_drop_vs_improve()
    impact_metrics = brain.get_impact_metrics()
    timeline = brain.get_insight_timeline()
    radar_data = brain.get_subject_mastery_radar()

    return render_template(
        "analytics.html", 
        results=results, 
        best_action=best_action, 
        roi_data=roi_data, 
        decisions=decisions,
        impact_metrics=impact_metrics,
        timeline=timeline,
        radar_data=radar_data
    )

from models import Subject, Component, Marks, CAMarks, StudyLog

# ... other imports ...

@app.route("/log_study", methods=["POST"])
def log_study():
    if not ENABLE_STUDY_LOGS:
        return jsonify({"success": False, "message": "Module disabled"}), 403
    
    data = request.get_json()
    sub_code = data.get("subject_code")
    duration = data.get("duration", 1.0) # Default 1 hour if not specified
    
    sub = Subject.query.filter_by(subject_code=sub_code).first()
    if sub:
        log = StudyLog(subject_id=sub.id, duration_hours=duration)
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "message": f"Study session of {duration}h logged for {sub_code}!",
            "new_streak": 6
        })
    return jsonify({"success": False, "message": "Subject not found"}), 404

@app.route("/models")
def models():
    return render_template("models.html")

@app.route("/study-planner")
def study_planner():
    from intelligence import AcademicBrain
    brain = AcademicBrain(db.session)
    
    cog_load = brain.get_cognitive_load()
    learning_insights = brain.get_learning_insights()
    identity = brain.get_user_identity()
    roi_data = brain.get_roi_analysis()
    timeline = brain.get_insight_timeline()
    
    # Mock some data for the habit tracker part since we don't have a specific table for habits yet
    # but we can structure it for the template
    return render_template(
        "study_planner.html",
        cog_load=cog_load,
        learning_insights=learning_insights,
        identity=identity,
        roi_data=roi_data,
        timeline=timeline
    )


@app.route("/syllabus", methods=["GET", "POST"])
def syllabus():
    from models import Subject, SyllabusFile
    if request.method == "POST":
        sub_id = request.form.get("subject_id")
        file = request.files.get("syllabus_file")
        
        if file and file.filename:
            filename = f"Syllabus_{sub_id}_" + secure_filename(file.filename)
            upload_dir = os.path.join(app.root_path, 'static', 'uploads', 'syllabus')
            os.makedirs(upload_dir, exist_ok=True)
            path = os.path.join(upload_dir, filename)
            file.save(path)
            
            # Enforce ONE syllabus per subject: delete existing
            SyllabusFile.query.filter_by(subject_id=sub_id).delete()
            
            new_syllabus = SyllabusFile(
                subject_id=sub_id, 
                file_path=f"/static/uploads/syllabus/{filename}"
            )
            db.session.add(new_syllabus)
            db.session.commit()
            return redirect(url_for('syllabus'))
            
    subjects = Subject.query.all()
    syllabus_map = {}
    for sub in subjects:
        file = SyllabusFile.query.filter_by(subject_id=sub.id).first()
        syllabus_map[sub.id] = file
        
    return render_template("syllabus.html", subjects=subjects, syllabus_map=syllabus_map)

@app.route("/history")
def history():
    subjects = Subject.query.all()
    results = []
    total_points = 0
    total_credits = 0

    for sub in subjects:
        score, grade, gpa = get_subject_score_and_grade(sub.id)
        credits = sub.credits if sub.credits else 0
        total_points += gpa*credits
        total_credits += credits
        
        results.append({
            "subject": sub,
            "score": score,
            "grade": grade if score > 0 else "-",
            "gpa": gpa,
            "credits": credits,
            "status": "COMPLETED" if score > 0 else "PENDING"
        })

    cgpa = 0
    if total_credits>0:
        cgpa = round(total_points/total_credits,2)

    return render_template(
        "history.html",
        results=results,
        cgpa=cgpa,
        total_credits=total_credits
    )

import json
SETTINGS_FILE = "settings.json"
DEFAULT_SETTINGS = {
    "first_name": "Julian",
    "last_name": "Admin",
    "institution": "Global Institute of Architectural Analytics",
    "grading_scale": "4.0",
    "semester_intervals": "16 Weeks (Traditional)",
    "auto_archive": True,
    "gpa_drop_warning": True,
    "project_deadlines": True,
    "weekly_digest": False,
    "ntfy_topic": "" # User sets this to get mobile/laptop notifications
}

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return DEFAULT_SETTINGS.copy()
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
            merged = DEFAULT_SETTINGS.copy()
            merged.update(data)
            return merged
    except:
        return DEFAULT_SETTINGS.copy()

def save_settings(data):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f)

import datetime

@app.context_processor
def inject_settings():
    return dict(
        user_settings=load_settings(),
        current_hour=datetime.datetime.now().hour
    )

@app.route("/settings", methods=["GET", "POST"])
def settings_page():
    if request.method == "POST":
        current = load_settings()
        current["first_name"] = request.form.get("first_name", current["first_name"])
        current["last_name"] = request.form.get("last_name", current["last_name"])
        current["institution"] = request.form.get("institution", current["institution"])
        current["grading_scale"] = request.form.get("grading_scale", current["grading_scale"])
        current["semester_intervals"] = request.form.get("semester_intervals", current["semester_intervals"])
        current["auto_archive"] = request.form.get("auto_archive") == "on"
        current["gpa_drop_warning"] = request.form.get("gpa_drop_warning") == "on"
        current["project_deadlines"] = request.form.get("project_deadlines") == "on"
        current["weekly_digest"] = request.form.get("weekly_digest") == "on"
        current["ntfy_topic"] = request.form.get("ntfy_topic", "").strip()
        
        profile_file = request.files.get("profile_pic")
        if profile_file and profile_file.filename:
            from werkzeug.utils import secure_filename
            import os
            filename = secure_filename(profile_file.filename)
            upload_dir = os.path.join(app.root_path, 'static', 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            path = os.path.join(upload_dir, filename)
            profile_file.save(path)
            current["profile_pic_url"] = f"/static/uploads/{filename}"
            
        save_settings(current)
        return jsonify({"status": "success"})
    return render_template("settings.html")




@app.route("/api/test_notification", methods=["POST"])
def test_notification():
    from notifications import send_notification
    success = send_notification(
        "Nexora Test Alert", 
        "Congratulations! Your real-time notification engine is now synced with your device.",
        priority="high"
    )
    if success:
        return jsonify({"status": "success", "message": "Notification sent successfully!"})
    return jsonify({"status": "error", "message": "Failed to send notification. Check your topic settings."})

@app.route("/api/notification_status")
def notification_status():
    settings = load_settings()
    topic = settings.get("ntfy_topic", "").strip()
    return jsonify({
        "synced": bool(topic),
        "topic": topic
    })

@app.route("/subject/<int:subject_id>",methods=["GET","POST"])
def subject_page(subject_id):

    subject = Subject.query.get(subject_id)

    components = Component.query.filter_by(subject_id=subject_id).all()

    edit_mode = request.args.get("edit")

    # -----------------------
    # SAVE DATA
    # -----------------------

    if request.method=="POST":
        old_score, old_grade, _ = get_subject_score_and_grade(subject_id)


        for comp in components:

            if comp.component_name!="Continuous Assessment":

                marks=request.form.get(f"marks_{comp.id}")

                if marks:

                    row = Marks.query.filter_by(
                        subject_id=subject_id,
                        component_id=comp.id
                    ).first()

                    if row:
                        row.marks_obtained=float(marks)
                    else:
                        row=Marks(
                            subject_id=subject_id,
                            component_id=comp.id,
                            marks_obtained=float(marks)
                        )
                        db.session.add(row)

        # SAVE CA MARKS

        CAMarks.query.filter_by(subject_id=subject_id).delete()

        ca_marks=request.form.getlist("ca_marks[]")
        ca_max=request.form.getlist("ca_max[]")

        for m,mx in zip(ca_marks,ca_max):

            if m and mx:
                row=CAMarks(
                    subject_id=subject_id,
                    marks=float(m),
                    max_marks=float(mx)
                )
                db.session.add(row)
            elif is_practical(subject):
                row=CAMarks(
                    subject_id=subject_id,
                    marks=0.0,
                    max_marks=0.0
                )
                db.session.add(row)

        db.session.commit()

        new_score, new_grade, _ = get_subject_score_and_grade(subject_id)
        if new_score < old_score:
            from notifications import send_notification
            send_notification(
                f"Grade Update: {subject.subject_code}",
                f"⚠️ Performance Alert! Current score dropped from {old_score} to {new_score}. Current Grade: {new_grade}",
                priority="high"
            )
        elif new_score > old_score:
            from notifications import send_notification
            send_notification(
                f"Academic Gain: {subject.subject_code}",
                f"🚀 Multi-Factor Improvement! Score increased from {old_score} to {new_score}. New Grade: {new_grade}",
                priority="default"
            )

        return redirect(url_for("subject_page",subject_id=subject_id) + "#top")


    # -----------------------
    # LOAD COMPONENT MARKS
    # -----------------------

    entered_marks={}

    for comp in components:

        row=Marks.query.filter_by(
            subject_id=subject_id,
            component_id=comp.id
        ).first()

        if row:
            entered_marks[comp.id]=row.marks_obtained


    # -----------------------
    # LOAD CA MARKS
    # -----------------------

    ca_rows=CAMarks.query.filter_by(subject_id=subject_id).order_by(CAMarks.id).all()

    ca_data=[]

    for row in ca_rows:

        ca_data.append({
            "marks":row.marks,
            "max":row.max_marks
        })


    # -----------------------
    # SCORE CALCULATION
    # -----------------------

    score = 0

    for comp in components:
        if comp.component_name == "Attendance":
            # Use entered marks if available, otherwise assume full marks
            mark = Marks.query.filter_by(subject_id=subject_id, component_id=comp.id).first()
            if mark and comp.max_marks > 0:
                score += math.ceil((mark.marks_obtained / comp.max_marks) * comp.weight)
            else:
                score += comp.weight
            continue
            
        if comp.component_name == "Continuous Assessment":
            continue # Calculated separately via CAMarks

        mark = Marks.query.filter_by(
            subject_id=subject_id,
            component_id=comp.id
        ).first()

        if mark:
            score += math.ceil((mark.marks_obtained/comp.max_marks)*comp.weight)

    ca_rows = CAMarks.query.filter_by(subject_id=subject_id).order_by(CAMarks.id).all()

    ca_total = 0
    ca_max = 0

    for comp in components:
        if comp.component_name=="Continuous Assessment":
            ca_score_contrib, ca_total, ca_max = calc_ca_score(subject, ca_rows, comp.weight)
            score += math.ceil(ca_score_contrib)

    score = round(score,2)

    grade,gpa = get_grade(score, subject.subject_code)


    # -----------------------
    # GRADE PREDICTION
    # -----------------------

    # GRADE PREDICTION ENGINE (MID-TERM FOCUS)
    prediction = []
    grade_targets = {"O": 90, "A+": 80, "A": 70}

    midterm_comp = next((c for c in components if any(k in c.component_name.upper() for k in ["MID TERM", "MID-TERM", "MTE", "MIDTERM"])), None)
    endterm_comp = next((c for c in components if any(k in c.component_name.upper() for k in ["END TERM", "END-TERM", "ETE", "ENDTERM"])), None)
    
    m_mark = Marks.query.filter_by(subject_id=subject_id, component_id=midterm_comp.id).first() if midterm_comp else None
    e_mark = Marks.query.filter_by(subject_id=subject_id, component_id=endterm_comp.id).first() if endterm_comp else None

    # Logic: If mark is missing or exactly 0, consider it pending for prediction purposes
    is_m_pending = midterm_comp and (m_mark is None or m_mark.marks_obtained == 0)
    is_e_pending = endterm_comp and (e_mark is None or e_mark.marks_obtained == 0)

    for g, target in grade_targets.items():
        if score >= target:
            prediction.append({"grade": g, "target_score": target, "achieved": True})
            continue

        p_entry = {"grade": g, "target_score": target}
        
        if midterm_comp and is_m_pending and endterm_comp and is_e_pending:
            # BOTH PENDING: Standard "No Fear" Strategy (75% End Term effort)
            safe_end_contrib = (75.0 / 100.0) * endterm_comp.weight
            mid_contrib_needed = target - score - safe_end_contrib
            mid_raw = (mid_contrib_needed / midterm_comp.weight) * midterm_comp.max_marks
            
            p_entry["mid_goal"] = {
                "score": round(mid_raw, 1),
                "max": midterm_comp.max_marks,
                "label": "Confidence Mid Target",
                "notes": "Reach this to keep End Terms easy (Max 75% effort)."
            }

            # If Mid is impossible with 75% End Term effort, try Intense Strategy (90% End Term effort)
            if mid_raw > midterm_comp.max_marks:
                intense_end_contrib = (90.0 / 100.0) * endterm_comp.weight
                mid_contrib_intense = target - score - intense_end_contrib
                mid_raw_intense = (mid_contrib_intense / midterm_comp.weight) * midterm_comp.max_marks
                
                p_entry["mid_goal"]["score"] = max(0, min(midterm_comp.max_marks, round(mid_raw_intense, 1)))
                p_entry["mid_goal"]["label"] = "High Effort Mid"
                p_entry["mid_goal"]["notes"] = "Must score high. End Term effort will also need to be 90%."
                
                # If still impossible even with 90% End Term, mark as Narrow Margin
                if mid_raw_intense > midterm_comp.max_marks:
                     p_entry["mid_goal"]["score"] = midterm_comp.max_marks
                     p_entry["mid_goal"]["label"] = "Max Effort Required"
                     p_entry["mid_goal"]["notes"] = "Even with full Mid marks, you'll need a perfect End Term."
            elif mid_raw < 0:
                p_entry["mid_goal"]["score"] = 0
                p_entry["mid_goal"]["label"] = "Safety Secured"
                p_entry["mid_goal"]["notes"] = "You're in a great spot! Even 0 here keeps your target in reach."
        elif endterm_comp and is_e_pending:
            # ONLY END TERM PENDING: Show required marks
            end_diff = target - score
            if end_diff > 0:
                end_req_raw = (end_diff / endterm_comp.weight) * endterm_comp.max_marks
                p_entry["end_req"] = {
                    "score": round(end_req_raw, 1) if end_req_raw <= endterm_comp.max_marks else "N/A",
                    "max": endterm_comp.max_marks
                }
            else:
                p_entry["achieved"] = True
        elif midterm_comp and is_m_pending:
            mid_diff = target - score
            if mid_diff > 0:
                mid_req_raw = (mid_diff / midterm_comp.weight) * midterm_comp.max_marks
                p_entry["mid_goal"] = {
                    "score": round(mid_req_raw, 1) if mid_req_raw <= midterm_comp.max_marks else "N/A",
                    "max": midterm_comp.max_marks,
                    "label": "Required Mid-Term",
                    "notes": "End Terms are already graded or not detected."
                }
            else:
                p_entry["achieved"] = True
        else:
            p_entry["completed_all"] = True

        prediction.append(p_entry)

    return render_template(
        "subject.html",
        subject=subject,
        components=components,
        entered_marks=entered_marks,
        ca_data=ca_data,
        ca_total=ca_total,
        ca_max=ca_max,
        score=score,
        grade=grade,
        prediction=prediction,
        edit_mode=edit_mode,
        is_prac=is_practical(subject)
    )

# -----------------------
# AI CHATBOT
# -----------------------

@app.route("/api/chat", methods=["POST"])
def chat_api():
    if not os.environ.get("GEMINI_API_KEY"):
        return jsonify({"response": "I'm sorry, I cannot think right now because the **GEMINI_API_KEY** is not set in the environment variables. Please add it to your `.env` file or system environment."}), 200
    
    import json
    import tempfile
    from werkzeug.utils import secure_filename
    import re
    
    if request.is_json:
        data = request.json
        user_message = data.get("message", "")
        history_data = data.get("history", [])
        files = []
    else:
        user_message = request.form.get("message", "")
        history_str = request.form.get("history", "[]")
        try:
            history_data = json.loads(history_str)
        except:
            history_data = []
        files = request.files.getlist("files")
    
    if not user_message and not files:
        return jsonify({"response": "Please say something."}), 200
        
    try:
        from intelligence import AcademicBrain
        brain = AcademicBrain(db.session)
        user_context = brain.get_context_for_ai()
        
        system_prompt = (
            "You are Nexora AI, a universal intelligence powered by Gemini. "
            "You are deeply integrated into the CGPA PREDICTOR app and have access to the user's REAL data. "
            f"\n\n{user_context}\n"
            "Use this data to give SPECIFIC, direct advice (e.g., 'Focus on Physics Unit 3' or 'Your Math ROI is low'). "
            "Always be concise, professional, and strategic. If a user asks 'What should I do?', "
            "analyze their lowest scores and highest credit subjects first."
        )
        
        # Format history for Gemini API
        formatted_history = []
        for msg in history_data:
            # SDK expects 'user' and 'model'
            role = "model" if msg.get("role") == "ai" else "user"
            content = msg.get("content", "")
            # Strip simple HTML from content representation and remove meta-data strings
            clean_content = re.sub(r'<[^>]+>', '', content).strip()
            if clean_content:
                # FIX: Parts must be dictionaries for Pydantic validation
                formatted_history.append({"role": role, "parts": [{"text": clean_content}]})
        
        if not client:
            return jsonify({"response": "AI Client not initialized. Please check your API key."}), 500

        # Create chat session with formatted history
        chat = client.chats.create(
            model='gemini-1.5-flash',
            config={'system_instruction': system_prompt},
            history=formatted_history
        )
        
        uploaded_gemini_files = []
        # Note: uploaded_gemini_files are already objects from client.files.upload
        for f in files:
            if f.filename:
                temp_dir = tempfile.gettempdir()
                filepath = os.path.join(temp_dir, secure_filename(f.filename))
                f.save(filepath)
                # Upload to Gemini
                g_file = client.files.upload(path=filepath)
                uploaded_gemini_files.append(g_file)
        
        message_parts = []
        for f in uploaded_gemini_files:
            message_parts.append(f)
            
        if user_message:
            # FIX: If we have ONLY text, send as string for broad compatibility
            if not uploaded_gemini_files:
                message_parts = user_message
            else:
                message_parts.append({"text": user_message})
        elif not message_parts:
            message_parts = "Hello"
            
        # FIX: Ensure we send message_parts in correct format
        response = chat.send_message(message_parts)
        
        import markdown
        html_response = markdown.markdown(response.text)
        return jsonify({"response": html_response, "text": response.text}), 200
    except Exception as e:
        error_msg = str(e)
        friendly_error = (
            f"**TECHNICAL ERROR DETECTED**\n\n"
            f"The AI core encountered an issue: `{error_msg}`\n\n"
            "This error indicates that either the model name is not recognized or the API key doesn't have access to it. "
            "I have updated the system to use the most stable model available."
        )
        import markdown
        return jsonify({"response": friendly_error, "debug_error": error_msg}), 200

@app.route("/api/daily-slogan")
def daily_slogan_api():
    offline_slogans = [
        "Architect Your Future, One Insight at a Time.",
        "Master the Moment. Own the Result.",
        "Precision in Strategy. Excellence in Outcome.",
        "Your Potential, Architecturalized.",
        "Data-Driven Dreams. Discipline-Focused Days.",
        "Sync Your Strategy. Own Your Success.",
        "The Best Way to Predict Your Grade is to Create it."
    ]
    
    if not client or not os.environ.get("GEMINI_API_KEY"):
        import random
        return jsonify({"slogan": random.choice(offline_slogans)}), 200
    
    try:
        current_date = datetime.datetime.now().strftime("%B %d, %Y %H:%M:%S")
        import random
        noise = random.randint(1, 1000)
        prompt = (
            f"Today is {current_date}. Random Seed: {noise}. "
            "Generate one highly creative, unique, and modern motivational slogan "
            "for a student using a study planner app called Nexora. "
            "IMPORTANT: Make this one different from common academic slogans. "
            "Keep it under 8 words. Avoid clichés. Make it sound sophisticated and data-driven."
        )
        
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=[{"role": "user", "parts": [{"text": prompt}]}]
        )
        
        slogan = response.text.replace('"', '').replace('*', '').strip()
        if len(slogan.split()) > 10:
             slogan = "Sync Your Strategy. Own Your Success."
             
        return jsonify({"slogan": slogan, "date": current_date})
    except Exception as e:
        return jsonify({"slogan": random.choice(offline_slogans), "error": str(e)})

# -----------------------
# CONTINUE ASSESSMENT
# -----------------------

@app.route("/continue-assessment")
def continue_assessment():
    subjects = Subject.query.all()
    assessments = AssessmentProgress.query.order_by(AssessmentProgress.timestamp.desc()).all()
    
    # Calculate progress for each assessment
    assessment_list = []
    for a in assessments:
        total_topics = len(a.topics) if a.topics else 0
        completed_topics = sum(1 for t in a.topics if t.get('completed')) if a.topics else 0
        progress = (completed_topics / total_topics * 100) if total_topics > 0 else 0
        
        sub = Subject.query.get(a.subject_id)
        assessment_list.append({
            "id": a.id,
            "subject": sub,
            "unit_number": a.unit_number,
            "topics": a.topics,
            "notes": a.notes,
            "progress": round(progress, 1)
        })
        
    return render_template("assessment.html", subjects=subjects, assessments=assessment_list)

@app.route("/add-assessment", methods=["POST"])
def add_assessment():
    sub_id = request.form.get("subject_id", type=int)
    unit_num = request.form.get("unit_number", type=int)
    topics_str = request.form.get("topics", "")
    
    # Parse topics from comma-separated string
    topic_list = [{"name": t.strip(), "completed": False} for t in topics_str.split(",") if t.strip()]
    
    new_assessment = AssessmentProgress(
        subject_id=sub_id,
        unit_number=unit_num,
        topics=topic_list,
        notes=""
    )
    db.session.add(new_assessment)
    db.session.commit()
    return redirect(url_for("continue_assessment"))

@app.route("/update-assessment/<int:assessment_id>", methods=["POST"])
def update_assessment(assessment_id):
    assessment = AssessmentProgress.query.get_or_404(assessment_id)
    
    # Update unit number if provided
    if "unit_number" in request.form:
        assessment.unit_number = request.form.get("unit_number", type=int)

    # Update notes
    if "notes" in request.form:
        assessment.notes = request.form.get("notes")
        
    # Update topic completion
    if assessment.topics:
        updated_topics = []
        for i, topic in enumerate(assessment.topics):
            topic_completed = request.form.get(f"topic_{i}") == "on"
            updated_topics.append({"name": topic["name"], "completed": topic_completed})
        assessment.topics = updated_topics
    
    db.session.commit()
    return redirect(url_for("continue_assessment"))

@app.route("/delete-assessment/<int:assessment_id>")
def delete_assessment(assessment_id):
    assessment = AssessmentProgress.query.get_or_404(assessment_id)
    db.session.delete(assessment)
    db.session.commit()
    return redirect(url_for("continue_assessment"))

if __name__=="__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)