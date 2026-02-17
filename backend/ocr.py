import pytesseract
from PIL import Image
import cv2
import numpy as np
import io
import re

# Path to Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def preprocess_image(image):
    img = np.array(image)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Resize (improves accuracy)
    gray = cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)

    # Denoise
    gray = cv2.fastNlMeansDenoising(gray, None, 30, 7, 21)

    # Adaptive threshold (better than simple threshold)
    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        2
    )

    return thresh


def clean_text(text):
    # Remove extra spaces and new lines
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_text(image_bytes):
    image = Image.open(io.BytesIO(image_bytes))

    processed = preprocess_image(image)

    custom_config = r'--oem 3 --psm 6'

    text = pytesseract.image_to_string(
        processed,
        lang="eng+hin+tam+tel+kan+mal",
        config=custom_config
    )

    text = clean_text(text)

    return text
