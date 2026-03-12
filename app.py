from flask import Flask, render_template, request, redirect, url_for
from config import Config
from database import db
from models import Subject, Component, Marks, CAMarks

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)


# -----------------------
# GRADE SYSTEM
# -----------------------

def get_grade(score):

    if score >= 90:
        return "O",10
    elif score >= 80:
        return "A+",9
    elif score >= 70:
        return "A",8
    elif score >= 60:
        return "B+",7
    elif score >= 50:
        return "B",6
    else:
        return "F",0


# -----------------------
# DASHBOARD
# -----------------------

@app.route("/")
def dashboard():

    subjects = Subject.query.all()

    results = []

    total_points = 0
    total_credits = 0

    for sub in subjects:

        components = Component.query.filter_by(subject_id=sub.id).all()

        score = 0

        for comp in components:

            mark = Marks.query.filter_by(
                subject_id=sub.id,
                component_id=comp.id
            ).first()

            if mark:
                score += (mark.marks_obtained/comp.max_marks)*comp.weight

        ca_rows = CAMarks.query.filter_by(subject_id=sub.id).all()

        ca_total = sum(c.marks for c in ca_rows)
        ca_max = sum(c.max_marks for c in ca_rows)

        for comp in components:
            if comp.component_name=="Continuous Assessment" and ca_max>0:
                score += (ca_total/ca_max)*comp.weight

        score = round(score,2)

        grade,gpa = get_grade(score)

        credits = sub.credits if sub.credits else 0

        total_points += gpa*credits
        total_credits += credits

        results.append({
            "subject":sub,
            "score":score,
            "grade":grade,
            "gpa":gpa
        })

    cgpa = 0

    if total_credits>0:
        cgpa = round(total_points/total_credits,2)

    return render_template(
        "dashboard.html",
        results=results,
        cgpa=cgpa
    )


# -----------------------
# SUBJECT PAGE
# -----------------------

@app.route("/subject/<int:subject_id>",methods=["GET","POST"])
def subject_page(subject_id):

    subject = Subject.query.get(subject_id)

    components = Component.query.filter_by(subject_id=subject_id).all()

    edit_mode = request.args.get("edit")

    # -----------------------
    # SAVE DATA
    # -----------------------

    if request.method=="POST":

        for comp in components:

            if comp.component_name!="Continuous Assessment":

                marks=request.form.get(f"marks_{comp.id}")

                if marks:

                    row = Marks.query.filter_by(
                        subject_id=subject_id,
                        component_id=comp.id
                    ).first()

                    if row:
                        row.marks_obtained=float(marks)
                    else:
                        row=Marks(
                            subject_id=subject_id,
                            component_id=comp.id,
                            marks_obtained=float(marks)
                        )
                        db.session.add(row)

        # SAVE CA MARKS

        CAMarks.query.filter_by(subject_id=subject_id).delete()

        ca_marks=request.form.getlist("ca_marks[]")
        ca_max=request.form.getlist("ca_max[]")

        for m,mx in zip(ca_marks,ca_max):

            if m and mx:

                row=CAMarks(
                    subject_id=subject_id,
                    marks=float(m),
                    max_marks=float(mx)
                )

                db.session.add(row)

        db.session.commit()

        return redirect(url_for("subject_page",subject_id=subject_id) + "#top")


    # -----------------------
    # LOAD COMPONENT MARKS
    # -----------------------

    entered_marks={}

    for comp in components:

        row=Marks.query.filter_by(
            subject_id=subject_id,
            component_id=comp.id
        ).first()

        if row:
            entered_marks[comp.id]=row.marks_obtained


    # -----------------------
    # LOAD CA MARKS
    # -----------------------

    ca_rows=CAMarks.query.filter_by(subject_id=subject_id).all()

    ca_data=[]

    for row in ca_rows:

        ca_data.append({
            "marks":row.marks,
            "max":row.max_marks
        })


    # -----------------------
    # SCORE CALCULATION
    # -----------------------

    score = 0

    for comp in components:

        mark = Marks.query.filter_by(
            subject_id=subject_id,
            component_id=comp.id
        ).first()

        if mark:
            score += (mark.marks_obtained/comp.max_marks)*comp.weight

    ca_rows = CAMarks.query.filter_by(subject_id=subject_id).all()

    ca_total = sum(c.marks for c in ca_rows)
    ca_max = sum(c.max_marks for c in ca_rows)

    for comp in components:
        if comp.component_name=="Continuous Assessment" and ca_max>0:
            score += (ca_total/ca_max)*comp.weight

    score = round(score,2)

    grade,gpa = get_grade(score)


    # -----------------------
    # GRADE PREDICTION
    # -----------------------

    prediction = []

    grade_targets = {
        "O":90,
        "A+":80,
        "A":70,
        "B+":60,
        "B":50
    }

    for g,target in grade_targets.items():

        if score < target:

            need = round(target-score,2)

            prediction.append(
                f"{need} more marks needed to reach grade {g}"
            )

    return render_template(
        "subject.html",
        subject=subject,
        components=components,
        entered_marks=entered_marks,
        ca_data=ca_data,
        ca_total=ca_total,
        ca_max=ca_max,
        score=score,
        grade=grade,
        prediction=prediction,
        edit_mode=edit_mode
    )


if __name__=="__main__":
    app.run(debug=True)