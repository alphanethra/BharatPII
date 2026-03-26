import cv2
import numpy as np
from pii_detector import detect_pii
from redaction_engine import redact_image
from signature_detector import detect_and_blur_signature
from ocr import extract_text

def test_engine():
    # Read test image
    with open("test_image.jpeg", "rb") as f:
        img_bytes = f.read()

    # Detect PII
    text = extract_text(img_bytes)
    pii_results = detect_pii(text)
    print("Detected PII:", pii_results)

    # Redact PII
    redacted_bytes = redact_image(img_bytes, pii_results)

    # Redact Signature
    final_bytes, signature_found = detect_and_blur_signature(redacted_bytes)
    print("Signature Found:", signature_found)

    # Save output
    with open("redacted_output.jpeg", "wb") as f:
        f.write(final_bytes)
    print("Saved to redacted_output.jpeg")

if __name__ == "__main__":
    test_engine()
