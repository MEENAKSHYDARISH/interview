import json
import os
import uuid
from flask import g

DB_FILE = 'database.json'

class Collection:
    def __init__(self, db, name):
        self.db = db
        self.name = name

    def _get_data(self):
        return self.db.read().get(self.name, [])

    def find_one(self, query):
        data = self._get_data()
        for item in data:
            match = True
            for k, v in query.items():
                # Handle ObjectId query simulation
                if k == '_id':
                    if str(item.get('_id')) != str(v):
                        match = False
                        break
                elif item.get(k) != v:
                    match = False
                    break
            if match:
                return item
        return None

    def find(self, query=None):
        data = self._get_data()
        if not query:
            return data
        
        results = []
        for item in data:
            match = True
            for k, v in query.items():
                if item.get(k) != v:
                    match = False
                    break
            if match:
                results.append(item)
        return results

    def insert_one(self, doc):
        data = self.db.read()
        if self.name not in data:
            data[self.name] = []
        
        if '_id' not in doc:
            doc['_id'] = str(uuid.uuid4())
            
        data[self.name].append(doc)
        self.db.write(data)
        
        # Mimic PyMongo InsertResult
        class InsertResult:
            inserted_id = doc['_id']
        return InsertResult()

    def update_one(self, query, update):
        data = self.db.read()
        collection_data = data.get(self.name, [])
        
        updated = False
        for item in collection_data:
            match = True
            for k, v in query.items():
                if item.get(k) != v:
                    match = False
                    break
            
            if match:
                # Basic implementation of $set
                if "$set" in update:
                    for sk, sv in update["$set"].items():
                        item[sk] = sv
                updated = True
                break
        
        if updated:
            self.db.write(data)
        return updated

    def delete_many(self, query):
        data = self.db.read()
        collection_data = data.get(self.name, [])
        
        new_collection_data = []
        deleted_count = 0
        
        for item in collection_data:
            match = True
            for k, v in query.items():
                if item.get(k) != v:
                    match = False
                    break
            
            if not match:
                new_collection_data.append(item)
            else:
                deleted_count += 1
        
        if deleted_count > 0:
            data[self.name] = new_collection_data
            self.db.write(data)
            
        return deleted_count

class JsonDB:
    def __init__(self, filepath=DB_FILE):
        self.filepath = filepath
        if not os.path.exists(self.filepath):
            with open(self.filepath, 'w') as f:
                json.dump({"users": [], "job_roles": []}, f)

    def read(self):
        try:
            with open(self.filepath, 'r') as f:
                return json.load(f)
        except:
            return {}

    def write(self, data):
        with open(self.filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def getattr(self, name):
        return Collection(self, name)
    
    # Allow attribute access like db.users
    def __getattr__(self, name):
        return Collection(self, name)

db_instance = JsonDB()

def get_db():
    return db_instance
