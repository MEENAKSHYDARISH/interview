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
