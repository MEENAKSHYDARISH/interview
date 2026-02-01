from flask import Blueprint, request, jsonify

student_resume_bp = Blueprint('student_resume', __name__)

@student_resume_bp.route('/student/upload-resume', methods=['POST'])
def upload_resume():
    # Placeholder for resume upload logic
    return jsonify({"file_id": "mock_file_id_123"})
