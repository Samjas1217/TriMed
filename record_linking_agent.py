import os
import json
from rapidfuzz import fuzz
from database.mongo import patients_collection
from google import genai
from dotenv import load_dotenv

load_dotenv()


def rule_match(patient):

    best_match = None
    best_score = 0

    name_input = (
        (patient.get("first_name", "") + " " + patient.get("last_name", ""))
    ).lower()

    dob_input = patient.get("date_of_birth")

    for p in patients_collection.find():

        name_db = (
            (p.get("first_name", "") + " " + p.get("last_name", ""))
        ).lower()

        name_score = fuzz.token_sort_ratio(name_input, name_db)

        dob_score = 100 if dob_input == p.get("date_of_birth") else 0

        score = (0.7 * name_score) + (0.3 * dob_score)

        if score > best_score:

            best_score = score
            best_match = p

    return best_match, best_score


def ai_match(patient):

    api_key = os.getenv("GEMINI_API_KEY1")

    if not api_key:
        return None

    client = genai.Client(api_key=api_key)

    patients = list(patients_collection.find())

    db_records = []

    for p in patients:

        db_records.append({
            "id": str(p["_id"]),
            "name": p.get("first_name","") + " " + p.get("last_name",""),
            "dob": p.get("date_of_birth"),
            "phone": p.get("phone"),
            "email": p.get("email")
        })

    prompt = f"""
You are a hospital record matching AI.

Find the most likely patient match.

Patient from OCR:

{json.dumps(patient,indent=2)}

Existing database patients:

{json.dumps(db_records,indent=2)}

Return JSON:

{{
"patient_id":"id or null",
"confidence":0-100
}}
"""

    try:

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )

        text = response.text.strip()

        text = text.replace("```json","").replace("```","")

        result = json.loads(text)

        return result

    except Exception as e:

        print("AI matching failed:", e)

        return None


def link_patient_record(patient):

    # First try rule matching
    match, score = rule_match(patient)

    if match and score > 85:

        return {
            "patient_id": str(match["_id"]),
            "confidence": score
        }

    # If rule match weak → use AI
    ai_result = ai_match(patient)

    if ai_result:

        return ai_result

    return {
        "patient_id": None,
        "confidence": 0
    }
