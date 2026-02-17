from pdf2image import convert_from_bytes
from ocr import extract_text
import io

# IMPORTANT: use YOUR poppler path
POPPLER_PATH = r"C:\Users\karth\Downloads\poppler\Library\bin"

def ocr_scanned_pdf(file_bytes):
    images = convert_from_bytes(
        file_bytes,
        poppler_path=POPPLER_PATH
    )

    full_text = ""

    for image in images:
        img_buffer = io.BytesIO()
        image.save(img_buffer, format="PNG")
        img_bytes = img_buffer.getvalue()

        text = extract_text(img_bytes)
        full_text += text + "\n"

    return full_text
