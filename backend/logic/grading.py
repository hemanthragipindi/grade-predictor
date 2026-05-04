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

# Rule 1: Fixed Weightage Rules
def get_fixed_weight(comp_name):
    rules = {
        'Attendance': 5,
        'Mid-Term': 20,
        'End-Term': 50,
        'CA': 25
    }
    return rules.get(comp_name, 0)

def is_practical(subject):
    code = (subject.subject_code or '').lower()
    name = (subject.subject_name or '').lower()
    # Identifying practical subjects like ECE279
    practical_codes = ['ece279', 'cse326', 'cse443']
    practical_keywords = ['lab', 'practical', 'workshop']
    return any(c in code for c in practical_codes) or any(k in name for k in practical_keywords)

def calc_ca_score(subject, ca_rows, comp_weight):
    code = (subject.subject_code or '').upper()
    
    # Rule 3: Special handling for INT306 and CSE101
    if code in ['INT306', 'CSE101']:
        # These subjects use a custom distribution across multiple CA components
        earned = sum(row.marks for row in ca_rows)
        possible = sum(row.max_marks for row in ca_rows)
        if possible == 0: return 0, 0, 100
        # Scale to the fixed 25% CA weight
        ca_contribution = (earned / possible) * get_fixed_weight('CA')
        return ca_contribution, earned, possible
    
    # Rule 3: Standard CA logic for all other subjects
    earned = sum(row.marks for row in ca_rows)
    possible = sum(row.max_marks for row in ca_rows)
    if possible == 0: return 0, 0, 100
    ca_contribution = (earned / possible) * get_fixed_weight('CA')
    return ca_contribution, earned, possible
