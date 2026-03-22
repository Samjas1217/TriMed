import json
from google import genai
from agents.patient_extraction_agent import get_api_key

def correct_ocr_text(ocr_text):
    api_key = get_api_key()
    
    if not api_key:
        return ocr_text
        
    try:
        client = genai.Client(api_key=api_key)
        
        prompt = f"""
        You are an advanced OCR correction engine for medical documents.
        
        Fix common OCR spelling mistakes in the following text.
        For example: 'Patlent' -> 'Patient', 'Gupla' -> 'Gupta', 'D0B' -> 'DOB'.
        Correct the text to be as accurate as possible to the likely original document.
        Do NOT add any conversational filler, do NOT summarize, do NOT change the layout.
        JUST RETURN THE CORRECTED TEXT.

        OCR TEXT:
        {ocr_text}
        """
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        
        corrected_text = response.text.strip()
        
        # If the model refused or returned something drastically short/wrong, fallback to original
        if len(corrected_text) < len(ocr_text) * 0.5:
             return ocr_text
             
        return corrected_text
        
    except Exception as e:
        print("OCR correction failed:", e)
        return ocr_text
