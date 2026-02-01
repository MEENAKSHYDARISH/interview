from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from ..db import get_db
from ..models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('student_select'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        db = get_db()
        user = User.get_by_email(db, email)
        
        # Check password (assuming stored hash or plain for dev if not set)
        if user and user.password_hash and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('student_select'))
        else:
            flash('Invalid email or password', 'error')
            
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('student_select'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        db = get_db()
        if User.get_by_email(db, email):
            flash('Email already registered', 'error')
        else:
            hashed_pw = generate_password_hash(password)
            db.users.insert_one({
                "name": name,
                "email": email,
                "password": hashed_pw,
                "role": "student"
            })
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
            
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('landing'))
