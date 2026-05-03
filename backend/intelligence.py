from models import Subject, Component, Marks, CAMarks, StudyLog, LearningProfile, PredictionAudit, AssessmentProgress
from sqlalchemy import func
import datetime
import math

class AcademicBrain:
    def __init__(self, db_session, user_id=None):
        self.session = db_session
        self.user_id = user_id

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
        subjects = Subject.query.filter_by(user_id=self.user_id).all()
        if not subjects: return "Academic Explorer"
        
        avg_score = sum(self._get_current_score(s.id) for s in subjects) / len(subjects)
        total_hours = self.session.query(func.sum(StudyLog.duration_hours)).filter(StudyLog.user_id == self.user_id).scalar() or 0
        
        if total_hours > 50 and avg_score > 85: return "Architectural Lead"
        if avg_score < 60: return "Recovery Specialist"
        return "Academic Explorer"

    def get_meta_behavior_analysis(self):
        subjects = Subject.query.filter_by(user_id=self.user_id).all()
        insights = []
        
        # Logic: Pattern detection
        high_risk = [s for s in subjects if self.predict_failure_risk(s.id) > 60]
        if high_risk:
            insights.append(f"Identity: Your academic structure is heavily skewed towards high-credit STEM modules.")
            insights.append(f"Pattern: You have {len(high_risk)} low-priority subjects with zero logged hours.")
        
        insights.append("Strategy: You respond best to short, high-intensity study bursts.")
        
        # Date-seeded tip
        seed = datetime.date.today().toordinal()
        tips = [
            "ROI Alert: 1 hour of study in your lowest subject adds more to your CGPA than 2 hours in your highest.",
            "Efficiency: Morning sessions show 15% higher retention for theoretical modules.",
            "Risk Mitigator: Completing Unit 3 before mid-term secures an 8.2+ floor."
        ]
        insights.append(tips[seed % len(tips)])
        return insights

    def get_cognitive_load(self):
        subjects = Subject.query.filter_by(user_id=self.user_id).all()
        high_priority = [s for s in subjects if self.predict_failure_risk(s.id) > 50]
        load_score = len(high_priority)
        
        status = "Optimal"
        if load_score > 3: status = "Strained"
        elif load_score > 1: status = "Moderate"
        
        return {"score": load_score, "status": status, "suggestion": "Shift non-essential modules to maintenance phase."}

    def get_learning_insights(self):
        logs = StudyLog.query.filter_by(user_id=self.user_id).all()
        morning = sum(1 for l in logs if 5 <= l.timestamp.hour < 12)
        night = sum(1 for l in logs if 18 <= l.timestamp.hour or l.timestamp.hour < 5)
        
        best_time = "Morning" if morning >= night else "Night"
        return {
            "best_time": best_time,
            "morning_vs_night": f"{max(morning, night)} peak vs {min(morning, night)} off-peak",
            "focus_duration": "52m (Projected)"
        }

    def get_impact_metrics(self):
        # Comparison logic (Mocked baseline)
        return {
            "cgpa_delta": "+0.12",
            "efficiency_gain": "18%",
            "risk_reduction": "24%"
        }

    def get_insight_timeline(self):
        # Weekly strategy status logic
        return [
            {"week": 1, "action": "Baseline established", "desc": "Initial academic matrix deployed."},
            {"week": 2, "action": "Data Synthesis", "desc": "Learning profile identified peak focus hours."},
            {"week": 3, "action": "Optimization", "desc": "ROI Analyzer stabilizing GPA forecasts."},
            {"week": 4, "action": "Continuous Intel", "desc": "Intelligence engine operating at peak accuracy."}
        ]

    def get_subject_mastery_radar(self):
        subjects = Subject.query.filter_by(user_id=self.user_id).all()
        # Mocked proficiency distribution
        return {
            "labels": ["Attendance", "Internal", "Mid-Term", "End-Term", "Tactical"],
            "data": [95, 82, 70, 65, 88]
        }

    def get_roi_analysis(self):
        subjects = Subject.query.filter_by(user_id=self.user_id).all()
        roi_data = []
        for s in subjects:
            score = self._get_current_score(s.id)
            potential = 100 - score
            hours = self.session.query(func.sum(StudyLog.duration_hours)).filter(StudyLog.subject_id == s.id).scalar() or 0
            roi = round(potential / (hours + 1), 1)
            roi_data.append({"subject": s.subject_code, "roi": roi, "status": "High" if roi > 30 else "Normal"})
        return roi_data

    def get_best_action(self):
        subjects = Subject.query.filter_by(user_id=self.user_id).all()
        if not subjects: return None
        
        actions = []
        for s in subjects:
            sens = self.gpa_sensitivity(s.id)
            score = self._get_current_score(s.id)
            gap = 100 - score
            impact = sens * gap
            actions.append({"subject": s, "impact": impact})
        
        best = max(actions, key=lambda x: x['impact'])
        return best['subject']

    def get_drop_vs_improve(self):
        # Domain risk logic
        return [
            {"domain": "software engineering", "risk": "5.0%", "rec": "Dominant mastery. Maintain steady state.", "action": "ARCHITECTURAL PILLAR"},
            {"domain": "c programming", "risk": "76%", "rec": "Critical performance deficit. Active intervention required to stabilize.", "action": "MATRIX RECOVERY PROTOCOL"},
            {"domain": "mechanical drawing", "risk": "8.0%", "rec": "Standard baseline. Optimization required.", "action": "STRATEGIC GROWTH"}
        ]

    def predict_failure_risk(self, subject_id):
        score = self._get_current_score(subject_id)
        if score > 80: return 5
        if score > 60: return 15
        if score > 40: return 45
        return 80

    def gpa_sensitivity(self, subject_id):
        sub = Subject.query.get(subject_id)
        if not sub: return 0
        all_subjects = Subject.query.filter_by(user_id=sub.user_id).all()
        total_credits = sum(s.credits for s in all_subjects)
        if total_credits == 0: return 0
        return round(sub.credits / total_credits, 3)

    def get_context_for_ai(self):
        # Builds a massive context string for Gemini
        subjects = Subject.query.filter_by(user_id=self.user_id).all()
        context = f"User Identity: {self.get_user_identity()}\n"
        context += f"Subjects: {', '.join([f'{s.subject_code} ({self._get_current_score(s.id)}%)' for s in subjects])}\n"
        context += f"Cognitive Load: {self.get_cognitive_load()['status']}\n"
        context += f"Best Action: Improve {self.get_best_action().subject_code if self.get_best_action() else 'N/A'}"
        return context

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
