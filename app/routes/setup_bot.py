from flask import Blueprint, request, jsonify
import openai
import json
import os

setup_bot_bp = Blueprint('setup_bot', __name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "dummy-key")
openai.api_key = OPENAI_API_KEY

@setup_bot_bp.route('/student/setup-bot', methods=['POST'])
def setup_bot():
    # Auth Check: Use logic or header mock
    from flask_login import current_user
    if current_user.is_authenticated:
        if current_user.role != 'student':
             return jsonify({"detail": "Forbidden"}), 403
    else:
        # Fallback for dev/mock testing
        user_role = request.headers.get('X-Mock-Role', 'student')
        if user_role != 'student':
            return jsonify({"detail": "Forbidden"}), 403

    data = request.json
    text = data.get("text", "")
    
    system = """You are an assistant that maps a student's free-text request into a JSON with keys:
- job_role (string),
- interview_type (one of: Technical, HR, Behavioral, Stress, Aptitude, Custom),
- difficulty (Easy, Medium, Hard).
Return only a compact JSON object with those fields. If job role is unknown, set job_role to 'General'."""
    
    prompt = [
        {"role":"system", "content": system},
        {"role":"user", "content": f"User request: {text}\nReturn JSON only."}
    ]
    
    try:
        # Check if dummy key, return mock response
        if OPENAI_API_KEY == "dummy-key":
             return jsonify({
                "job_role": "Backend Developer",
                "interview_type": "Technical",
                "difficulty": "Medium",
                "mock": True
             })

        resp = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=prompt,
            temperature=0.0,
            max_tokens=200
        )
        content = resp.choices[0].message["content"].strip()
        try:
            parsed = json.loads(content)
        except Exception:
            parsed = {"job_role":"General","interview_type":"Technical","difficulty":"Medium"}
        return jsonify(parsed)
    except Exception as e:
        return jsonify({"job_role":"General","interview_type":"Technical","difficulty":"Medium", "error": str(e)})
