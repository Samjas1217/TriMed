import json
import os
import random
import re
from dotenv import load_dotenv
from google import genai

load_dotenv()


def get_api_key():

    keys = [
        os.getenv("GEMINI_API_KEY1"),
        os.getenv("GEMINI_API_KEY2"),
        os.getenv("GEMINI_API_KEY3")
    ]

    keys = [k for k in keys if k]

    if not keys:
        return None

    return random.choice(keys)


def regex_extract(text):

    data = {}

    patterns = {
        "first_name": r"First\s*Name\s*:\s*(\w+)",
        "last_name": r"Last\s*Name\s*:\s*(\w+)",
        "patient_id": r"Patient\s*ID\s*:\s*([A-Za-z0-9\-]+)",
        "date_of_birth": r"Date\s*of\s*Birth\s*:\s*([0-9\-\/]+)",
        "age": r"Age\s*:\s*([0-9]+)",
        "gender": r"Gender\s*:\s*(Male|Female)",
        "blood_group": r"Blood\s*Group\s*:\s*([A-Z\+\-]+)",
        "phone_number": r"Phone\s*Number\s*:\s*([\+0-9\s\-]+)",
        "email": r"Email\s*ID\s*:\s*([A-Za-z0-9@.\-_]+)"
    }

    for key, pattern in patterns.items():

        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            value = match.group(1).strip()

            if key == "phone_number":
                value = normalize_phone(value)

            data[key] = value

    return data


def normalize_phone(phone):

    digits = re.sub(r"\D", "", phone)

    if digits.startswith("91") and len(digits) == 12:
        return "+" + digits

    if len(digits) == 10:
        return "+91" + digits

    return phone


def gemini_extract(ocr_text):

    api_key = get_api_key()

    if not api_key:
        return None

    try:

        client = genai.Client(api_key=api_key)

        prompt = f"""
You are a medical document parser.

Extract structured patient information from OCR text.

Return JSON ONLY.

Fields:
first_name
last_name
patient_id
date_of_birth
age
gender
blood_group
phone_number
email

OCR TEXT:
{ocr_text}
"""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )

        text = response.text.strip()

        text = text.replace("```json", "").replace("```", "")

        return json.loads(text)

    except Exception as e:

        print("Gemini extraction failed:", e)

        return None


def extract_patient_info(ocr_text):

    # First try regex (fast)
    data = regex_extract(ocr_text)

    # If important fields missing → use AI
    if not data.get("first_name") or not data.get("patient_id"):

        ai_data = gemini_extract(ocr_text)

        if ai_data:
            data.update(ai_data)

    return data
