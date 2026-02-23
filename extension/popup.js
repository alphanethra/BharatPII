document.getElementById("scanBtn").addEventListener("click", async () => {

    const file = document.getElementById("fileInput").files[0];
    const output = document.getElementById("output");

    if (!file) {
        alert("Please select a file");
        return;
    }

    output.textContent = "Scanning... Please wait...";

    try {
        const formData = new FormData();
        formData.append("file", file);

        const response = await fetch("http://127.0.0.1:8000/scan", {
            method: "POST",
            body: formData
        });

        const result = await response.json();

        console.log("Full OCR Response:", result);

        // Safe fallback handling
        let pii = result.pii_detected || {
            aadhaar: [],
            pan: [],
            phone: [],
            email: [],
            credit_card: []
        };

        let riskLevel = result.risk_level || "UNKNOWN";

        let summary =
            "Scan Complete ✅\n\n" +
            "Risk Level: " + riskLevel + "\n\n" +
            "Detected PII:\n" +
            "--------------------------------\n" +
            "Aadhaar: " + pii.aadhaar.length + "\n" +
            "PAN: " + pii.pan.length + "\n" +
            "Phone: " + pii.phone.length + "\n" +
            "Email: " + pii.email.length + "\n" +
            "Credit Card: " + pii.credit_card.length + "\n\n" +
            "--------------------------------\n\n" +
            "Extracted Text:\n\n" +
            (result.extracted_text || "No text extracted.");

        output.textContent = summary;

    } catch (error) {
        console.error("Error:", error);
        output.textContent = "Error connecting to backend.";
    }
});