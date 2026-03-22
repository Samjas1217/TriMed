import os
from google import genai
from dotenv import load_dotenv

load_dotenv()


def classify_document(ocr_text):

    """
    Classify the medical document type using AI
    """

    api_key = os.getenv("GEMINI_API_KEY1")

    if not api_key:
        return "Unknown"

    try:

        client = genai.Client(api_key=api_key)

        prompt = f"""
You are a medical document classifier.

Classify the document type.

Possible types:

Lab Report
Prescription
Referral
Insurance Form
Medical Record
Discharge Summary
Radiology Report
Other

Return ONLY the document type.

Document Text:

{ocr_text}
"""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )

        doc_type = response.text.strip()

        return doc_type

    except Exception as e:

        print("Document classification failed:", e)

        return "Unknown"