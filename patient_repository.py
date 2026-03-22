from database.mongo import patients_collection
from datetime import datetime
from bson import ObjectId


# -----------------------------
# Create new patient
# -----------------------------
def create_patient(patient_data):

    try:

        # Prevent duplicates
        existing = patients_collection.find_one({
            "first_name": patient_data.get("first_name"),
            "last_name": patient_data.get("last_name"),
            "date_of_birth": patient_data.get("date_of_birth")
        })

        if existing:
            return str(existing["_id"])

        new_patient = {
            "first_name": patient_data.get("first_name"),
            "last_name": patient_data.get("last_name"),
            "date_of_birth": patient_data.get("date_of_birth"),
            "phone_number": patient_data.get("phone_number"),
            "email": patient_data.get("email"),
            "patient_identifier": patient_data.get("patient_id"),
            "created_at": datetime.utcnow()
        }

        result = patients_collection.insert_one(new_patient)

        return str(result.inserted_id)

    except Exception as e:
        print("Create patient error:", e)
        return None


# -----------------------------
# Find patient by ID
# -----------------------------
def get_patient_by_id(patient_id):

    try:

        patient = patients_collection.find_one({
            "_id": ObjectId(patient_id)
        })

        return patient

    except Exception as e:
        print("Patient lookup error:", e)
        return None


# -----------------------------
# Find patient by details
# -----------------------------
def find_patient_by_details(first_name, last_name, dob):

    try:

        patient = patients_collection.find_one({
            "first_name": first_name,
            "last_name": last_name,
            "date_of_birth": dob
        })

        return patient

    except Exception as e:
        print("Patient search error:", e)
        return None


# -----------------------------
# Get all patients
# -----------------------------
def get_all_patients():

    try:

        patients = list(
            patients_collection.find()
            .sort("created_at", -1)
        )

        return patients

    except Exception as e:
        print("Fetch patients error:", e)
        return []


# -----------------------------
# Update patient info
# -----------------------------
def update_patient(patient_id, update_data):

    try:

        patients_collection.update_one(
            {"_id": ObjectId(patient_id)},
            {"$set": update_data}
        )

    except Exception as e:
        print("Update patient error:", e)


# -----------------------------
# Delete patient
# -----------------------------
def delete_patient(patient_id):

    try:

        patients_collection.delete_one({
            "_id": ObjectId(patient_id)
        })

    except Exception as e:
        print("Delete patient error:", e)
