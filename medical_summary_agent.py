import json
from google import genai
from agents.patient_extraction_agent import get_api_key

def generate_medical_summary(ocr_text):
    api_key = get_api_key()
    
    if not api_key:
        return None
        
    try:
        client = genai.Client(api_key=api_key)
        
        prompt = f"""
        You are an expert AI medical assistant reviewing a patient's medical document.
        
        Extract a structured medical summary from the following OCR text.
        
        Return JSON ONLY with exactly these fields:
        - chief_complaint: A short sentence summarizing why the patient is here or what the document is about. If not evident, use "Not specified".
        - diagnosis: Any diagnoses mentioned. If none, use "Not specified".
        - medications: Any medications mentioned. If none, use "None mentioned".
        - recommended_action: The recommended next steps or follow-ups. If none, use "No specific action recommended".
        
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
        print("Medical summary generation failed:", e)
        return {
            "chief_complaint": "Extraction failed",
            "diagnosis": "Extraction failed",
            "medications": "Extraction failed",
            "recommended_action": "Extraction failed"
        }
