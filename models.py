from database import db

class Subject(db.Model):
    __tablename__ = "subjects"

    id = db.Column(db.Integer, primary_key=True)
    subject_code = db.Column(db.String(20))
    subject_name = db.Column(db.String(100))
    credits = db.Column(db.Integer)


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