from fastapi import FastAPI, UploadFile, File
from ocr import extract_text
from pdf_handler import ocr_scanned_pdf
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()
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

    if file.filename.lower().endswith(".pdf"):
        text = ocr_scanned_pdf(file_bytes)
    else:
        text = extract_text(file_bytes)

    print("Extracted Text:\n", text)

    return {"extracted_text": text}
