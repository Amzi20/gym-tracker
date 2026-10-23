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
    return "Gym tracker is running!"


if __name__ == "__main__":
    app.run(debug=True, port=5001)