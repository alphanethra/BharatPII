import re

def detect_pii(text):
    results = {}

    # Aadhaar (12 digits, optional spaces)
    aadhaar_pattern = r"\b\d{4}\s?\d{4}\s?\d{4}\b"
    results["aadhaar"] = re.findall(aadhaar_pattern, text)

    # PAN (ABCDE1234F format)
    pan_pattern = r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"
    results["pan"] = re.findall(pan_pattern, text)

    # Phone numbers (Indian)
    phone_pattern = r"\b[6-9]\d{9}\b"
    results["phone"] = re.findall(phone_pattern, text)

    # Email
    email_pattern = r"\b[\w\.-]+@[\w\.-]+\.\w+\b"
    results["email"] = re.findall(email_pattern, text)

    # Credit Card (13–16 digits)
    cc_pattern = r"\b\d{13,16}\b"
    results["credit_card"] = re.findall(cc_pattern, text)

    return results

def calculate_risk(results):
    score = 0

    if results["aadhaar"]:
        score += 3
    if results["pan"]:
        score += 3
    if results["credit_card"]:
        score += 4
    if results["phone"]:
        score += 1
    if results["email"]:
        score += 1

    if score >= 6:
        return "HIGH"
    elif score >= 3:
        return "MEDIUM"
    else:
        return "LOW"