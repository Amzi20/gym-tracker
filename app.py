from datetime import date, timedelta
from collections import defaultdict
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///gym.db"
db = SQLAlchemy(app)


class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    duration = db.Column(db.Integer, nullable=False)  # minutes
    entries = db.relationship(
        "ExerciseEntry", backref="workout", cascade="all, delete-orphan"
    )


class ExerciseEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(db.Integer, db.ForeignKey("workout.id"), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    sets = db.Column(db.Integer, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=False)  # kg


with app.app_context():
    db.create_all()  # creates gym.db the first time you run the app


@app.route("/")
def home():
    workouts = Workout.query.order_by(Workout.date.desc()).all()
    weeks = defaultdict(list)
    for w in workouts:
        week_start = w.date - timedelta(days=w.date.weekday())  # that week's Monday
        weeks[week_start].append(w)

    summary = []
    for week_start, items in weeks.items():  # newest week first
        summary.append(
            {
                "start": week_start,
                "workouts": items,
                "count": len(items),
                "minutes": sum(w.duration for w in items),
                "volume": sum(
                    e.sets * e.reps * e.weight for w in items for e in w.entries
                ),
            }
        )
    return render_template("history.html", weeks=summary)


@app.route("/delete/<int:workout_id>", methods=["POST"])
def delete_workout(workout_id):
    workout = db.get_or_404(Workout, workout_id)
    db.session.delete(workout)
    db.session.commit()
    return redirect(url_for("home"))

@app.route("/log", methods=["GET", "POST"])
def log_workout():
    if request.method == "POST":
        workout = Workout(
            date=date.fromisoformat(request.form["date"]),
            duration=int(request.form["duration"]),
        )
        names = request.form.getlist("name")
        sets = request.form.getlist("sets")
        reps = request.form.getlist("reps")
        weights = request.form.getlist("weight")
        for n, s, r, w in zip(names, sets, reps, weights):
            if n.strip() and s and r and w:  # skip empty rows
                workout.entries.append(
                    ExerciseEntry(
                        name=n.strip().title(),  # "bench press" becomes "Bench Press"
                        sets=int(s),
                        reps=int(r),
                        weight=float(w),
                    )
                )
        db.session.add(workout)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("log.html", today=date.today().isoformat())


@app.route("/progress")
def progress():
    names = [
        n for (n,) in db.session.query(ExerciseEntry.name)
        .distinct().order_by(ExerciseEntry.name)
    ]
    selected = request.args.get("exercise") or (names[0] if names else None)

    points = []
    if selected:
        rows = (
            db.session.query(Workout.date, db.func.max(ExerciseEntry.weight))
            .select_from(Workout)
            .join(ExerciseEntry)
            .filter(ExerciseEntry.name == selected)
            .group_by(Workout.date)
            .order_by(Workout.date)
            .all()
        )
        points = [{"date": d.isoformat(), "weight": w} for d, w in rows]

    return render_template(
        "progress.html", names=names, selected=selected, points=points
    )


if __name__ == "__main__":
    app.run(debug=True, port=5001)