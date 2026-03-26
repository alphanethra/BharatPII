import re


# ==========================================================
# Luhn Algorithm (Credit/Debit Card Validation)
# ==========================================================

def luhn_check(card_number):
    digits = [int(d) for d in card_number]
    checksum = 0
    parity = len(digits) % 2

    for i, digit in enumerate(digits):
        if i % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit

    return checksum % 10 == 0


# ==========================================================
# MAIN PII DETECTION
# ==========================================================

def detect_pii(text):

    # --------------------------
    # Normalize OCR text
    # --------------------------
    text_clean = text.replace("\n", " ")
    text_clean = re.sub(r"\s+", " ", text_clean)

    # --------------------------
    # Aadhaar (12 digits)
    # --------------------------
    aadhaar_raw = re.findall(r"\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b", text_clean)
    aadhaar = list(set([a.replace(" ", "") for a in aadhaar_raw]))

    # --------------------------
    # PAN
    # --------------------------
    pan = list(set(re.findall(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", text_clean)))

    # --------------------------
    # Passport
    # --------------------------
    passport = list(set(re.findall(r"\b[A-Z][0-9]{7}\b", text_clean)))

    # --------------------------
    # Driving License
    # --------------------------
    driving_license_raw = re.findall(
    r"\b[A-Z]{2}\d{2}\s?\d{4}\d{7}\b",
    text_clean
)

    driving_license = list(set(
    dl.replace(" ", "") for dl in driving_license_raw
))

    # --------------------------
    # Voter ID
    # --------------------------
    voter_id = list(set(
        re.findall(r"\b[A-Z]{3}[0-9]{7}\b", text_clean)
    ))

    # --------------------------
    # IFSC
    # --------------------------
    ifsc = list(set(
        re.findall(r"\b[A-Z]{4}0[A-Z0-9]{6}\b", text_clean)
    ))

    # --------------------------
    # DOB (Robust)
    # --------------------------
    dob = list(set(
        re.findall(
            r"\d{1,2}\s*[-/\.]\s*\d{1,2}\s*[-/\.]\s*\d{4}",
            text_clean
        )
    ))
    dob = [re.sub(r"\s+", "", d) for d in dob]

    # --------------------------
    # Phone
    # --------------------------
    phone = list(set(
        re.findall(r"\b[6-9]\d{9}\b", text_clean)
    ))

    # --------------------------
    # Email
    # --------------------------
    email = list(set(
        re.findall(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", text_clean)
    ))

    # --------------------------
    # Bank Account (Context-aware)
    # --------------------------
    bank_account = []
    if "account" in text_clean.lower():
        potential_accounts = re.findall(r"\b\d{11,16}\b", text_clean)

        potential_accounts = [
            acc for acc in potential_accounts
            if acc not in aadhaar
        ]

        bank_account = list(set(potential_accounts))

    # --------------------------
    # VID (Virtual ID - 16 digits on Aadhaar)
    # --------------------------
    vids_to_ignore = []
    vid_raw = re.findall(r"\bVID\s*[:\-]?\s*\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b", text_clean, re.IGNORECASE)
    for v in vid_raw:
        vids_to_ignore.append(re.sub(r"[^\d]", "", v))

    # --------------------------
    # Credit / Debit Card (Luhn validated)
    # --------------------------
    credit_debit_card = []

    # Remove spaces & hyphens before checking
    text_digits_only = re.sub(r"[^\d]", "", text_clean)

    # Extract 13–19 digit sequences
    potential_cards = re.findall(r"\d{13,19}", text_digits_only)

    for num in potential_cards:
        if num in vids_to_ignore:
            continue
        if luhn_check(num):
            credit_debit_card.append(num)

    credit_debit_card = list(set(credit_debit_card))

    # --------------------------
    # CVV (only if card exists)
    # --------------------------
    cvv = []
    if credit_debit_card:
        cvv = list(set(re.findall(r"\b\d{3,4}\b", text_clean)))

    # --------------------------
    # Expiry Date (MM/YY or MM/YYYY)
    # --------------------------
    expiry_date = list(set(
        re.findall(r"\b(0[1-9]|1[0-2])\s*/\s*\d{2,4}\b", text_clean)
    ))

    # --------------------------
    # Final PII Dictionary
    # --------------------------
    pii_data = {
        "aadhaar": aadhaar,
        "pan": pan,
        "passport": passport,
        "driving_license": driving_license,
        "voter_id": voter_id,
        "ifsc": ifsc,
        "dob": dob,
        "phone": phone,
        "email": email,
        "bank_account": bank_account,
        "credit_debit_card": credit_debit_card,
        "cvv": cvv,
        "expiry_date": expiry_date
    }

    return pii_data