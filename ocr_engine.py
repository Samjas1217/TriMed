import pytesseract
import os
import cv2
import easyocr

from core.image_processor import preprocess_image

# Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Initialize EasyOCR reader
reader = easyocr.Reader(['en'], gpu=False)


def run_tesseract(image):

    config = r"--oem 3 --psm 6"

    text = pytesseract.image_to_string(
        image,
        config=config
    )

    return text.strip()


def run_easyocr(image):

    results = reader.readtext(image)

    words = []

    for (_, text, prob) in results:
        if prob > 0.4:
            words.append(text)

    return " ".join(words)


def merge_text(t1, t2):

    if len(t1) > len(t2):
        return t1

    return t2


def run_ocr(image_path: str) -> str:

    try:

        if not os.path.exists(image_path):
            raise Exception("OCR image not found")

        # Preprocess image
        processed = preprocess_image(image_path)

        # Run both OCR engines
        text1 = run_tesseract(processed)

        text2 = run_easyocr(processed)

        # Merge best result
        final_text = merge_text(text1, text2)

        return final_text.strip()

    except Exception as e:

        print("OCR failed:", e)

        return ""
