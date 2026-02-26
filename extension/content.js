document.addEventListener("change", async function (event) {

    const input = event.target;

    if (input.type === "file" && input.files.length > 0) {

        const file = input.files[0];

        const formData = new FormData();
        formData.append("file", file);

        // STEP 1: Detect PII (Normal Scan)
        const response = await fetch("http://127.0.0.1:8000/scan", {
            method: "POST",
            body: formData
        });

        const result = await response.json();

        if (result.risk_level === "LOW") {
            return; // allow upload normally
        }

        // STEP 2: Show Warning Popup
        const userChoice = confirm(
            `⚠ Sensitive PII Detected!\n\nRisk Level: ${result.risk_level}\n\nDo you want to redact before upload?`
        );

        if (!userChoice) {
            input.value = ""; // Cancel upload
            return;
        }

        // STEP 3: Call Redaction Endpoint
        const redactResponse = await fetch("http://127.0.0.1:8000/scan?redact=true", {
            method: "POST",
            body: formData
        });

        const blob = await redactResponse.blob();

        // STEP 4: Replace File Using DataTransfer
        const sanitizedFile = new File([blob], file.name, {
            type: blob.type
        });

        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(sanitizedFile);

        input.files = dataTransfer.files;

        alert("✅ File redacted and replaced successfully!");

    }
});