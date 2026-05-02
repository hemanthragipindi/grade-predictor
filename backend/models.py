from database import db
from flask_login import UserMixin
import datetime

class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    mobile = db.Column(db.String(15), unique=True)
    password = db.Column(db.String(200))
    profile_pic = db.Column(db.String(255), default='default_avatar.jpg')
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Subject(db.Model):
    __tablename__ = "subjects"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
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
    weight = db.Column(db.Float, default=0.0)

class CloudFile(db.Model):
    __tablename__ = "cloud_files"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    file_name = db.Column(db.String(255))
    file_type = db.Column(db.String(50))
    file_url = db.Column(db.String(500))
    public_id = db.Column(db.String(255))
    provider = db.Column(db.String(20)) # 'cloudinary' or 'firebase'
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class StudyLog(db.Model):
    __tablename__ = "study_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'))
    duration_hours = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class LearningProfile(db.Model):
    __tablename__ = "learning_profiles"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    peak_focus_hour = db.Column(db.Integer)
    preferred_session_length = db.Column(db.Integer)

class PredictionAudit(db.Model):
    __tablename__ = "prediction_audits"
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer)
    predicted_score = db.Column(db.Float)
    actual_score = db.Column(db.Float)
    accuracy_percentage = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class SyllabusFile(db.Model):
    __tablename__ = "syllabus"
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), unique=True)
    file_path = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class AssessmentProgress(db.Model):
    __tablename__ = "assessment_progress"
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'))
    unit_number = db.Column(db.Integer)
    topics = db.Column(db.JSON)
    notes = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
