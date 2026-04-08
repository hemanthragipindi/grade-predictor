
import os
from app import app, db
from models import Subject, Component, Marks, CAMarks

with app.app_context():
    # Update PHY110
    phy110 = Subject.query.filter_by(subject_code="PHY110").first()
    if phy110:
        comps = Component.query.filter_by(subject_id=phy110.id).all()
        for comp in comps:
            if "Mid" in comp.component_name:
                comp.max_marks = 30
                print(f"Updated {comp.component_name} max_marks to 30")
            elif "End" in comp.component_name:
                comp.max_marks = 60
                print(f"Updated {comp.component_name} max_marks to 60")
        
        db.session.commit()
        print("PHY110 max marks updated successfully.")
    else:
        print("PHY110 not found.")
