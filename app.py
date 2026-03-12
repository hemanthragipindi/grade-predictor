import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from database import db
from models import Subject, Component, Marks, CAMarks, User

app = Flask(__name__)
app.config.from_object(Config)

# Required for session management / flash messages
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-super-secret-key')

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# -----------------------
# AUTHENTICATION
# -----------------------

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
        
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = User.query.filter_by(username=username).first()
        if user:
            flash("Username already exists", "error")
            return redirect(url_for("signup"))
            
        new_user = User(
            username=username,
            password_hash=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()
        
        # Optionally create some default subjects for new users here
        
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))
        
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
        
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid username or password", "error")
            return redirect(url_for("login"))
            
        login_user(user)
        return redirect(url_for("dashboard"))
        
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


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
@login_required
def dashboard():

    subjects = Subject.query.filter_by(user_id=current_user.id).all()

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
# ADD SUBJECT
# -----------------------
@app.route("/add_subject", methods=["POST"])
@login_required
def add_subject():
    subject_code = request.form.get("subject_code")
    subject_name = request.form.get("subject_name")
    credits = request.form.get("credits")

    if subject_name and credits:
        new_sub = Subject(
            user_id=current_user.id,
            subject_code=subject_code,
            subject_name=subject_name,
            credits=int(credits)
        )
        db.session.add(new_sub)
        db.session.commit()
        
        # Add a default Continuous Assessment component automatically
        ca_comp = Component(
            subject_id=new_sub.id,
            component_name="Continuous Assessment",
            max_marks=100,
            weight=40
        )
        db.session.add(ca_comp)
        db.session.commit()
        flash("Subject added successfully!", "success")
        
    return redirect(url_for("dashboard"))


# -----------------------
# SUBJECT PAGE
# -----------------------

@app.route("/subject/<int:subject_id>",methods=["GET","POST"])
@login_required
def subject_page(subject_id):

    subject = Subject.query.filter_by(id=subject_id, user_id=current_user.id).first()
    if not subject:
        flash("Subject not found or unauthorized.", "error")
        return redirect(url_for("dashboard"))

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