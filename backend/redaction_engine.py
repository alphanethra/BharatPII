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
def redact_image(image_bytes, pii_results, processed_bytes=None):

    import re
    import cv2
    import numpy as np
    import pytesseract
    from pytesseract import Output

    nparr_orig = np.frombuffer(image_bytes, np.uint8)
    img_orig = cv2.imdecode(nparr_orig, cv2.IMREAD_COLOR)
    
    # Draw on the processed (blurred) image if provided, otherwise on original
    if processed_bytes:
        nparr_draw = np.frombuffer(processed_bytes, np.uint8)
        img_draw = cv2.imdecode(nparr_draw, cv2.IMREAD_COLOR)
    else:
        img_draw = img_orig.copy()

    if img_orig is None or img_draw is None:
        return processed_bytes or image_bytes

    ocr_data = pytesseract.image_to_data(img_orig, output_type=Output.DICT)
    n_boxes = len(ocr_data['text'])

    # -----------------------------
    # Normalize detected PII
    # -----------------------------
    pii_values = []

    for values in pii_results.values():
        for v in values:
            if v:
                normalized = re.sub(r"[^\dA-Z]", "", v.upper())
                if len(normalized) >= 8:
                    pii_values.append(normalized)

    i = 0

    while i < n_boxes:

        word = ocr_data['text'][i].strip()
        conf = int(ocr_data['conf'][i]) if ocr_data['conf'][i] != '-1' else 0

        if conf < 55:
            i += 1
            continue

        clean_word = re.sub(r"[^\dA-Z]", "", word.upper())

        if not clean_word:
            i += 1
            continue

        # ----------------------------------------
        # 1️⃣ Try Exact Match (Safe)
        # ----------------------------------------
        for pii in pii_values:
            if clean_word == pii:

                x = ocr_data['left'][i]
                y = ocr_data['top'][i]
                w = ocr_data['width'][i]
                h = ocr_data['height'][i]

                if w >= 35 and h >= 18:
                    cv2.rectangle(img_draw, (x, y), (x + w, y + h), (0, 0, 0), -1)

                break
        else:
            # ----------------------------------------
            # 2️⃣ Reconstruct multi-token group
            # ----------------------------------------
            combined = clean_word
            coords = [i]

            j = i + 1
            while j < min(i + 6, n_boxes):

                next_word = ocr_data['text'][j].strip()
                next_clean = re.sub(r"[^\dA-Z]", "", next_word.upper())

                if next_clean:
                    combined += next_clean
                    coords.append(j)
                    j += 1
                else:
                    break

            combined_clean = re.sub(r"[^\dA-Z]", "", combined)

            # ----------------------------------------
            # 3️⃣ Safe containment match
            # ----------------------------------------
            for pii in pii_values:

                # Require strong length
                if len(combined_clean) >= len(pii) and pii in combined_clean:

                    xs, ys, xe, ye = [], [], [], []
                    match_start = combined_clean.find(pii)
                    match_end = match_start + len(pii)
                    
                    pos = 0
                    for idx in coords:
                        token_clean = re.sub(r"[^\dA-Z]", "", ocr_data['text'][idx].strip().upper())
                        token_len = len(token_clean)
                        
                        # Only include token bounds if it overlaps with the matched PII text
                        if pos < match_end and (pos + token_len) > match_start:
                            x = ocr_data['left'][idx]
                            y = ocr_data['top'][idx]
                            w = ocr_data['width'][idx]
                            h = ocr_data['height'][idx]

                            if w >= 30 and h >= 15:
                                xs.append(x)
                                ys.append(y)
                                xe.append(x + w)
                                ye.append(y + h)
                                
                        pos += token_len

                    if xs:
                        start_x = min(xs)
                        start_y = min(ys)
                        end_x = max(xe)
                        end_y = max(ye)

                        cv2.rectangle(
                            img_draw,
                            (start_x, start_y),
                            (end_x, end_y),
                            (0, 0, 0),
                            -1
                        )

                    break

        i += 1

    _, buffer = cv2.imencode(".jpg", img_draw)
    return buffer.tobytes()
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