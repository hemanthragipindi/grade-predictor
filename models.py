from database import db

class Subject(db.Model):
    __tablename__ = "subjects"

    id = db.Column(db.Integer, primary_key=True)
    subject_code = db.Column(db.String(20))
    subject_name = db.Column(db.String(100))
    credits = db.Column(db.Integer)
    semester = db.Column(db.Integer, default=2)


class Component(db.Model):
    __tablename__ = "components"

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer)
    component_name = db.Column(db.String(100))
    max_marks = db.Column(db.Float)
    weight = db.Column(db.Float)


class Marks(db.Model):
    __tablename__ = "marks"

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer)
    component_id = db.Column(db.Integer)
    marks_obtained = db.Column(db.Float)


class CAMarks(db.Model):
    __tablename__ = "ca_marks"

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer)
    marks = db.Column(db.Float)
    max_marks = db.Column(db.Float)

class StudyLog(db.Model):
    __tablename__ = "study_logs"
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer)
    duration_hours = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=db.func.now())

class RecommendationFeedback(db.Model):
    __tablename__ = "feedbacks"
    id = db.Column(db.Integer, primary_key=True)
    recommendation_type = db.Column(db.String(50))
    was_helpful = db.Column(db.Boolean)
    score_improvement = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=db.func.now())

class LearningProfile(db.Model):
    __tablename__ = "learning_profiles"
    id = db.Column(db.Integer, primary_key=True)
    best_time_of_day = db.Column(db.String(20)) # morning, afternoon, night
    avg_focus_duration = db.Column(db.Float)
    subject_difficulties = db.Column(db.JSON) # Mapping subject_id -> difficulty_score

class PredictionAudit(db.Model):
    __tablename__ = "prediction_audits"
    id = db.Column(db.Integer, primary_key=True)
    predicted_gpa = db.Column(db.Float)
    actual_gpa = db.Column(db.Float)
    accuracy_percentage = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=db.func.now())

class SyllabusFile(db.Model):
    __tablename__ = "syllabus"
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), unique=True)
    file_path = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=db.func.now())

class AssessmentProgress(db.Model):
    __tablename__ = "assessment_progress"
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'))
    unit_number = db.Column(db.Integer)
    topics = db.Column(db.JSON) # List of {"name": str, "completed": bool}
    notes = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=db.func.now())
