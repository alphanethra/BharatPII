import re

import re

def detect_pii(text):
    """
    Detect various types of Personally Identifiable Information (PII)
    from extracted OCR text.
    """

    pii_data = {
        # Identity Numbers
        "aadhaar": list(set(re.findall(r"\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b", text))),
        "pan": list(set(re.findall(r"\b[A-Za-z]{5}[0-9]{4}[A-Za-z]\b", text))),
        "voter_id": list(set(re.findall(r"\b[A-Z]{3}[0-9]{7}\b", text))),
        "passport": list(set(re.findall(r"\b[A-Z][0-9]{7}\b", text))),
        "driving_license": list(set(re.findall(r"\b[A-Z]{2}\d{2}\d{4}\d{7}\b", text))),

        # Contact Information
        "phone": list(set(re.findall(r"\b[6-9]\d{9}\b", text))),
        "email": list(set(re.findall(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", text))),

        # Financial
        "bank_account": list(set(re.findall(r"\b\d{9,18}\b", text))),
        "ifsc": list(set(re.findall(r"\b[A-Z]{4}0[A-Z0-9]{6}\b", text))),

        # Personal Details
        "dob": list(set(re.findall(r"\b\d{2}/\d{2}/\d{4}\b", text)))
    }

    return pii_data