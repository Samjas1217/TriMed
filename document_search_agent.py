import json
from google import genai
from database.mongo import uploads_collection, patients_collection
from agents.patient_extraction_agent import get_api_key

def ai_document_search(query_text):
    """
    Search for documents using natural language by first converting the query
    into a MongoDB filter using Gemini.
    """
    api_key = get_api_key()
    if not api_key:
        return []
        
    try:
        client = genai.Client(api_key=api_key)
        
        prompt = f"""
        You are an AI assistant helping doctors search for medical documents.
        Analyze the following query and extract the search parameters.
        
        Return JSON ONLY with any of the following fields if they are mentioned:
        - document_type (e.g., "Lab Report", "Prescription", etc. - match the exact casing if possible)
        - patient_name (if a name is mentioned, like "Sanjay Gupta")
        
        QUERY:
        "{query_text}"
        """
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        
        text = response.text.strip().replace("```json", "").replace("```", "")
        search_params = json.loads(text)
        
        mongo_filter = {}
        
        # Filter by document type
        if "document_type" in search_params and search_params["document_type"]:
            mongo_filter["document_type"] = {"$regex": search_params["document_type"], "$options": "i"}
            
        # Filter by patient
        if "patient_name" in search_params and search_params["patient_name"]:
            # Need to find the patient ID first
            name_parts = search_params["patient_name"].split()
            patient_filter = {}
            if len(name_parts) >= 1:
                patient_filter["first_name"] = {"$regex": name_parts[0], "$options": "i"}
            if len(name_parts) >= 2:
                patient_filter["last_name"] = {"$regex": name_parts[1], "$options": "i"}
                
            matched_patients = list(patients_collection.find(patient_filter, {"patient_id": 1}))
            if not matched_patients:
                return [] # No patient found with that name
                
            patient_ids = [p["patient_id"] for p in matched_patients if "patient_id" in p]
            if patient_ids:
                mongo_filter["matched_patient_id"] = {"$in": patient_ids}
                
        # If no specific filters could be extracted, maybe just search ocr_text?
        if not mongo_filter:
             # Basic keyword fallback
             mongo_filter["ocr_text"] = {"$regex": query_text, "$options": "i"}
             
        # Execute query
        results = list(uploads_collection.find(mongo_filter).sort("uploaded_at", -1).limit(20))
        
        # Serialize ObjectIds and dates
        for res in results:
            res["_id"] = str(res["_id"])
            if "uploaded_at" in res:
                res["uploaded_at"] = res["uploaded_at"].isoformat() if res["uploaded_at"] else None
                
        return results
        
    except Exception as e:
        print("AI document search failed:", e)
        return []
