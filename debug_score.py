
from app import app, db, get_subject_score_and_grade
from models import Subject

with app.app_context():
    subjects = Subject.query.filter_by(semester=1).all()
    
    total_points = 0
    total_credits = 0

    print("--- REAL WORLD SEMESTER 1 SCORES ---")
    for sub in subjects:
        score, grade, gpa = get_subject_score_and_grade(sub.id)
        print(f"{sub.subject_code}: Score = {score}, Grade = {grade}, GPA = {gpa}")
        credits = sub.credits if sub.credits else 0
        total_points += gpa * credits
        total_credits += credits

    tgpa = round(total_points/total_credits, 2) if total_credits > 0 else 0
    print(f"\nFinal TGPA: {tgpa}")
