let interceptedInput = null;
let interceptedFile = null;

function interceptFileInputs() {

    document.querySelectorAll("input[type=file]").forEach(input => {

        if (input.dataset.bharatpii) return;
        input.dataset.bharatpii = "true";

        input.addEventListener("change", async function () {

            if (!this.files.length) return;

            interceptedInput = this;
            interceptedFile = this.files[0];

            const formData = new FormData();
            formData.append("file", interceptedFile);

            try {

                const res = await fetch("http://127.0.0.1:8000/scan", {
                    method: "POST",
                    body: formData
                });

                const result = await res.json();

                showPopup(result);

            } catch (err) {
                console.error("Backend not reachable", err);
            }
        });
    });
}

function showPopup(result) {

    const risk = result.risk_level;
    const pii = result.pii_detected;

    const popup = document.createElement("div");
    popup.id = "bharatpii-popup";

    popup.innerHTML = `
        <div class="box">
            <h3>BharatPII Shield</h3>

            <div class="risk ${risk.toLowerCase()}">
                Risk Level: ${risk}
            </div>

            <div class="pii">
                ${formatPII(pii)}
            </div>

            <button id="yes">Redact & Upload</button>
            <button id="no">Upload Original</button>
        </div>
    `;

    document.body.appendChild(popup);

    document.getElementById("yes").onclick = redactAndReplace;
    document.getElementById("no").onclick = () => popup.remove();
}

function formatPII(pii){

    let html = "<b>Detected PII:</b><br>";

    Object.keys(pii).forEach(k => {
        if (pii[k].length > 0)
            html += `${k}: ${pii[k].length}<br>`;
    });

    return html;
}

async function redactAndReplace(){

    const formData = new FormData();
    formData.append("file", interceptedFile);

    try {

        const res = await fetch("http://127.0.0.1:8000/redact", {
            method: "POST",
            body: formData
        });

        const blob = await res.blob();

        const redactedFile = new File(
            [blob],
            interceptedFile.name,
            { type: blob.type }
        );

        const dt = new DataTransfer();
        dt.items.add(redactedFile);

        interceptedInput.files = dt.files;

        document.getElementById("bharatpii-popup").remove();

        alert("File replaced successfully ✅");

    } catch(err){
        console.error("Redaction failed", err);
    }
}

interceptFileInputs();

new MutationObserver(interceptFileInputs).observe(
    document.body,
    { childList:true, subtree:true }
);