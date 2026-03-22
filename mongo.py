from pymongo import MongoClient

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")

# Database
db = client["hospital_ai"]

# Collections
patients_collection = db["patients"]
uploads_collection = db["uploads"]
staff_collection = db["staff"]
admin_collection = db["admin"]
