from flask import Blueprint, request, jsonify
import os
import io
from pypdf import PdfReader

student_resume_bp = Blueprint('student_resume', __name__)

@student_resume_bp.route('/api/resume/upload', methods=['POST'])
def upload_resume():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    try:
        text = ""
        filename = file.filename.lower()
        
        if filename.endswith('.pdf'):
            # Read PDF
            pdf_stream = io.BytesIO(file.read())
            reader = PdfReader(pdf_stream)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        elif filename.endswith('.txt'):
            # Read TXT
            text = file.read().decode('utf-8')
        else:
            return jsonify({"error": "Unsupported file format. Please upload PDF or TXT."}), 400
            
        return jsonify({"status": "success", "text": text.strip()})
        
    except Exception as e:
        print(f"Resume Parse Error: {e}")
        return jsonify({"error": "Failed to parse file"}), 500
