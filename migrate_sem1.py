
from app import app, db
from models import Subject, Component, Marks, CAMarks
from sqlalchemy import text

def migrate():
    with app.app_context():
        # 1. Add semester column if it doesn't exist (PostgreSQL syntax)
        try:
            db.session.execute(text("ALTER TABLE subjects ADD COLUMN semester INTEGER DEFAULT 2"))
            db.session.commit()
            print("Added semester column.")
        except Exception as e:
            db.session.rollback()
            print(f"Column might already exist: {e}")

        # 2. Update existing subjects to semester 2
        Subject.query.update({Subject.semester: 2})
        db.session.commit()
        print("Updated existing subjects to Semester 2.")

        # 3. Add Semester 1 Subjects
        sem1_subjects = [
            {"code": "CSE111", "name": "Orientation to Computing I", "credits": 2, "semester": 1},
            {"code": "CSE326", "name": "Internet Programming Laboratory", "credits": 2, "semester": 1},
            {"code": "INT108", "name": "Python Programming", "credits": 4, "semester": 1},
            {"code": "MEC136", "name": "Engineering Drawing with AutoCAD", "credits": 4, "semester": 1},
            {"code": "MTH165", "name": "Mathematics for Engineers", "credits": 4, "semester": 1},
            {"code": "PHY110", "name": "Engineering Physics", "credits": 3, "semester": 1},
        ]

        for s_data in sem1_subjects:
            if not Subject.query.filter_by(subject_code=s_data["code"]).first():
                sub = Subject(
                    subject_code=s_data["code"],
                    subject_name=s_data["name"],
                    credits=s_data["credits"],
                    semester=s_data["semester"]
                )
                db.session.add(sub)
                db.session.flush()

                # Add Components
                if s_data["code"] == "INT108":
                    comps = [
                        ("Continuous Assessment", 100, 50),
                        ("Attendance", 5, 5),
                        ("Practical End Term", 100, 45)
                    ]
                elif s_data["code"] == "CSE326":
                    comps = [
                        ("Continuous Assessment", 100, 45),
                        ("Attendance", 5, 5),
                        ("Objective Type End Term", 60, 50)
                    ]
                elif s_data["code"] == "CSE111":
                    comps = [
                        ("Continuous Assessment", 100, 50),
                        ("Attendance", 5, 20),
                        ("Objective Type End Term", 60, 30)
                    ]
                elif s_data["code"] == "MEC136":
                    comps = [
                        ("Theory Mid Term", 40, 20),
                        ("Continuous Assessment", 100, 25),
                        ("Attendance", 5, 5),
                        ("Theory End Term", 70, 50)
                    ]
                else: # MTH165, PHY110
                    comps = [
                        ("Theory Mid Term", 40, 20),
                        ("Continuous Assessment", 100, 25),
                        ("Attendance", 5, 5),
                        ("Theory End Term", 70, 50)
                    ]

                comp_objs = []
                for c_name, c_max, c_weight in comps:
                    comp = Component(
                        subject_id=sub.id,
                        component_name=c_name,
                        max_marks=c_max,
                        weight=c_weight
                    )
                    db.session.add(comp)
                    db.session.flush()
                    comp_objs.append(comp)

                # Add Sample Marks from screenshots
                if s_data["code"] == "INT108":
                    # CA: 80/100, Att: 4/5, End: 44/100
                    for c in comp_objs:
                        if "Continuous" in c.component_name: m = 80
                        elif "Attendance" in c.component_name: m = 4
                        else: m = 44 # Practical End Term
                        db.session.add(Marks(subject_id=sub.id, component_id=c.id, marks_obtained=m))
                    # Add CA details for INT108 (it's practical)
                    # 80/100 -> split as 80/100 each for 4 rows to get 40/50
                    for _ in range(4):
                        db.session.add(CAMarks(subject_id=sub.id, marks=80.0, max_marks=100.0))

                elif s_data["code"] == "CSE326":
                    # CA: 85/100, Att: 5/5, End: 47/60
                    for c in comp_objs:
                        if "Continuous" in c.component_name: m = 85
                        elif "Attendance" in c.component_name: m = 5
                        else: m = 47
                        db.session.add(Marks(subject_id=sub.id, component_id=c.id, marks_obtained=m))
                    for _ in range(4): # CA Details
                        db.session.add(CAMarks(subject_id=sub.id, marks=85.0, max_marks=100.0))

                elif s_data["code"] == "CSE111":
                    # CA: 86/100, Att: 5/5, End: 46/60
                    for c in comp_objs:
                        if "Continuous" in c.component_name: m = 86
                        elif "Attendance" in c.component_name: m = 5
                        else: m = 46
                        db.session.add(Marks(subject_id=sub.id, component_id=c.id, marks_obtained=m))
                    for _ in range(4): # CA Details
                        db.session.add(CAMarks(subject_id=sub.id, marks=86.0, max_marks=100.0))

                elif s_data["code"] == "MEC136":
                    # Mid: 35/40, CA: 84/100, Att: 5/5, End: 55/70
                    for c in comp_objs:
                        if "Mid" in c.component_name: m = 35
                        elif "Continuous" in c.component_name: m = 84
                        elif "Attendance" in c.component_name: m = 5
                        else: m = 55
                        db.session.add(Marks(subject_id=sub.id, component_id=c.id, marks_obtained=m))
                    # MEC136 is NOT practical in my logic yet, so CA total is sum. 
                    # If I add 1 row 84/100 it works.
                    db.session.add(CAMarks(subject_id=sub.id, marks=84.0, max_marks=100.0))

        db.session.commit()
        print("Semester 1 subjects added successfully.")

if __name__ == "__main__":
    migrate()
