from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import io

from ocr import extract_text
from pdf_handler import ocr_scanned_pdf
from pii_detector import detect_pii
from risk_engine import calculate_risk
from face_detector import blur_faces_image, blur_faces_pdf
from redaction_engine import redact_text, redact_image, redact_pdf
from crypto_engine import encrypt_bytes, decrypt_bytes, hash_pii_results
from signature_detector import detect_and_blur_signature

app = FastAPI()

# ==========================================================
# CORS
# ==========================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================================
# MAIN SCAN API
# ==========================================================
@app.post("/scan")
async def scan_file(
    file: UploadFile = File(...),
    redact: bool = False
):

    # ======================================================
    # READ FILE
    # ======================================================
    file_bytes = await file.read()

    filename = file.filename.lower()

    poppler_path = (
        r"C:\Users\karth\Downloads\poppler\Library\bin"
    )

    # ======================================================
    # ENCRYPTION
    # ======================================================
    encrypted_file = encrypt_bytes(file_bytes)

    file_bytes = decrypt_bytes(encrypted_file)

    # ======================================================
    # OCR EXTRACTION
    # ======================================================
    if filename.endswith(".pdf"):

        text = ocr_scanned_pdf(file_bytes)

    else:

        text = extract_text(file_bytes)

    print("Extracted Text:", text)

    # ======================================================
    # PII DETECTION
    # ======================================================
    pii_results = detect_pii(text)

    # ======================================================
    # HASHED AUDIT LOG
    # ======================================================
    audit_log = hash_pii_results(pii_results)

    # ======================================================
    # FACE DETECTION
    # ======================================================
    face_detected = False

    processed_file = file_bytes

    try:

        if filename.endswith(".pdf"):

            processed_file, face_count = blur_faces_pdf(
                file_bytes,
                poppler_path
            )

            face_detected = face_count > 0

        elif filename.endswith(
            (".jpg", ".jpeg", ".png")
        ):

            processed_file, face_count = blur_faces_image(
                file_bytes
            )

            face_detected = face_count > 0

    except Exception as e:

        print("Face detection error:", e)

    # ======================================================
    # SIGNATURE BLUR
    # ======================================================
    processed_file, signature_detected = (
        detect_and_blur_signature(
            processed_file
        )
    )

    # ======================================================
    # RISK ENGINE
    # ======================================================
    risk_level = calculate_risk(
        pii_results,
        face_detected
    )

    # ======================================================
    # REDACTION MODE
    # ======================================================
    if redact:

        # --------------------------------------------------
        # TEXT FILE
        # --------------------------------------------------
        if filename.endswith(".txt"):

            redacted_text = redact_text(
                text,
                pii_results
            )

            return {
                "redacted_text": redacted_text,
                "risk_level": risk_level,
                "pii_detected": pii_results
            }

        # --------------------------------------------------
        # IMAGE FILE
        # --------------------------------------------------
        elif filename.endswith(
            (".jpg", ".jpeg", ".png")
        ):

            redacted_image = redact_image(
                processed_file,
                pii_results
            )

            return StreamingResponse(
                io.BytesIO(redacted_image),
                media_type="image/jpeg"
            )

        # --------------------------------------------------
        # PDF FILE
        # --------------------------------------------------
        elif filename.endswith(".pdf"):

            redacted_pdf = redact_pdf(
                processed_file,
                poppler_path,
                pii_results
            )

            return StreamingResponse(
                io.BytesIO(redacted_pdf),
                media_type="application/pdf",
                headers={
                    "Content-Disposition":
                    "attachment; filename=redacted.pdf"
                }
            )

    # ======================================================
    # NORMAL SCAN RESPONSE
    # ======================================================
    return {

        "extracted_text": text,

        "pii_detected": pii_results,

        "pii_audit_hashes": audit_log,

        "risk_level": risk_level,

        "signature_detected": signature_detected,

        "face_detected": face_detected
    }

# ==========================================================
# SEPARATE REDACT ENDPOINT
# ==========================================================
@app.post("/redact")
async def redact_endpoint(
    file: UploadFile = File(...)
):

    file_bytes = await file.read()

    filename = file.filename.lower()

    poppler_path = (
        r"C:\Users\karth\Downloads\poppler\Library\bin"
    )

    # ======================================================
    # OCR
    # ======================================================
    if filename.endswith(".pdf"):

        text = ocr_scanned_pdf(file_bytes)

    else:

        text = extract_text(file_bytes)

    # ======================================================
    # PII DETECTION
    # ======================================================
    pii_results = detect_pii(text)

    processed_file = file_bytes

    # ======================================================
    # FACE BLUR
    # ======================================================
    try:

        if filename.endswith(".pdf"):

            processed_file, _ = blur_faces_pdf(
                file_bytes,
                poppler_path
            )

        elif filename.endswith(
            (".jpg", ".jpeg", ".png")
        ):

            processed_file, _ = blur_faces_image(
                file_bytes
            )

    except Exception as e:

        print("Face blur error:", e)

    # ======================================================
    # SIGNATURE BLUR
    # ======================================================
    processed_file, _ = (
        detect_and_blur_signature(
            processed_file
        )
    )

    # ======================================================
    # TEXT REDACTION
    # ======================================================
    if filename.endswith(".txt"):

        redacted_text = redact_text(
            text,
            pii_results
        )

        return {
            "redacted_text": redacted_text
        }

    # ======================================================
    # IMAGE REDACTION
    # ======================================================
    elif filename.endswith(
        (".jpg", ".jpeg", ".png")
    ):

        redacted_image = redact_image(
            processed_file,
            pii_results
        )

        return StreamingResponse(
            io.BytesIO(redacted_image),
            media_type="image/jpeg"
        )

    # ======================================================
    # PDF REDACTION
    # ======================================================
    elif filename.endswith(".pdf"):

        redacted_pdf = redact_pdf(
            processed_file,
            poppler_path,
            pii_results
        )

        return StreamingResponse(
            io.BytesIO(redacted_pdf),
            media_type="application/pdf",
            headers={
                "Content-Disposition":
                "attachment; filename=redacted.pdf"
            }
        )

    # ======================================================
    # UNSUPPORTED FILE
    # ======================================================
    return {
        "error": "Unsupported file type"
    }