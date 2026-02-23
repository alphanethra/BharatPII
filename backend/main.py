from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from ocr import extract_text
from pdf_handler import ocr_scanned_pdf
from pii_detector import detect_pii
from risk_engine import calculate_risk
from face_detector import blur_faces_image, blur_faces_pdf

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
async def scan_file(file: UploadFile = File(...)):
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
    # 3️⃣ FACE DETECTION + BLUR
    # ===============================
    poppler_path = r"C:\Users\karth\Downloads\poppler\Library\bin"  # Update if needed

    face_detected = False
    blurred_file = file_bytes

    try:
        if filename.endswith(".pdf"):
            blurred_file, face_count = blur_faces_pdf(file_bytes, poppler_path)
            face_detected = face_count > 0

        elif filename.endswith((".jpg", ".jpeg", ".png")):
            blurred_file, face_count = blur_faces_image(file_bytes)
            face_detected = face_count > 0

    except Exception as e:
        print("Face detection error:", e)

    # ===============================
    # 4️⃣ RISK CALCULATION
    # ===============================
    risk_level = calculate_risk(
        pii_results,
        face_detected=face_detected
    )

    # ===============================
    # 5️⃣ RESPONSE
    # ===============================
    return {
        "extracted_text": text,
        "pii_detected": pii_results,
        "risk_level": risk_level,
        "face_detected": face_detected
    }