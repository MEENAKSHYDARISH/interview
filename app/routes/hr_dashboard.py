from flask import Blueprint, render_template, request, redirect, flash, url_for
from flask_login import login_required, current_user
from ..db import get_db
from ..models import Question, InterviewReport, User
from bson.objectid import ObjectId

hr_dashboard_bp = Blueprint('hr_dashboard', __name__)

@hr_dashboard_bp.route('/hr/dashboard')
@login_required
def dashboard():
    if current_user.role != 'hr':
        return redirect(url_for('hr_auth.login'))
        
    db = get_db()
    
    # Fetch Reports
    reports = InterviewReport.get_all(db)
    
    # Helper to get user names
    # Optimize in prod: use aggregation
    enriched_reports = []
    for r in reports:
        student = User.get_by_id(db, ObjectId(r['student_id']))
        r['student_name'] = student.name if student else "Unknown"
        r['id'] = str(r['_id'])
        enriched_reports.append(r)

    return render_template('hr_dashboard.html', reports=enriched_reports, user=current_user)

@hr_dashboard_bp.route('/hr/add-question', methods=['POST'])
@login_required
def add_question():
    if current_user.role != 'hr':
        return redirect(url_for('hr_auth.login'))

    role = request.form.get('role')
    q_type = request.form.get('type')
    content = request.form.get('content')
    
    if role and q_type and content:
        db = get_db()
        Question.create(db, role, q_type, content, current_user.id)
        flash("Question added successfully!", "success")
    else:
        flash("All fields are required.", "error")
        
    return redirect(url_for('hr_dashboard.dashboard'))

@hr_dashboard_bp.route('/hr/report/<report_id>')
@login_required
def view_report(report_id):
    if current_user.role != 'hr':
        return redirect(url_for('hr_auth.login'))
        
    db = get_db()
    report_data = InterviewReport.get_by_id(db, ObjectId(report_id))
    
    if not report_data:
        flash("Report not found")
        return redirect(url_for('hr_dashboard.dashboard'))
        
    student = User.get_by_id(db, ObjectId(report_data['student_id']))
    report_data['student_name'] = student.name if student else "Unknown"
    
    return render_template('hr_view_report.html', report=report_data)
