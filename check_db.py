
import os
from app import app, db, is_practical
from models import Subject, Component, Marks, CAMarks

with app.app_context():
    subjects = Subject.query.all()
    print(f"Total subjects: {len(subjects)}")
    sem1 = [s for s in subjects if s.semester == 1]
    sem2 = [s for s in subjects if s.semester == 2]
    print(f"Semester 1 subjects: {len(sem1)}")
    print(f"Semester 2 subjects: {len(sem2)}")
    
    print("\n--- INT108 Verification ---")
    int108 = Subject.query.filter_by(subject_code='INT108').first()
    if int108:
        print(f"INT108 found. Semester: {int108.semester}")
        print(f"is_practical('INT108'): {is_practical(int108)}")
        comps = Component.query.filter_by(subject_id=int108.id).all()
        for c in comps:
            print(f"  - {c.component_name}: Weight {c.weight}")
    else:
        print("INT108 NOT FOUND")
