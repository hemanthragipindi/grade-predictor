
import os
from app import app, db
from models import Subject, Component, Marks, CAMarks

transcript_data = [
    {
        "code": "CSE111",
        "components": [
            ("Attendance", 5, 20, 5),
            ("Continuous Assessment", 100, 50, 86),
            ("Objective Type End Term", 60, 30, 46)
        ]
    },
    {
        "code": "CSE326",
        "components": [
            ("Attendance", 5, 5, 5),
            ("Continuous Assessment", 100, 45, 85),
            ("Objective Type End Term", 60, 50, 47)
        ]
    },
    {
        "code": "INT108",
        "components": [
            ("Attendance", 5, 5, 4),
            ("Continuous Assessment", 100, 50, 80),
            ("Practical End Term", 100, 45, 44)
        ]
    },
    {
        "code": "MEC136",
        "components": [
            ("Attendance", 5, 5, 5),
            ("Continuous Assessment", 100, 25, 84),
            ("Theory End Term", 70, 50, 55),
            ("Theory Mid Term", 40, 20, 35)
        ]
    },
    {
        "code": "MTH165",
        "components": [
            ("Attendance", 5, 5, 5),
            ("Continuous Assessment", 100, 25, 62),
            ("Objective Type End Term", 30, 15, 29),
            ("Objective Type Mid Term", 30, 20, 17),
            ("Theory End Term", 40, 35, 33)
        ]
    },
    {
        "code": "PHY110",
        "components": [
            ("Attendance", 5, 5, 4),
            ("Continuous Assessment", 100, 25, 64),
            ("Objective Type End Term", 60, 50, 25),
            ("Objective Type Mid Term", 30, 20, 12)
        ]
    }
]

with app.app_context():
    for sub_data in transcript_data:
        sub = Subject.query.filter_by(subject_code=sub_data["code"]).first()
        if not sub:
            continue
            
        Marks.query.filter_by(subject_id=sub.id).delete()
        CAMarks.query.filter_by(subject_id=sub.id).delete()
        Component.query.filter_by(subject_id=sub.id).delete()
        
        for c_name, c_max, c_weight, c_marks in sub_data["components"]:
            comp = Component(subject_id=sub.id, component_name=c_name, max_marks=c_max, weight=c_weight)
            db.session.add(comp)
            db.session.flush()
            
            if c_name == "Continuous Assessment":
                # Practical subjects check
                if sub.subject_code == "INT108":
                    for _ in range(4):
                        db.session.add(CAMarks(subject_id=sub.id, marks=float(c_marks), max_marks=float(c_max)))
                else:
                    db.session.add(CAMarks(subject_id=sub.id, marks=float(c_marks), max_marks=float(c_max)))
            else:
                db.session.add(Marks(subject_id=sub.id, component_id=comp.id, marks_obtained=c_marks))

    db.session.commit()
    print("Transcript synced exactly!")
