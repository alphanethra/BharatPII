import cv2
import numpy as np
import pytesseract
from pytesseract import Output


def detect_and_blur_signature(image_bytes):
    """
    Blur only handwritten signature
    - PAN: Signature
    - DL : Sign. Of Holder
    - Ignore: Sign. Licensing Authority
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

        clean = word.strip().lower()

        # detect only holder signature
        if "holder" in clean or "signature" in clean:

            # avoid licensing authority
            next_word = ""
            if i + 1 < len(ocr_data['text']):
                next_word = ocr_data['text'][i+1].strip().lower()

            if "authority" in next_word:
                continue

            x = ocr_data['left'][i]
            y = ocr_data['top'][i]
            w = ocr_data['width'][i]
            h = ocr_data['height'][i]

            # blur region ABOVE the word
            start_y = max(0, y - int(h * 3))
            end_y = y

            start_x = max(0, x - int(w * 1.5))
            end_x = min(width, x + w + int(w * 1.5))

            region = img[start_y:end_y, start_x:end_x]

            if region.size != 0:
                blurred = cv2.GaussianBlur(region, (51, 51), 30)
                img[start_y:end_y, start_x:end_x] = blurred
                signature_found = True

    _, buffer = cv2.imencode(".jpg", img)
    return buffer.tobytes(), signature_found