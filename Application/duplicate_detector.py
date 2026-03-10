from rapidfuzz import fuzz
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["hospitalDB"]

patients_collection = db["patients"]


def detect_duplicates(new_patient):

    possible_duplicates = []

    new_name = (
        (new_patient.get("first_name") or "") +
        " " +
        (new_patient.get("last_name") or "")
    ).strip()

    new_dob = new_patient.get("date_of_birth")

    for patient in patients_collection.find():

        existing_name = (
            (patient.get("first_name") or "") +
            " " +
            (patient.get("last_name") or "")
        ).strip()

        name_score = fuzz.token_sort_ratio(new_name, existing_name)

        dob_score = 100 if new_dob == patient.get("date_of_birth") else 0

        final_score = (0.7 * name_score) + (0.3 * dob_score)

        if final_score > 80:
            possible_duplicates.append({
                "patient_id": str(patient["_id"]),
                "name": existing_name,
                "confidence": final_score
            })

    return possible_duplicates