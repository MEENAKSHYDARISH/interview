from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from ..db import get_db
from ..models import User
import werkzeug.security as security
from werkzeug.security import generate_password_hash

hr_auth_bp = Blueprint('hr_auth', __name__)

@hr_auth_bp.route('/hr/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        db = get_db()
        if User.get_by_email(db, email):
            flash('Email already registered')
        else:
            hashed_pw = generate_password_hash(password)
            db.users.insert_one({
                "name": name,
                "email": email,
                "password": hashed_pw,
                "role": "hr"
            })
            flash('Registration successful! Please login.')
            return redirect(url_for('hr_auth.login'))
            
    return render_template('hr_register.html')

@hr_auth_bp.route('/hr/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        db = get_db()
        user = User.get_by_email(db, email)
        
        # Check if user exists, password matches, AND is HR role
        if user and security.check_password_hash(user.password_hash, password):
            if user.role != 'hr':
                flash('Access Denied: You are not an HR admin.')
                return redirect(url_for('hr_auth.login'))
            
            login_user(user)
            return redirect(url_for('hr_dashboard.dashboard'))
        else:
            flash('Invalid Email or Password')
            
    return render_template('hr_login.html')

@hr_auth_bp.route('/hr/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('hr_auth.login'))
