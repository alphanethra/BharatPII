def calculate_risk(pii_results, face_detected=False):
    """
    Calculate overall risk score based on detected PII.
    """

    score = 0

    # High Sensitivity Identifiers
    if pii_results.get("aadhaar"):
        score += 5
    if pii_results.get("pan"):
        score += 5
    if pii_results.get("passport"):
        score += 5
    if pii_results.get("driving_license"):
        score += 4
    if pii_results.get("voter_id"):
        score += 4

    # Financial
    if pii_results.get("bank_account"):
        score += 4
    if pii_results.get("ifsc"):
        score += 2

    # Medium Sensitivity
    if pii_results.get("phone"):
        score += 2
    if pii_results.get("dob"):
        score += 2

    # Low Sensitivity
    if pii_results.get("email"):
        score += 1

    # Biometric Factor
    if face_detected:
        score += 5

    # Risk Classification
    if score >= 12:
        return "HIGH"
    elif score >= 5:
        return "MEDIUM"
    else:
        return "LOW"