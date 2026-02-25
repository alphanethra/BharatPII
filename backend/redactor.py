import re
import cv2
import numpy as np
from pdf2image import convert_from_bytes
from PIL import Image
import io

# -------------------------
# TEXT MASKING ENGINE
# -------------------------

def mask_sensitive_text(text, pii_results):

    for aadhaar in pii_results.get("aadhaar", []):
        masked = "XXXX XXXX " + aadhaar[-4:]
        text = text.replace(aadhaar, masked)

    for pan in pii_results.get("pan", []):
        masked = "XXXXX" + pan[-4:]
        text = text.replace(pan, masked)

    for phone in pii_results.get("phone", []):
        masked = "XXXXXX" + phone[-4:]
        text = text.replace(phone, masked)

    for email in pii_results.get("email", []):
        parts = email.split("@")
        masked = "XXXX@" + parts[1]
        text = text.replace(email, masked)

    return text


# -------------------------
# IMAGE REDACTION (FULL BLUR)
# -------------------------

def blur_entire_image(image_bytes):
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    blurred = cv2.GaussianBlur(img, (51, 51), 30)

    _, buffer = cv2.imencode(".jpg", blurred)
    return buffer.tobytes()


# -------------------------
# PDF REDACTION
# -------------------------

def redact_pdf(pdf_bytes, poppler_path=None):
    pages = convert_from_bytes(pdf_bytes, poppler_path=poppler_path)
    redacted_pages = []

    for page in pages:
        img_bytes = io.BytesIO()
        page.save(img_bytes, format="JPEG")

        blurred_page = blur_entire_image(img_bytes.getvalue())
        redacted_pages.append(Image.open(io.BytesIO(blurred_page)))

    output_pdf = io.BytesIO()
    redacted_pages[0].save(
        output_pdf,
        save_all=True,
        append_images=redacted_pages[1:],
        format="PDF"
    )

    return output_pdf.getvalue()