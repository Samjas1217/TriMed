import os
import json
from dotenv import load_dotenv
from google import genai
from database.mongo import patients_collection

load_dotenv()


def ai_patient_search(query: str):
    """
    AI-powered patient search using natural language
    """

    api_key = os.getenv("GEMINI_API_KEY1")

    if not api_key:
        return []

    try:

        client = genai.Client(api_key=api_key)

        # Load patients from database
        patients = list(patients_collection.find())

        patient_records = []

        for p in patients:

            patient_records.append({
                "patient_id": str(p["_id"]),
                "first_name": p.get("first_name"),
                "last_name": p.get("last_name"),
                "date_of_birth": p.get("date_of_birth"),
                "phone": p.get("phone"),
                "email": p.get("email"),
                "patient_identifier": p.get("patient_identifier")
            })

        prompt = f"""
You are a hospital database search assistant.

User query:
{query}

Patient records:
{json.dumps(patient_records, indent=2)}

Find matching patients.

Return JSON ONLY in this format:

{{
"patients":[
    {{
        "patient_id":"id"
    }}
]
}}
"""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )

        text = response.text.strip()

        text = text.replace("```json", "").replace("```", "")

        result = json.loads(text)

        return result.get("patients", [])

    except Exception as e:

        print("AI patient search failed:", e)

        return []
