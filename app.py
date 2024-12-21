from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI', 'sqlite:///quiz.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'

db = SQLAlchemy(app)

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    answer1 = db.Column(db.String(255), nullable=False)
    answer2 = db.Column(db.String(255), nullable=False)
    answer3 = db.Column(db.String(255))
    answer4 = db.Column(db.String(255))
    correct_answer = db.Column(db.Integer, nullable=False)
    explanation = db.Column(db.String(255))

# Create the database tables
with app.app_context():
    db.create_all()

# Forms
class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()
        if existing_user_username:
            raise ValidationError('That username already exists. Please choose a different one.')

# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('admin'))
        flash('Invalid username or password')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route("/admin")
@login_required
def admin():
    questions = Question.query.all()
    return render_template("admin.html", questions=questions)

@app.route("/")
def index():
    questions = Question.query.all()
    total_questions = len(questions)
    return render_template("index.html", questions=questions, total_questions=total_questions)

@app.route("/get_question/<int:index>")
def get_question(index):
    questions = Question.query.all()
    if 0 <= index < len(questions):
        question_data = {
            "question": questions[index].question,
            "answers": [questions[index].answer1, questions[index].answer2, questions[index].answer3, questions[index].answer4],
            "correctAnswer": questions[index].correct_answer,
            "explanation": questions[index].explanation
        }
        return jsonify(question_data)
    return jsonify({"error": "Question not found"}), 404

@app.route("/check_answer", methods=["POST"])
def check_answer():
    data = request.get_json()
    question_index = data.get("questionIndex")
    selected_answer = data.get("selectedAnswer")
    questions = Question.query.all()

    if 0 <= question_index < len(questions):
        correct_answer = questions[question_index].correct_answer
        explanation = questions[question_index].explanation
        is_correct = selected_answer == correct_answer
        return jsonify({"isCorrect": is_correct, "explanation": explanation, "correctAnswer": correct_answer})
    return jsonify({"error": "Invalid question index"}), 400

@app.route("/admin/add", methods=["POST"])
@login_required
def add_question():
    if request.method == 'POST':
        question = request.form.get('question', '')
        answer1 = request.form.get('answer1', '')
        answer2 = request.form.get('answer2', '')
        answer3 = request.form.get('answer3', '')
        answer4 = request.form.get('answer4', '')
        correct_answer = int(request.form.get('correct_answer', 0))
        explanation = request.form.get('explanation', '')
        new_question = Question(question=question, answer1=answer1, answer2=answer2, answer3=answer3, answer4=answer4, correct_answer=correct_answer, explanation=explanation)
        db.session.add(new_question)
        db.session.commit()
        return redirect(url_for('admin'))
    return render_template('admin.html')

@app.route("/admin/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_question(id):
    question = Question.query.get_or_404(id)
    if request.method == 'POST':
        question.question = request.form.get('question', '')
        question.answer1 = request.form.get('answer1', '')
        question.answer2 = request.form.get('answer2', '')
        question.answer3 = request.form.get('answer3', '')
        question.answer4 = request.form.get('answer4', '')
        question.correct_answer = int(request.form.get('correct_answer', 0))
        question.explanation = request.form.get('explanation', '')
        db.session.commit()
        return redirect(url_for('admin'))
    return render_template('edit.html', question=question)

@app.route("/admin/delete/<int:id>")
@login_required
def delete_question(id):
    question = Question.query.get_or_404(id)
    db.session.delete(question)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route("/result")
def result():
    score = request.args.get("score", 0, type=int)
    total_questions = Question.query.count()  # Get total questions directly from the database
    correct_answers = score
    incorrect_answers = total_questions - correct_answers
    percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0

    feedback = ""
    if percentage >= 90:
        feedback = "Excellent work!"
    elif percentage >= 75:
        feedback = "Great job!"
    elif percentage >= 50:
        feedback = "Good effort! Keep practicing."
    else:
        feedback = "Don't give up! Try again."

    return render_template(
        "result.html",
        total_questions=total_questions,
        correct_answers=correct_answers,
        incorrect_answers=incorrect_answers,
        percentage=round(percentage, 2),
        feedback=feedback
    )

if __name__ == "__main__":
    app.run(debug=True)
