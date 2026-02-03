from flask import Blueprint, request, jsonify, session
import google.generativeai as genai
import os
import json

interview_api_bp = Blueprint('interview_api', __name__)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "dummy-key")
if GOOGLE_API_KEY != "dummy-key":
    genai.configure(api_key=GOOGLE_API_KEY)

SYSTEM_PROMPT_TEMPLATE = """You are a professional AI Interviewer for a {role} position.
Interview Type: {interview_type}
Current Interface Difficulty: {difficulty}

Your goal is to conduct a structured interview based STRONGLY on the candidate's resume and responses, while adapting to the interview type.

Resume Context:
{resume_text}

Rules:
1. Start by asking about a specific project or skill mentioned in the resume.
2. Ask one clear question at a time.
3. If the user's answer is too brief or off-topic, politely probe further.
4. If the answer is good, acknowledge it briefly and move to the next relevant topic from the resume or role requirements.
5. LISTEN to the user's previous answer. If they mentioned something interesting or unclear, ask a follow-up question about it before moving to a new topic.
6. For 'Technical' interviews, focus on technical depth, system design, and coding concepts.
7. For 'Behavioral' interviews, focus on soft skills, teamwork, and conflict resolution (STAR method).
8. Keep your responses concise (suitable for Text-to-Speech). Max 2-3 sentences for feedback, then the question.
9. The output must be JSON with the following structure:
{{
    "feedback": "Brief feedback on the previous answer (if any).",
    "question": "The next interview question."
}}
"""

def get_gemini_model():
    return genai.GenerativeModel('gemini-flash-latest')

@interview_api_bp.route('/api/interview/start', methods=['POST'])
def start_interview():
    data = request.json
    role = data.get('role', 'Candidate')
    interview_type = data.get('type', 'Technical')
    resume_text = data.get('resume_text', 'No resume provided.')
    difficulty = data.get('difficulty', 'Medium')

    full_system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        role=role,
        interview_type=interview_type,
        difficulty=difficulty,
        resume_text=resume_text
    )

    # Initialize chat history with system prompt (Gemini often works better if system prompt is separate or first message)
    # For simplicity, we'll keep the structure but adapt how we call Gemini.
    session['interview_history'] = [
        {"role": "user", "parts": [full_system_prompt + "\n\nStart the interview. Introduce yourself briefly as the AI Interviewer and ask the first question (e.g., 'Tell me about yourself')."]}
    ]
    
    try:
        response_data = _get_gemini_response(session['interview_history'])
        # Add assistant response to history
        session['interview_history'].append({"role": "model", "parts": [json.dumps(response_data)]})
        return jsonify(response_data)
    except Exception as e:
        return jsonify({"error": str(e), "question": "Hello. I'm ready to interview you. Could you introduce yourself?", "feedback": ""})

@interview_api_bp.route('/api/interview/chat', methods=['POST'])
def chat_interview():
    data = request.json
    user_answer = data.get('answer', '')

    if 'interview_history' not in session:
        return jsonify({"error": "Session expired", "question": "Please restart the interview.", "feedback": ""}), 400

    # Append user answer
    session['interview_history'].append({"role": "user", "parts": [user_answer]})

    try:
        response_data = _get_gemini_response(session['interview_history'])
        session['interview_history'].append({"role": "model", "parts": [json.dumps(response_data)]})
        return jsonify(response_data)
    except Exception as e:
        # Fallback mechanism if JSON parsing fails or API errors
        return jsonify({
            "feedback": "I didn't quite catch that.",
            "question": "Could you elaborate further on your previous experience?"
        })

@interview_api_bp.route('/api/interview/end', methods=['POST'])
def end_interview():
    if 'interview_history' not in session:
        return jsonify({"error": "No active session found"}), 400

    history = session['interview_history']
    
    # Prompt for report generation
    report_prompt = """
    The interview is over. Please analyze the entire conversation above.
    Provide a detailed performance report in JSON format with:
    - score (integer 0-100)
    - summary (string, 2-3 sentences)
    - strengths (list of strings)
    - weaknesses (list of strings)
    - suggestion (string, improvement advice)
    """
    # Create a separate history for report generation to append the instruction
    report_history = history.copy()
    report_history.append({"role": "user", "parts": [report_prompt]})

    try:
        if GOOGLE_API_KEY == "dummy-key":
             report_data = {
                 "score": 85,
                 "summary": "Good technical understanding but needs more confidence.",
                 "strengths": ["Python Knowledge", "Problem Solving"],
                 "weaknesses": ["Communication Speed", "System Design Depth"],
                 "suggestion": "Practice mock interviews to improve pacing."
             }
        else:
            final_response = _get_gemini_response(report_history, json_mode=True)
            report_data = final_response if isinstance(final_response, dict) else _parse_json_from_text(str(final_response))
        
        # Save to DB
        from ..db import get_db
        from ..models import InterviewReport
        from flask_login import current_user
        
        db = get_db()
        student_id = current_user.id if current_user.is_authenticated else "anonymous"
        role = "Interview Candidate" 

        InterviewReport.create(
            db,
            student_id,
            role,
            report_data.get('score', 0),
            report_data.get('summary', ''),
            report_data.get('strengths', []),
            report_data.get('weaknesses', []),
            report_data.get('suggestion', '')
        )

        session['report_data'] = report_data
        session.pop('interview_history', None) # Clear history
        return jsonify({"status": "success", "redirect_url": "/report"})
    except Exception as e:
        print(f"Report Error: {e}")
        return jsonify({"error": str(e)}), 500

def _get_gemini_response(messages, json_mode=False):
    if GOOGLE_API_KEY == "dummy-key":
        return {
            "feedback": "This is a mock response (No API Key).",
            "question": "What is your greatest strength? (Mock)"
        }

    import time
    
    retries = 3
    delay = 2

    for attempt in range(retries):
        try:
            model = get_gemini_model()
            
            chat = model.start_chat(history=messages[:-1])
            last_message = messages[-1]['parts'][0]
            
            response = chat.send_message(last_message)
            content = response.text.strip()
            return _parse_json_from_text(content)
        except Exception as e:
            if "429" in str(e) or "ResourceExhausted" in str(e):
                print(f"Gemini 429 Quota Error (Attempt {attempt+1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(delay)
                    delay *= 2 # Exponential backoff
                    continue
            
            print(f"Gemini Error: {e}")
            # Try a simpler fallback for stateless if chat fails (though it shouldn't)
            try:
                 prompt = "\n".join([f"{m['role']}: {m['parts'][0]}" for m in messages])
                 response = model.generate_content(prompt)
                 return _parse_json_from_text(response.text.strip())
            except Exception as e2:
                if attempt < retries - 1 and ("429" in str(e2) or "ResourceExhausted" in str(e2)):
                     time.sleep(delay)
                     delay *= 2
                     continue
                raise e

def _parse_json_from_text(content):
    try:
        # Clean up markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content: # Sometimes just ```
            content = content.split("```")[1].split("```")[0].strip()
            
        if "{" in content:
            start = content.find("{")
            end = content.rfind("}") + 1
            content = content[start:end]
        return json.loads(content)
    except Exception as e:
        print(f"JSON Parse Error: {e}\nContent: {content}")
        # Return empty structure on failure
        return {}
