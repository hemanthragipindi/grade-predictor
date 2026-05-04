import math
from models import Subject, Component, Marks, CAMarks
from logic.grading import get_grade, calc_ca_score, get_fixed_weight

def get_subject_score_and_grade(subject_id):
    sub = Subject.query.get(subject_id)
    if not sub: return 0, "F", 0
    
    components = Component.query.filter_by(subject_id=subject_id).all()
    score = 0
    for comp in components:
        # Rule 1: Enforce Fixed Weightage Rules
        comp_weight = get_fixed_weight(comp.component_name)
        
        if comp.component_name != "Continuous Assessment":
            m = Marks.query.filter_by(subject_id=subject_id, component_id=comp.id).first()
            if m and comp.max_marks > 0:
                score += (m.marks_obtained / comp.max_marks) * comp_weight
        else:
            ca_rows = CAMarks.query.filter_by(subject_id=subject_id).all()
            if ca_rows:
                ca_score_contrib, _, _ = calc_ca_score(sub, ca_rows, comp_weight)
                score += ca_score_contrib

    score = round(score, 2)
    grade, gpa = get_grade(score, sub.subject_code)
    return score, grade, gpa
