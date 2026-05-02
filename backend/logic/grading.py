import math

def get_grade(score, subject_code=None):
    if subject_code == "CSE326":
        if score >= 84: return "O", 10.0
        elif score >= 75: return "A+", 9.0
        elif score >= 65: return "A", 8.0
        elif score >= 55: return "B+", 7.0
        elif score >= 45: return "B", 6.0
        elif score >= 40: return "C", 5.0
        else: return "F", 0.0

    if score >= 90: return "O", 10.0
    elif score >= 80: return "A+", 9.0
    elif score >= 70: return "A", 8.0
    elif score >= 60: return "B+", 7.0
    elif score >= 50: return "B", 6.0
    elif score >= 40: return "C", 5.0
    else: return "F", 0.0

def is_practical(subject):
    s = f"{subject.subject_code or ''} {subject.subject_name or ''}".lower()
    practical_codes = ['cse101', 'cse121', 'ece279', 'int306']
    practical_keywords = ['laboratory', 'practical', 'lab']
    return any(code in s for code in practical_codes) or any(kw in s for kw in practical_keywords)

def calc_ca_score(subject, ca_rows, comp_weight):
    if is_practical(subject):
        w0 = ca_rows[0].weight if len(ca_rows)>0 and ca_rows[0].weight > 0 else 20
        w1 = ca_rows[1].weight if len(ca_rows)>1 and ca_rows[1].weight > 0 else 15
        w2 = ca_rows[2].weight if len(ca_rows)>2 and ca_rows[2].weight > 0 else 15
        w3 = ca_rows[3].weight if len(ca_rows)>3 and ca_rows[3].weight > 0 else 15
        
        m0 = (ca_rows[0].marks/ca_rows[0].max_marks)*w0 if len(ca_rows)>0 and ca_rows[0].max_marks>0 else 0
        m1 = (ca_rows[1].marks/ca_rows[1].max_marks)*w1 if len(ca_rows)>1 and ca_rows[1].max_marks>0 else 0
        m2 = (ca_rows[2].marks/ca_rows[2].max_marks)*w2 if len(ca_rows)>2 and ca_rows[2].max_marks>0 else 0
        m3 = (ca_rows[3].marks/ca_rows[3].max_marks)*w3 if len(ca_rows)>3 and ca_rows[3].max_marks>0 else 0
        
        total_w = w0+w1+w2+w3
        if total_w == 0: return 0, 0, 0
        ca_score = (m0+m1+m2+m3)/total_w * comp_weight
        return ca_score, (m0+m1+m2+m3), total_w
    else:
        ca_sum = sum(row.marks for row in ca_rows)
        ca_max = sum(row.max_marks for row in ca_rows)
        ca_score = (ca_sum/ca_max)*comp_weight if ca_max > 0 else 0
        return ca_score, ca_sum, ca_max
