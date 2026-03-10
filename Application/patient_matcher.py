from rapidfuzz import fuzz
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["hospitalDB"]

patients_collection = db["patients"]


def find_matching_patient(extracted_patient):

    best_match = None
    best_score = 0

    if not extracted_patient:
        return None, 0

    name_input = (
        (extracted_patient.get("first_name") or "") + " " +
        (extracted_patient.get("last_name") or "")
    ).strip()

    dob_input = extracted_patient.get("date_of_birth")

    for patient in patients_collection.find():

        name_db = (
            (patient.get("first_name") or "") + " " +
            (patient.get("last_name") or "")
        ).strip()

        name_score = fuzz.token_sort_ratio(name_input, name_db)

        dob_score = 100 if dob_input == patient.get("date_of_birth") else 0

        final_score = (0.7 * name_score) + (0.3 * dob_score)

        if final_score > best_score:
            best_score = final_score
            best_match = patient

    return best_match, best_score