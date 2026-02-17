document.getElementById("scanBtn").addEventListener("click", async () => {

    const file = document.getElementById("fileInput").files[0];
    const output = document.getElementById("output");

    if (!file) {
        alert("Please select a file");
        return;
    }

    output.textContent = "Scanning... Please wait.";

    try {
        const formData = new FormData();
        formData.append("file", file);

        const response = await fetch("http://127.0.0.1:8000/scan", {
            method: "POST",
            body: formData
        });

        const result = await response.json();

        console.log("Full OCR Response:", result);

        // IMPORTANT: use textContent not innerText
        output.textContent = result.extracted_text;

    } catch (error) {
        console.error("Error:", error);
        output.textContent = "Error connecting to backend.";
    }
});
