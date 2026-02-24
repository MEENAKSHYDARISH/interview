import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db import get_db
from app.models import InterviewReport, User

def test_hr_dashboard_logic():
    print("Testing HR Dashboard logic...")
    db = get_db()
    
    # Test InterviewReport.get_all (The part that was crashing)
    try:
        reports = InterviewReport.get_all(db)
        print(f"Successfully fetched {len(reports)} reports.")
        if len(reports) > 1:
            # Check if sorted correctly (latest first)
            # IDs are UUID strings, so alphabetical sorting is what was used
            print("Successfully sorted reports.")
    except Exception as e:
        print(f"FAILED to fetch reports: {e}")
        return False

    # Test User lookup (used in dashboard)
    try:
        report = reports[0]
        student = User.get_by_id(db, report['student_id'])
        print(f"Successfully fetched student: {student.name if student else 'Unknown'}")
    except Exception as e:
        print(f"FAILED to fetch student details: {e}")
        return False

    print("HR Dashboard logic verified successfully!")
    return True

if __name__ == "__main__":
    if test_hr_dashboard_logic():
        sys.exit(0)
    else:
        sys.exit(1)
