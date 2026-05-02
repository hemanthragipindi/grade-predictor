from models import Subject, Component, Marks, CAMarks, StudyLog, LearningProfile, PredictionAudit
from sqlalchemy import func
import datetime
import math

class AcademicBrain:
    def __init__(self, db_session):
        self.session = db_session

    def analyze_gpa_tier(self, cgpa):
        if cgpa >= 9.0:
            return {
                "tier": "Architectural Elite",
                "strategy": "Maintenance & Refinement",
                "focus": "Optimization of high-yield assets. Secure your lead.",
                "color": "#10b981",
                "message": "System stable. Focus on perfection vectors."
            }
        elif cgpa >= 7.5:
            return {
                "tier": "Core Strategist",
                "strategy": "Structural Expansion",
                "focus": "Shift focus to high-sensitivity subjects to break 9.0 threshold.",
                "color": "#3b82f6",
                "message": "Optimization required in secondary modules."
            }
        else:
            return {
                "tier": "Matrix Recovery",
                "strategy": "System Stabilization",
                "focus": "Priority focus on subjects below 40% to save CGPA architecture.",
                "color": "#f43f5e",
                "message": "Critical stabilization protocol active."
            }

    def get_user_identity(self):
        subjects = Subject.query.all()
        # Filter subjects by user_id if needed, but the session filters it usually
        avg_score = sum(self._get_current_score(s.id) for s in subjects) / (len(subjects) or 1)
        return "Academic Explorer"

    def get_meta_behavior_analysis(self):
        subjects = Subject.query.all()
        insights = ["Initial Scan: Awaiting focus-burst intensity data."]
        import random
        seed = datetime.date.today().toordinal()
        random.seed(seed)
        daily_tips = ["Daily Strategy: Prioritize subjects with Credits > 3."]
        insights.append(random.choice(daily_tips))
        return insights

    def get_cognitive_load(self):
        subjects = Subject.query.all()
        high_priority = [s for s in subjects if self.predict_failure_risk(s.id) > 60]
        load_score = len(high_priority)
        status = "Optimal" if load_score <= 2 else "High"
        return {"score": load_score, "status": status, "suggestion": ""}

    def get_learning_insights(self):
        return {"best_time": "Morning", "morning_vs_night": "Standard optimization", "focus_duration": "45m"}

    def get_ai_advice(self, message, history):
        # Professional fallback logic for academic guidance
        msg = message.lower()
        if "grade" in msg or "marks" in msg:
            return "To optimize your grades, focus on subjects with high GPA sensitivity and ensure your Continuous Assessment (CA) scores stay above 75%."
        if "upload" in msg or "file" in msg:
            return "You can secure academic artifacts like PDFs and images in your Cloud Vault. Images are optimized via Cloudinary automatically."
        return "I am Nexora. I am here to help you project your academic outcomes and optimize your study matrix. How can I assist with your course strategy?"

    def predict_failure_risk(self, subject_id):
        score = self._get_current_score(subject_id)
        if score >= 60: return 5
        return 50

    def gpa_sensitivity(self, subject_id):
        sub = Subject.query.get(subject_id)
        total_credits = sum(s.credits for s in Subject.query.all())
        if total_credits == 0: return 0
        return round((sub.credits / total_credits) * 0.1, 3)

    def _get_current_score(self, subject_id):
        from logic.grading import get_grade, is_practical, calc_ca_score
        sub = Subject.query.get(subject_id)
        components = Component.query.filter_by(subject_id=subject_id).all()
        score = 0
        for comp in components:
            if comp.component_name != "Continuous Assessment":
                mark = Marks.query.filter_by(subject_id=subject_id, component_id=comp.id).first()
                if mark and comp.max_marks > 0:
                    score += (mark.marks_obtained/comp.max_marks)*comp.weight
            else:
                ca_rows = CAMarks.query.filter_by(subject_id=subject_id).all()
                if ca_rows:
                    ca_score_contrib, _, _ = calc_ca_score(sub, ca_rows, comp.weight)
                    score += ca_score_contrib
        return round(score, 2)
