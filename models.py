from database import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

class Subject(db.Model):
    __tablename__ = "subjects"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_code = db.Column(db.String(20))
    subject_name = db.Column(db.String(100))
    credits = db.Column(db.Integer)


class Component(db.Model):
    __tablename__ = "components"

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    component_name = db.Column(db.String(100))
    max_marks = db.Column(db.Float)
    weight = db.Column(db.Float)


class Marks(db.Model):
    __tablename__ = "marks"

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    component_id = db.Column(db.Integer, db.ForeignKey('components.id'), nullable=False)
    marks_obtained = db.Column(db.Float)


class CAMarks(db.Model):
    __tablename__ = "ca_marks"

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    marks = db.Column(db.Float)
    max_marks = db.Column(db.Float)