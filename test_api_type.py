import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_start_interview(role, interview_type):
    print(f"\n--- Testing Start Interview: {role} ({interview_type}) ---")
    payload = {
        "role": role,
        "type": interview_type,
        "difficulty": "Medium",
        "resume_text": "Experienced in Python, Flask, and System Design. Led a team of 5 engineers."
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/interview/start", json=payload)
        if response.status_code == 200:
            data = response.json()
            if 'error' in data:
                print("API ERROR:", data['error'])
                with open("last_error.txt", "w") as f:
                    f.write(data['error'])
            print("Response:", json.dumps(data, indent=2))
        else:
            print(f"Error: {response.status_code}", response.text)
    except Exception as e:
        print(f"Request Failed: {e}")

if __name__ == "__main__":
    test_start_interview("Software Engineer", "Behavioral")
    test_start_interview("Software Engineer", "Technical")
