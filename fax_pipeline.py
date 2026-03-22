from core.ocr_engine import run_ocr
from agents.patient_extraction_agent import extract_patient_info
from agents.record_linking_agent import link_patient_record
from agents.duplicate_detection_agent import detect_duplicate_patient
from database.patient_repository import create_patient
from agents.confidence_agent import (
    calculate_ocr_confidence,
    calculate_extraction_confidence,
    calculate_duplicate_risk
)
from agents.medical_summary_agent import generate_medical_summary
from agents.ocr_correction_agent import correct_ocr_text

def process_fax(image_path: str):

    # -----------------------------
    # Step 1 : OCR
    # -----------------------------
    ocr_text = run_ocr(image_path)

    if not ocr_text:
        raise Exception("OCR returned empty text")

    # Step 1.5 : OCR Correction
    ocr_text = correct_ocr_text(ocr_text)



    # -----------------------------
    # Step 2 : AI Extraction
    # -----------------------------
    patient_data = extract_patient_info(ocr_text)

    if not patient_data:
        raise Exception("AI extraction failed")



    # -----------------------------
    # Step 3 : Patient Matching
    # -----------------------------
    match = link_patient_record(patient_data)

    patient_id = match.get("patient_id")
    confidence = match.get("confidence", 0)



    # -----------------------------
    # Step 4 : If no match → create patient
    # -----------------------------
    duplicates = []

    if not patient_id:

        patient_id = create_patient(patient_data)

        # Run duplicate detection AI
        duplicates = detect_duplicate_patient(patient_data)



    # -----------------------------
    # Step 5 : Document Classification & Return pipeline result
    # -----------------------------
    
    document_type = "Unknown"
    try:
        from agents.document_classifier_agent import classify_document
        document_type = classify_document(ocr_text)
    except Exception as e:
        print(e)
        document_type = "Unknown"

    # Confidence calculations
    ocr_conf = calculate_ocr_confidence(ocr_text)

    extraction_conf = calculate_extraction_confidence(patient_data)

    duplicate_risk = calculate_duplicate_risk(duplicates)

    # -----------------------------
    # Step 5a : Medical Summary
    # -----------------------------
    medical_summary = generate_medical_summary(ocr_text)

    return {

        "ocr_text": ocr_text,

        "patient_id": patient_id,

        "patient_data": patient_data,

        "match_confidence": confidence,

        "duplicates": duplicates,

        "document_type": document_type,

        "ocr_confidence": ocr_conf,

        "extraction_confidence": extraction_conf,

        "duplicate_risk": duplicate_risk,
        
        "medical_summary": medical_summary
    }

