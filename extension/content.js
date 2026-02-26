function interceptFileInputs() {

    const inputs = document.querySelectorAll("input[type='file']");

    inputs.forEach(input => {

        if (!input.dataset.bharatpii) {

            input.dataset.bharatpii = "true";

            input.addEventListener("change", async function () {

                if (!this.files.length) return;

                const file = this.files[0];

                console.log("Intercepted:", file.name);

                const formData = new FormData();
                formData.append("file", file);

                try {

                    const response = await fetch("http://localhost:8000/scan?redact=true", {
                        method: "POST",
                        body: formData
                    });

                    const blob = await response.blob();

                    const redactedFile = new File([blob], file.name, {
                        type: blob.type
                    });

                    const dataTransfer = new DataTransfer();
                    dataTransfer.items.add(redactedFile);

                    this.files = dataTransfer.files;

                    alert("BharatPII Shield: File Redacted ✅");

                } catch (err) {
                    console.error("BharatPII Error:", err);
                }
            });
        }
    });
}

// Run initially
interceptFileInputs();

// Run whenever DOM updates (important for Google Forms)
const observer = new MutationObserver(() => {
    interceptFileInputs();
});

observer.observe(document.body, {
    childList: true,
    subtree: true
});