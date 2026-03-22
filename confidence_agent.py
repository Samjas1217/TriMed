import re

def calculate_ocr_confidence(text: str) -> int:
    """
    Estimate OCR confidence based on text quality
    """

    if not text:
        return 0

    length_score = min(len(text) / 500, 1) * 40

    alpha_chars = len(re.findall(r"[A-Za-z]", text))
    total_chars = len(text)

    ratio = alpha_chars / total_chars if total_chars > 0 else 0

    char_score = ratio * 60

    return int(length_score + char_score)


def calculate_extraction_confidence(patient_data: dict) -> int:
    """
    Check how many important fields were extracted
    """

    fields = [
        "first_name",
        "last_name",
        "date_of_birth",
        "phone_number",
        "email"
    ]

    found = 0

    for f in fields:
        if patient_data.get(f):
            found += 1

    return int((found / len(fields)) * 100)


def calculate_duplicate_risk(duplicates: list) -> int:
    """
    Estimate duplicate risk
    """

    if not duplicates:
        return 0

    highest = max(d["confidence"] for d in duplicates)

    return int(highest)
