from fastapi.responses import StreamingResponse
import io
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from ocr import extract_text
from pdf_handler import ocr_scanned_pdf
from pii_detector import detect_pii
from risk_engine import calculate_risk
from face_detector import blur_faces_image, blur_faces_pdf
from redactor import mask_sensitive_text, redact_pdf, blur_entire_image
from pdf_redactor import extract_text_from_pdf, extract_text_from_image

app = FastAPI()

# Allow Chrome extension access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/scan")
async def scan_file(file: UploadFile = File(...), redact: bool = False):

    file_bytes = await file.read()
    filename = file.filename.lower()

    # ===============================
    # 1️⃣ OCR TEXT EXTRACTION
    # ===============================
    if filename.endswith(".pdf"):
        text = ocr_scanned_pdf(file_bytes)
    else:
        text = extract_text(file_bytes)

    # ===============================
    # 2️⃣ PII DETECTION
    # ===============================
    pii_results = detect_pii(text)

    # ===============================
    # 3️⃣ TEXT REDACTION (Masking)
    # ===============================
    sanitized_text = text
    if redact:
        sanitized_text = mask_sensitive_text(text, pii_results)

    # ===============================
    # 4️⃣ FACE DETECTION + BLUR
    # ===============================
    poppler_path = r"C:\Users\karth\Downloads\poppler\Library\bin"

    face_detected = False
    processed_file = file_bytes

    try:
        if filename.endswith(".pdf"):
            processed_file, face_count = blur_faces_pdf(file_bytes, poppler_path)
            face_detected = face_count > 0

            if redact:
                processed_file = redact_pdf(processed_file, poppler_path)

        elif filename.endswith((".jpg", ".jpeg", ".png")):
            processed_file, face_count = blur_faces_image(file_bytes)
            face_detected = face_count > 0

            if redact:
                processed_file = blur_entire_image(processed_file)

    except Exception as e:
        print("Face detection error:", e)

    # ===============================
    # 5️⃣ RISK CALCULATION
    # ===============================
    risk_level = calculate_risk(
        pii_results,
        face_detected=face_detected
    )

    # ===============================
    # 6️⃣ RESPONSE
    # ===============================
    if redact:
        return StreamingResponse(
        io.BytesIO(processed_file),
        media_type=file.content_type,
        headers={
            "Content-Disposition": f"attachment; filename=redacted_{file.filename}"
        }
    )

    return {
        "extracted_text": text,
        "sanitized_text": sanitized_text if redact else None,
        "pii_detected": pii_results,
        "risk_level": risk_level,
        "face_detected": face_detected,
        "redaction_applied": redact
    }
    