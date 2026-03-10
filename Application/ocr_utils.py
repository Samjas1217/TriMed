from PIL import Image
import pytesseract
import os

pytesseract.pytesseract.tesseract_cmd = \
r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text_from_image(image_path):

    try:
        if not os.path.exists(image_path):
            return "Image not found"

        # Open image
        img = Image.open(image_path)

        # Convert to grayscale
        img = img.convert("L")

        # Optional: Improve contrast (thresholding)
        img = img.point(lambda x: 0 if x < 140 else 255, '1')

        # OCR config
        custom_config = r'--oem 3 --psm 6'

        text = pytesseract.image_to_string(img, config=custom_config)

        return text.strip()

    except Exception as e:
        return f"OCR Error: {str(e)}"
