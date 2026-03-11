from pymongo import MongoClient
from difflib import SequenceMatcher

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["hospitalDB"]
patients_collection = db["patients"]


def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def match_patient(data):

    name = data.get("name")
    dob = data.get("dob")
    mrn = data.get("mrn")

    print("Matching Data:", data)

    # 1️⃣ MRN Match
    if mrn:
        patient = patients_collection.find_one({"mrn": mrn})
        if patient:
            print("MRN Match Found")
            return {
                "match_type": "MRN Match",
                "patient": patient
            }

    # 2️⃣ Name + DOB Match
    if name and dob:
        patient = patients_collection.find_one({
            "name": name,
            "dob": dob
        })
        if patient:
            print("Name + DOB Match Found")
            return {
                "match_type": "Name + DOB Match",
                "patient": patient
            }

    # 3️⃣ Fuzzy Name Match
    if name:
        patients = patients_collection.find()

        best_match = None
        best_score = 0

        for patient in patients:
            score = similarity(name, patient.get("name", ""))

            if score > best_score:
                best_score = score
                best_match = patient

        if best_score > 0.8:
            print("Fuzzy Match Found")
            return {
                "match_type": "Fuzzy Name Match",
                "patient": best_match,
                "similarity": best_score
            }

    print("No Match Found")

    # If no match found, create a new patient
    new_patient = {
    "name": name,
    "dob": dob,
    "mrn": mrn
    }

    inserted = patients_collection.insert_one(new_patient)

    new_patient["_id"] = inserted.inserted_id

    print("New Patient Created")

    return {
        "match_type": "New Patient Created",
        "patient": new_patient
}