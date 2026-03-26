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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/scan")
async def scan_file(file: UploadFile = File(...), redact: bool = False):

    # ==========================================
    # 0️⃣ READ FILE
    # ==========================================
    file_bytes = await file.read()
    filename = file.filename.lower()
    poppler_path = r"C:\Users\karth\Downloads\poppler\Library\bin"

    # ==========================================
    # 🔐 AES SECURE PROCESSING (CORRECT POSITION)
    # ==========================================
    encrypted_file = encrypt_bytes(file_bytes)
    file_bytes = decrypt_bytes(encrypted_file)

    # ==========================================
    # 1️⃣ OCR TEXT EXTRACTION
    # ==========================================
    if filename.endswith(".pdf"):
        text = ocr_scanned_pdf(file_bytes)
    else:
        text = extract_text(file_bytes)
    
    print("Extracted Text:", text)
    # ==========================================
    # 2️⃣ PII DETECTION
    # ==========================================
    pii_results = detect_pii(text)

    # 🔐 HASHED AUDIT LOG
    audit_log = hash_pii_results(pii_results)

    # ==========================================
    # 3️⃣ FACE DETECTION + BLUR
    # ==========================================
    face_detected = False
    processed_file = file_bytes

    try:
        if filename.endswith(".pdf"):
            processed_file, face_count = blur_faces_pdf(file_bytes, poppler_path)
            face_detected = face_count > 0

        elif filename.endswith((".jpg", ".jpeg", ".png")):
            processed_file, face_count = blur_faces_image(file_bytes)
            face_detected = face_count > 0

    except Exception as e:
        print("Face detection error:", e)
    
    processed_file, signature_detected = detect_and_blur_signature(processed_file)
    # ==========================================
    # 4️⃣ RISK CALCULATION
    # ==========================================
    risk_level = calculate_risk(pii_results, face_detected)

    # ==========================================
    # 5️⃣ APPLY REDACTION IF REQUESTED
    # ==========================================
    if redact:

        if filename.endswith(".txt"):
            redacted_text = redact_text(text, pii_results)
            return {
                "redacted_text": redacted_text,
                "risk_level": risk_level,
                "pii_detected": pii_results
            }

        elif filename.endswith((".jpg", ".jpeg", ".png")):
            redacted_image = redact_image(file_bytes, pii_results, processed_bytes=processed_file)
            return StreamingResponse(
                io.BytesIO(redacted_image),
                media_type="image/jpeg"
            )

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
              "Content-Disposition": "attachment; filename=redacted.pdf"
           }   
)
   
    # ==========================================
    # 6️⃣ NORMAL RESPONSE
    # ==========================================
    return {
        "extracted_text": text,
        "pii_detected": pii_results,
        "pii_audit_hashes": audit_log,
        "risk_level": risk_level,
        "signature_detected": signature_detected,
        "face_detected": face_detected
    }