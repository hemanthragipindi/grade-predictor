
import os
from app import app, db
from models import Subject, Component, Marks, CAMarks

with app.app_context():
    # Update MTH165
    mth165 = Subject.query.filter_by(subject_code="MTH165").first()
    if mth165:
        # Delete existing components and marks for MTH165
        Marks.query.filter_by(subject_id=mth165.id).delete()
        CAMarks.query.filter_by(subject_id=mth165.id).delete()
        Component.query.filter_by(subject_id=mth165.id).delete()
        
        # Add new components
        comps = [
            ("Objective Type Mid Term", 30, 20),
            ("Continuous Assessment", 100, 25),
            ("Attendance", 5, 5),
            ("Theory End Term", 40, 35),
            ("Objective Type End Term", 30, 15)
        ]
        
        comp_objs = []
        for c_name, c_max, c_weight in comps:
            comp = Component(
                subject_id=mth165.id,
                component_name=c_name,
                max_marks=c_max,
                weight=c_weight
            )
            db.session.add(comp)
            db.session.flush()
            comp_objs.append(comp)

        # Add Marks
        # Obj Mid: 17/30
        # CA: 62/100
        # Att: 5/5
        # Theory End: 33/40
        # Obj End: 29/30
        marks_data = {
            "Objective Type Mid Term": 17,
            "Continuous Assessment": 62,
            "Attendance": 5,
            "Theory End Term": 33,
            "Objective Type End Term": 29
        }
        
        for c in comp_objs:
            if c.component_name in marks_data:
                db.session.add(Marks(subject_id=mth165.id, component_id=c.id, marks_obtained=marks_data[c.component_name]))

        # Add CA Details
        db.session.add(CAMarks(subject_id=mth165.id, marks=62.0, max_marks=100.0))

        db.session.commit()
        print("MTH165 updated successfully.")
    else:
        print("MTH165 not found.")
