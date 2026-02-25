from pdf2image import convert_from_bytes
import pytesseract
import io
from PIL import Image

def extract_text_from_image(image_bytes):
    img = Image.open(io.BytesIO(image_bytes))
    return pytesseract.image_to_string(img)

def extract_text_from_pdf(pdf_bytes, poppler_path=None):
    pages = convert_from_bytes(pdf_bytes, poppler_path=poppler_path)
    text = ""

    for page in pages:
        text += pytesseract.image_to_string(page)

    return text