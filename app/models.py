from flask_login import UserMixin
# from bson import ObjectId # No longer needed

class User(UserMixin):
    def __init__(self, user_doc):
        self.id = str(user_doc['_id'])
        self.email = user_doc.get('email')
        self.name = user_doc.get('name', 'Student')
        self.role = user_doc.get('role', 'student')
        self.password_hash = user_doc.get('password')

    @staticmethod
    def get_by_id(db, user_id):
        # Removed ObjectId.is_valid check as we use string UUIDs now
        doc = db.users.find_one({"_id": user_id})
        if doc:
            return User(doc)
        return None


    @staticmethod
    def get_by_email(db, email):
        doc = db.users.find_one({"email": email})
        if doc:
            return User(doc)
        return None

class Question:
    def __init__(self, role, type, content, hr_id):
        self.role = role
        self.type = type
        self.content = content
        self.hr_id = hr_id

    @staticmethod
    def create(db, role, type, content, hr_id):
        return db.questions.insert_one({
            "role": role,
            "type": type,
            "content": content,
            "hr_id": hr_id,
            "created_at": "now" # In real app use datetime
        })
        
    @staticmethod
    def get_by_role(db, role):
        return list(db.questions.find({"role": role}))

class InterviewReport:
    @staticmethod
    def create(db, student_id, role, score, summary, strengths, weaknesses, suggestion):
        return db.reports.insert_one({
            "student_id": student_id,
            "role": role,
            "score": score,
            "summary": summary,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "suggestion": suggestion,
            "date": "Today" # Use datetime in prod
        })

    @staticmethod
    def get_all(db):
        return list(db.reports.find().sort("_id", -1))

    @staticmethod
    def get_by_id(db, report_id):
        return db.reports.find_one({"_id": report_id})
