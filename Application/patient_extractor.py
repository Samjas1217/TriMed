import re

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

    # -----------------------------
    # CLEAN OCR TEXT
    # -----------------------------
    text = ocr_text.replace("|", ":")
    text = re.sub(r'\s+', ' ', text)

    # -----------------------------
    # FIRST NAME
    # -----------------------------
    match = re.search(r'First\s*Name\s*:\s*([A-Za-z]+)', text, re.IGNORECASE)
    if match:
        data["first_name"] = match.group(1)

    # -----------------------------
    # LAST NAME
    # -----------------------------
    match = re.search(r'Last\s*Name\s*:\s*([A-Za-z]+)', text, re.IGNORECASE)
    if match:
        data["last_name"] = match.group(1)

    # -----------------------------
    # PATIENT ID
    # -----------------------------
    match = re.search(r'Patient\s*ID\s*:\s*([A-Za-z0-9\-]+)', text, re.IGNORECASE)
    if match:
        data["patient_id"] = match.group(1)

    # -----------------------------
    # DATE OF BIRTH
    # -----------------------------
    match = re.search(r'Date\s*of\s*Birth\s*:\s*([\d\-\/]+)', text, re.IGNORECASE)
    if match:
        data["date_of_birth"] = match.group(1)

    # -----------------------------
    # AGE
    # -----------------------------
    match = re.search(r'Age\s*:\s*(\d+)', text, re.IGNORECASE)
    if match:
        data["age"] = match.group(1)

    # -----------------------------
    # GENDER
    # -----------------------------
    match = re.search(r'Gender\s*:\s*(Male|Female|Other)', text, re.IGNORECASE)
    if match:
        data["gender"] = match.group(1)

    # -----------------------------
    # BLOOD GROUP
    # -----------------------------
    match = re.search(r'Blood\s*Group\s*:\s*([ABO]{1,2}[+-])', text, re.IGNORECASE)
    if match:
        data["blood_group"] = match.group(1)

    # -----------------------------
    # PHONE NUMBER
    # -----------------------------
    match = re.search(r'Phone\s*Number\s*:\s*([\+\d\s\-]+)', text, re.IGNORECASE)
    if match:
        data["phone_number"] = match.group(1).strip()

    # -----------------------------
    # EMAIL
    # -----------------------------
    match = re.search(r'Email\s*ID\s*:\s*([\w\.-]+@[\w\.-]+)', text, re.IGNORECASE)
    if match:
        data["email"] = match.group(1)

    return data