from database import db
from flask_login import UserMixin
import datetime

class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    mobile = db.Column(db.String(15), unique=True, nullable=True)
    password = db.Column(db.String(200), nullable=True)
    profile_pic = db.Column(db.String(255), default='default_avatar.jpg')
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "mobile": self.mobile,
            "profile_pic": self.profile_pic,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Subject(db.Model):
    __tablename__ = "subjects"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    subject_code = db.Column(db.String(20))
    subject_name = db.Column(db.String(100))
    credits = db.Column(db.Integer)
    semester = db.Column(db.Integer, default=2)

    def to_dict(self):
        return {
            "id": self.id,
            "subject_code": self.subject_code,
            "subject_name": self.subject_name,
            "credits": self.credits,
            "semester": self.semester
        }

class Component(db.Model):
    __tablename__ = "components"
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer)
    component_name = db.Column(db.String(100))
    max_marks = db.Column(db.Float)
    weight = db.Column(db.Float)

    def to_dict(self):
        return {
            "id": self.id,
            "component_name": self.component_name,
            "max_marks": self.max_marks,
            "weight": self.weight
        }

class Marks(db.Model):
    __tablename__ = "marks"
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer)
    component_id = db.Column(db.Integer)
    marks_obtained = db.Column(db.Float)

    def to_dict(self):
        return {
            "id": self.id,
            "component_id": self.component_id,
            "marks_obtained": self.marks_obtained
        }

class CAMarks(db.Model):
    __tablename__ = "ca_marks"
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer)
    marks = db.Column(db.Float)
    max_marks = db.Column(db.Float)
    weight = db.Column(db.Float, default=0.0)

    def to_dict(self):
        return {
            "id": self.id,
            "marks": self.marks,
            "max_marks": self.max_marks,
            "weight": self.weight
        }

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

    def to_dict(self):
        return {
            "id": self.id,
            "file_name": self.file_name,
            "file_type": self.file_type,
            "file_url": self.file_url,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

class StudyLog(db.Model):
    __tablename__ = "study_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'))
    duration_hours = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "subject_id": self.subject_id,
            "duration_hours": self.duration_hours,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

class AssessmentProgress(db.Model):
    __tablename__ = "assessment_progress"
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'))
    unit_number = db.Column(db.Integer)
    topics = db.Column(db.JSON)
    notes = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "subject_id": self.subject_id,
            "unit_number": self.unit_number,
            "topics": self.topics,
            "notes": self.notes,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }
