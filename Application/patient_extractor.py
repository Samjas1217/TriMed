import re
from ai_patient_agent import PatientInfoAgent
def extract_patient_info(ocr_text):

    data = {
        "first_name": None,
        "last_name": None,
        "patient_id": None,
        "date_of_birth": None,
        "age": None,
        "gender": None,
        "blood_group": None,
        "phone_number": None,
        "email": None
    }

    text = ocr_text

    # -----------------------------
    # FIRST NAME
    # -----------------------------
    match = re.search(r'First\s*Name\s*:\s*(.+)', text, re.IGNORECASE)
    if match:
        data["first_name"] = match.group(1).strip()

    # -----------------------------
    # LAST NAME
    # -----------------------------
    match = re.search(r'Last\s*Name\s*:\s*(.+)', text, re.IGNORECASE)
    if match:
        data["last_name"] = match.group(1).strip()

    # -----------------------------
    # PATIENT ID
    # -----------------------------
    match = re.search(r'Patient\s*ID\s*:\s*(.+)', text, re.IGNORECASE)
    if match:
        data["patient_id"] = match.group(1).strip()

    # -----------------------------
    # DATE OF BIRTH
    # -----------------------------
    match = re.search(r'Date\s*of\s*Birth\s*:\s*(.+)', text, re.IGNORECASE)
    if match:
        data["date_of_birth"] = match.group(1).strip()

    # -----------------------------
    # AGE
    # -----------------------------
    match = re.search(r'Age\s*:\s*(.+)', text, re.IGNORECASE)
    if match:
        data["age"] = match.group(1).strip()

    # -----------------------------
    # GENDER
    # -----------------------------
    match = re.search(r'Gender\s*:\s*(.+)', text, re.IGNORECASE)
    if match:
        data["gender"] = match.group(1).strip()

    # -----------------------------
    # BLOOD GROUP
    # -----------------------------
    match = re.search(r'Blood\s*Group\s*:\s*(.+)', text, re.IGNORECASE)
    if match:
        data["blood_group"] = match.group(1).strip()

    # -----------------------------
    # PHONE NUMBER
    # -----------------------------
    match = re.search(r'Phone\s*Number\s*:\s*(.+)', text, re.IGNORECASE)
    if match:
        data["phone_number"] = match.group(1).strip()

    # -----------------------------
    # EMAIL
    # -----------------------------
    match = re.search(r'Email\s*ID\s*:\s*(.+)', text, re.IGNORECASE)
    if match:
        data["email"] = match.group(1).strip()
    
    # If important fields missing → use AI
    if not data["first_name"] or not data["date_of_birth"]:

        try:
            agent = PatientInfoAgent()

            ai_result = agent.run(text)

            if isinstance(ai_result, dict):
                for key in data:
                    if not data[key] and key in ai_result:
                        data[key] = ai_result[key]

        except Exception as e:
            print("AI extraction failed:", e)

    return data