from flask import Flask, render_template, send_from_directory, session
import os

app = Flask(__name__, template_folder='templates', static_folder='static')

# Configuration
app.config['SECRET_KEY'] = 'dev-secret'
app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/ai_interviewer')

# Routes / Blueprints
# Routes / Blueprints
from .routes.setup_bot import setup_bot_bp
from .routes.hr_roles import hr_roles_bp
from .routes.student_resume import student_resume_bp
from .routes.auth import auth_bp
from .routes.interview_api import interview_api_bp
from flask_login import LoginManager, login_required, current_user
from .models import User
from .db import get_db

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    return User.get_by_id(db, user_id)

app.register_blueprint(setup_bot_bp)
app.register_blueprint(hr_roles_bp)
app.register_blueprint(student_resume_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(interview_api_bp)

# Frontend Routes (Pages)
@app.route('/')
def landing():
    return render_template('landing.html', user=current_user)

@app.route('/student/select')
@login_required
def student_select():
    return render_template('student_select.html', user=current_user)

@app.route('/interview')
@login_required
def interview_page():
    return render_template('interview.html', user=current_user)

@app.route('/report')
@login_required
def report_page():
    report_data = session.get('report_data', {})
    return render_template('report.html', user=current_user, report=report_data)

# Run
if __name__ == '__main__':
    app.run(debug=True, port=5000)
