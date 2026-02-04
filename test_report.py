import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000"

def test_report_generation():
    print("\n--- Testing Interview Flow & Report Generation ---")
    
    # 1. Start Interview to create session
    s = requests.Session()
    try:
        start_payload = {
            "role": "Software Engineer",
            "type": "Technical",
            "difficulty": "Medium",
            "resume_text": "Experienced Python Developer."
        }
        res = s.post(f"{BASE_URL}/api/interview/start", json=start_payload)
        if res.status_code != 200:
            print("Start Failed:", res.text)
            return

        print("Interview Started.")
        
        # 2. Chat a bit (optional, but good for history)
        chat_payload = {"answer": "I have 5 years of experience in Python."}
        s.post(f"{BASE_URL}/api/interview/chat", json=chat_payload)
        print("Chat sent.")
        
        # 3. End Interview (Triggers Report)
        print("Ending Interview (Generating Report)...")
        res = s.post(f"{BASE_URL}/api/interview/end")
        
        if res.status_code == 200:
            data = res.json()
            if data.get('status') == 'success':
                print("Report Generated Successfully!")
                print("Redirect URL:", data.get('redirect_url'))
            else:
                print("Report Generation Error (API Response):", data)
        else:
            print(f"Request Failed: {res.status_code}", res.text)
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_report_generation()
