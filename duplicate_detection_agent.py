import os
import json
from database.mongo import patients_collection
from google import genai
from dotenv import load_dotenv

load_dotenv()


def detect_duplicate_patient(new_patient):

    """
    Detect possible duplicate patient records using AI
    """

    api_key = os.getenv("GEMINI_API_KEY1")

    if not api_key:
        return []

    try:

        client = genai.Client(api_key=api_key)

        # Load existing patients
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
You are a hospital duplicate detection AI.

Determine if the new patient is likely the same as any existing patient.

New Patient:

{json.dumps(new_patient, indent=2)}

Existing Patients:

{json.dumps(db_records, indent=2)}

Return JSON ONLY:

{{
"duplicates":[
    {{
        "patient_id":"id",
        "confidence":0-100
    }}
]
}}
"""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )

        text = response.text.strip()

        text = text.replace("```json","").replace("```","")

        result = json.loads(text)

        return result.get("duplicates", [])

    except Exception as e:

        print("Duplicate detection failed:", e)

        return []
