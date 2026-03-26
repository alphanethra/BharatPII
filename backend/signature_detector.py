import cv2
import numpy as np
import pytesseract
from pytesseract import Output
def detect_and_blur_signature(image_bytes):
    """
    Detect 'Sign' or 'Signature' word
    and blur a properly sized region above it.
    """

    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return image_bytes, False

    ocr_data = pytesseract.image_to_data(
        img,
        output_type=Output.DICT
    )

    height, width, _ = img.shape
    signature_found = False

    for i, word in enumerate(ocr_data['text']):

        clean_word = word.strip().lower()

        if "sign" in clean_word or "हस्ताक्षर" in clean_word:

            x = ocr_data['left'][i]
            y = ocr_data['top'][i]
            w = ocr_data['width'][i]
            h = ocr_data['height'][i]

            # 🔥 Larger blur region
            blur_height = int(height * 0.12)  # 12% of full image height
            blur_width_expand = int(width * 0.08)

            start_y = max(0, y - blur_height)
            end_y = y  # Stop exactly at top of word so "Signature" remains visible

            start_x = max(0, x - blur_width_expand)
            end_x = min(width, x + w + blur_width_expand)

            region = img[start_y:end_y, start_x:end_x]

            if region.size != 0:
                blurred = cv2.GaussianBlur(region, (51, 51), 30)
                img[start_y:end_y, start_x:end_x] = blurred
                signature_found = True

    _, buffer = cv2.imencode(".jpg", img)
    return buffer.tobytes(), signature_found