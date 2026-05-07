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

    import re
    import cv2
    import numpy as np
    import pytesseract
    from pytesseract import Output

    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return image_bytes

    ocr_data = pytesseract.image_to_data(
        img,
        output_type=Output.DICT
    )

    n_boxes = len(ocr_data['text'])

    # ==========================================================
    # BUILD PII LIST
    # ==========================================================
    pii_values = []

    for category, values in pii_results.items():

        if category not in [
            "aadhaar",
            "pan",
            "driving_license",
            "phone",
            "dob"
        ]:
            continue

        for v in values:

            if not v:
                continue

            norm = re.sub(
                r"[^\dA-Z]",
                "",
                str(v).upper()
            )

            pii_values.append((norm, category, v))

    # ==========================================================
    # MASK FORMAT
    # ==========================================================
    def mask_value(value, category):

        if category == "aadhaar":
            return "XXXX XXXX " + value[-4:]

        elif category == "pan":
            return "XXXXXX" + value[-4:]

        elif category == "driving_license":
            return "XXXX XXXX " + value[-4:]

        elif category == "phone":
            return "X X X X X X" + value[-4:]

        elif category == "dob":
            year = value.split("/")[-1]
            return "XX/XX/" + year

        return "XXXX"

    # ==========================================================
    # OCR ITERATION
    # ==========================================================
    i = 0

    while i < n_boxes:

        word = ocr_data['text'][i].strip()

        conf = int(
            ocr_data['conf'][i]
        ) if ocr_data['conf'][i] != '-1' else 0

        if conf < 50:
            i += 1
            continue

        clean = re.sub(
            r"[^\dA-Z]",
            "",
            word.upper()
        )

        if not clean:
            i += 1
            continue

        # ==========================================================
        # MERGE OCR TOKENS
        # ==========================================================
        combined = clean
        coords = [i]

        j = i + 1

        while j < min(i + 6, n_boxes):

            nxt = ocr_data['text'][j].strip()

            nxt_clean = re.sub(
                r"[^\dA-Z]",
                "",
                nxt.upper()
            )

            if nxt_clean:

                combined += nxt_clean
                coords.append(j)
                j += 1

            else:
                break

        # ==========================================================
        # MATCH PII
        # ==========================================================
        matched = False

        for pii_norm, category, original in pii_values:

            if len(pii_norm) < 8:
                continue

            # ------------------------------------------------------
            # PAN STRICT MATCH
            # ------------------------------------------------------
            if category == "pan":

                if pii_norm != combined[:len(pii_norm)]:
                    continue

            # ------------------------------------------------------
            # DRIVING LICENSE
            # ------------------------------------------------------
            elif category == "driving_license":

                if pii_norm not in combined:
                    continue

            # ------------------------------------------------------
            # DOB
            # ------------------------------------------------------
            elif category == "dob":

                # Skip DOB masking inside DL
                if (
                    "driving_license" in pii_results
                    and pii_results["driving_license"]
                ):
                    continue

                if original.replace("/", "") not in combined:
                    continue

            # ------------------------------------------------------
            # AADHAAR / PHONE
            # ------------------------------------------------------
            else:

                if combined[-8:] != pii_norm[-8:]:
                    continue

            matched = True

            # ======================================================
            # REGION COORDINATES
            # ======================================================
            xs, ys, xe, ye = [], [], [], []

            for idx in coords:

                x = ocr_data['left'][idx]
                y = ocr_data['top'][idx]
                w = ocr_data['width'][idx]
                h = ocr_data['height'][idx]

                xs.append(x)
                ys.append(y)
                xe.append(x + w)
                ye.append(y + h)

            start_x = min(xs)
            start_y = min(ys)

            end_x = max(xe)
            end_y = max(ye)

            # Extra width for PAN final character
            if category == "pan":
                end_x += 20

            masked = mask_value(original, category)

            # ======================================================
            # FONT SETTINGS
            # ======================================================
            height = end_y - start_y

            font = cv2.FONT_HERSHEY_SIMPLEX

            font_scale = max(
                0.7,
                height / 28
            )
            if category == "phone":
              thickness = 4
            else:
              thickness = 2
            

            (tw, th), _ = cv2.getTextSize(
                masked,
                font,
                font_scale,
                thickness
            )

            # ======================================================
            # BLACK BOX
            # ======================================================
            padding_x = 2
            padding_y = 2

            # PHONE SPECIAL HANDLING
            if category == "phone":

                x1 = start_x - 35
                x2 = start_x + tw + 90

            else:

                x1 = start_x - padding_x
                x2 = start_x + tw + 25

            y1 = start_y - padding_y
            y2 = start_y + th + padding_y + 6

            cv2.rectangle(
                img,
                (x1, y1),
                (x2, y2),
                (0, 0, 0),
                -1
            )

            # ======================================================
            # WHITE TEXT
            # ======================================================
            text_y = start_y + th - 2

            cv2.putText(
                img,
                masked,
                (start_x, text_y),
                font,
                font_scale,
                (255, 255, 255),
                thickness,
                cv2.LINE_AA
            )

            break

        # ==========================================================
        # SKIP DUPLICATE MASKING
        # ==========================================================
        if matched:
            i += len(coords)
        else:
            i += 1

    _, buffer = cv2.imencode(".jpg", img)

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