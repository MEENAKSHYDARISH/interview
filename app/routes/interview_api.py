from flask import Blueprint, request, jsonify, session
import openai
import os
import json

interview_api_bp = Blueprint('interview_api', __name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "dummy-key")
openai.api_key = OPENAI_API_KEY

SYSTEM_PROMPT_TEMPLATE = """You are a professional AI Interviewer for a {role} position.
Your goal is to conduct a structured interview based on the candidate's resume and responses.
Current Interface Difficulty: {difficulty}

Resume Context:
{resume_text}

Rules:
1. Ask one clear question at a time.
2. Be professional but encouraging.
3. If the user's answer is too brief or off-topic, politely probe further.
4. If the answer is good, acknowledge it briefly and move to the next relevant topic.
5. Keep your responses concise (suitable for Text-to-Speech). Max 2-3 sentences for feedback, then the question.
6. The output must be JSON with the following structure:
{{
    "feedback": "Brief feedback on the previous answer (if any).",
    "question": "The next interview question."
}}
"""

@interview_api_bp.route('/api/interview/start', methods=['POST'])
def start_interview():
    data = request.json
    role = data.get('role', 'Candidate')
    resume_text = data.get('resume_text', 'No resume provided.')
    difficulty = data.get('difficulty', 'Medium')

    # store context in session (simple state management for POC)
    full_system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        role=role,
        difficulty=difficulty,
        resume_text=resume_text
    )

    session['interview_history'] = [
        {"role": "system", "content": full_system_prompt}
    ]
    
    # Generate first question
    initial_prompt = "Start the interview. Introduce yourself briefly as the AI Interviewer and ask the first question (e.g., 'Tell me about yourself')."
    session['interview_history'].append({"role": "user", "content": initial_prompt})

    try:
        response_data = _get_openai_response(session['interview_history'])
        # Add assistant response to history
        session['interview_history'].append({"role": "assistant", "content": json.dumps(response_data)})
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
    session['interview_history'].append({"role": "user", "content": user_answer})

    try:
        response_data = _get_openai_response(session['interview_history'])
        session['interview_history'].append({"role": "assistant", "content": json.dumps(response_data)})
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
    history.append({"role": "system", "content": report_prompt})

    try:
        if OPENAI_API_KEY == "dummy-key":
             report_data = {
                 "score": 85,
                 "summary": "Good technical understanding but needs more confidence.",
                 "strengths": ["Python Knowledge", "Problem Solving"],
                 "weaknesses": ["Communication Spleed", "System Design Depth"],
                 "suggestion": "Practice mock interviews to improve pacing."
             }
        else:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=history,
                temperature=0.7,
                max_tokens=600
            )
            content = response.choices[0].message["content"].strip()
            report_data = _parse_json_from_text(content)
        
        session['report_data'] = report_data
        session.pop('interview_history', None) # Clear history
        return jsonify({"status": "success", "redirect_url": "/report"})
    except Exception as e:
        print(f"Report Error: {e}")
        return jsonify({"error": str(e)}), 500

def _get_openai_response(messages):
    if OPENAI_API_KEY == "dummy-key":
        return {
            "feedback": "This is a mock response (No API Key).",
            "question": "What is your greatest strength? (Mock)"
        }

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=300
        )
        content = response.choices[0].message["content"].strip()
        # Ensure we just get the JSON part if there's extra text
        # Ensure we just get the JSON part if there's extra text
        return _parse_json_from_text(content)
    except Exception as e:
        print(f"OpenAI Error: {e}")
        raise e

def _parse_json_from_text(content):
    try:
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "{" in content:
            start = content.find("{")
            end = content.rfind("}") + 1
            content = content[start:end]
        return json.loads(content)
    except Exception as e:
        print(f"JSON Parse Error: {e}")
        # Return empty structure on failure
        return {}
