from pdf2image import convert_from_path
import os


POPPLER_PATH = r"C:\poppler-25.12.0\Library\bin"


def pdf_to_image(pdf_path, output_folder, unique_id):

    pages = convert_from_path(
        pdf_path,
        dpi=300,
        first_page=1,
        last_page=1,
        poppler_path=POPPLER_PATH
    )

    image_path = os.path.join(
        output_folder,
        f"{unique_id}.jpg"
    )

    pages[0].save(image_path, "JPEG")

    return image_path


