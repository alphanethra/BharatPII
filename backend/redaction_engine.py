import re
import cv2
import numpy as np
import pytesseract
from pytesseract import Output
from pdf2image import convert_from_bytes
from PIL import Image
import io


# ==========================================================
# TEXT REDACTION
# ==========================================================

def redact_text(text, pii_results):

    for category, values in pii_results.items():
        for value in values:
            if not value:
                continue

            if category == "aadhaar":
                masked = "XXXX XXXX " + value[-4:]
                text = text.replace(value, masked)

            elif category == "pan":
                text = text.replace(value, "XXXXX" + value[-4:])

            elif category == "passport":
                text = text.replace(value, "XXXXXXX" + value[-2:])

            elif category == "driving_license":
                text = text.replace(value, "XXXXXX" + value[-4:])

            elif category == "voter_id":
                text = text.replace(value, "XXXXXX" + value[-4:])

            elif category == "bank_account":
                text = text.replace(value, "XXXXXX" + value[-4:])

            elif category == "credit_debit_card":
                clean = re.sub(r"[ -]", "", value)
                masked = "XXXX XXXX XXXX " + clean[-4:]
                text = text.replace(value, masked)

            elif category == "cvv":
                text = text.replace(value, "XXX")

            elif category == "expiry_date":
                text = text.replace(value, "XX/XX")

            elif category == "ifsc":
                text = text.replace(value, "XXXXXX")

            elif category == "phone":
                text = text.replace(value, "XXXXXX" + value[-4:])

            elif category == "email":
                parts = value.split("@")
                if len(parts) == 2:
                    text = text.replace(value, "XXXX@" + parts[1])

            elif category == "dob":
              pattern = re.compile(re.escape(value))
              text = pattern.sub("XX/XX/XXXX", text)

            elif category == "year_of_birth":
                text = text.replace(value, "XXXX")

    return text


# ==========================================================
# IMAGE REDACTION (WITH CONFIDENCE FILTER)
# ==========================================================

def redact_image(image_bytes, pii_results):

    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return image_bytes

    ocr_data = pytesseract.image_to_data(img, output_type=Output.DICT)
    n_boxes = len(ocr_data['text'])

    # Flatten all PII values (digits only cleaned)
    pii_values = []
    for values in pii_results.values():
        for v in values:
            if v:
                pii_values.append(re.sub(r"\s+", "", v))

    height, width, _ = img.shape

    i = 0
    while i < n_boxes:

        word = ocr_data['text'][i].strip()
        conf = int(ocr_data['conf'][i]) if ocr_data['conf'][i] != '-1' else 0

        if conf < 55:
            i += 1
            continue

        clean_word = re.sub(r"\s+", "", word)

        # --------------------------
        # 1️⃣ Direct exact match
        # --------------------------
        if clean_word in pii_values:
            x = ocr_data['left'][i]
            y = ocr_data['top'][i]
            w = ocr_data['width'][i]
            h = ocr_data['height'][i]

            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 0), -1)
            i += 1
            continue

        # --------------------------
        # 2️⃣ Multi-token digit reconstruction
        # --------------------------
        if re.match(r"\d", clean_word):

            combined = clean_word
            coords = [i]

            j = i + 1
            while j < min(i + 6, n_boxes):

                next_word = ocr_data['text'][j].strip()
                next_clean = re.sub(r"\s+", "", next_word)

                if re.match(r"[\d/.-]+", next_clean):
                    combined += next_clean
                    coords.append(j)
                    j += 1
                else:
                    break

            combined_clean = re.sub(r"[^\d]", "", combined)

            # Check against PII
            for pii in pii_values:
                pii_digits = re.sub(r"[^\d]", "", pii)

                if pii_digits and pii_digits in combined_clean:

                    for idx in coords:
                        x = ocr_data['left'][idx]
                        y = ocr_data['top'][idx]
                        w = ocr_data['width'][idx]
                        h = ocr_data['height'][idx]

                        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 0), -1)

                    break

            i = j
            continue

        i += 1

    _, buffer = cv2.imencode(".jpg", img)
    return buffer.tobytes()
# ==========================================================
# PDF REDACTION
# ==========================================================

def redact_pdf(pdf_bytes, poppler_path, pii_results):

    pages = convert_from_bytes(pdf_bytes, poppler_path=poppler_path)
    redacted_pages = []

    for page in pages:
        img_buffer = io.BytesIO()
        page.save(img_buffer, format="JPEG")

        redacted_img_bytes = redact_image(
            img_buffer.getvalue(),
            pii_results
        )

        redacted_img = Image.open(io.BytesIO(redacted_img_bytes))
        redacted_pages.append(redacted_img)

    output_pdf = io.BytesIO()

    redacted_pages[0].save(
        output_pdf,
        save_all=True,
        append_images=redacted_pages[1:],
        format="PDF"
    )

    return output_pdf.getvalue()