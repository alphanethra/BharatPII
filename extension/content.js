let interceptedInput = null;
let interceptedFile = null;

// ==========================================================
// INTERCEPT FILE INPUTS
// ==========================================================
function interceptFileInputs() {

    document.querySelectorAll(
        "input[type=file]"
    ).forEach(input => {

        // avoid duplicate listeners
        if (input.dataset.bharatpii) return;

        input.dataset.bharatpii = "true";

        input.addEventListener(
            "change",
            async function () {

                if (!this.files.length) return;

                interceptedInput = this;
                interceptedFile = this.files[0];

                console.log(
                    "Intercepted File:",
                    interceptedFile
                );

                const formData = new FormData();

                formData.append(
                    "file",
                    interceptedFile
                );

                try {

                    // ==================================================
                    // SCAN API
                    // ==================================================
                    const res = await fetch(
                        "http://127.0.0.1:8000/scan",
                        {
                            method: "POST",
                            body: formData
                        }
                    );

                    const result = await res.json();

                    console.log(
                        "Scan Result:",
                        result
                    );

                    showPopup(result);

                } catch (err) {

                    console.error(
                        "Backend not reachable",
                        err
                    );

                    alert(
                        "Backend connection failed."
                    );
                }
            }
        );
    });
}

// ==========================================================
// POPUP UI
// ==========================================================
function showPopup(result) {

    // remove old popup if exists
    const oldPopup =
        document.getElementById(
            "bharatpii-popup"
        );

    if (oldPopup) {
        oldPopup.remove();
    }

    const risk =
        result.risk_level || "LOW";

    const popup =
        document.createElement("div");

    popup.id = "bharatpii-popup";

    popup.innerHTML = `

        <div class="bharat-box">

            <h2>⚠ PII Detected</h2>

            <div class="risk ${risk.toLowerCase()}">
                Risk Level: ${risk}
            </div>

            <p>
                Do you want to redact
                and replace this file?
            </p>

            <div class="btns">

                <button id="bharat-yes">
                    Yes, Redact
                </button>

                <button id="bharat-no">
                    No, Upload Original
                </button>

            </div>

        </div>
    `;

    document.body.appendChild(popup);

    // ======================================================
    // YES BUTTON
    // ======================================================
    document.getElementById(
        "bharat-yes"
    ).onclick = redactAndReplace;

    // ======================================================
    // NO BUTTON
    // ======================================================
    document.getElementById(
        "bharat-no"
    ).onclick = () => {

        const popup =
            document.getElementById(
                "bharatpii-popup"
            );

        if (popup) {
            popup.remove();
        }

        alert(
            "Original file kept unchanged."
        );
    };

    injectStyles();
}

// ==========================================================
// REDACT + REPLACE FILE
// ==========================================================
async function redactAndReplace() {

    const formData = new FormData();

    formData.append(
        "file",
        interceptedFile
    );

    try {

        // ==================================================
        // REDACTION API
        // ==================================================
        const res = await fetch(
            "http://127.0.0.1:8000/redact",
            {
                method: "POST",
                body: formData
            }
        );

        // backend failure
        if (!res.ok) {

            throw new Error(
                "Backend redaction failed"
            );
        }

        const blob = await res.blob();

        // ==================================================
        // CREATE REDACTED FILE
        // ==================================================
        const redactedFile = new File(
            [blob],
            interceptedFile.name,
            {
                type: blob.type
            }
        );

        console.log(redactedFile);

        // ==================================================
        // REPLACE FILE INPUT
        // ==================================================
        const dt = new DataTransfer();

        dt.items.add(redactedFile);

        interceptedInput.files = dt.files;

        // ==================================================
        // REMOVE POPUP SAFELY
        // ==================================================
        const popup =
            document.getElementById(
                "bharatpii-popup"
            );

        if (popup) {
            popup.remove();
        }

        // ==================================================
        // SUCCESS ALERT
        // ==================================================
        alert(
            "✅ File redacted and replaced successfully"
        );

    } catch(err){

        console.error(
            "Redaction failed",
            err
        );

        alert(
            "Redaction failed."
        );
    }
}

// ==========================================================
// INJECT POPUP CSS
// ==========================================================
function injectStyles() {

    if (
        document.getElementById(
            "bharat-style"
        )
    ) return;

    const style =
        document.createElement("style");

    style.id = "bharat-style";

    style.innerHTML = `

        #bharatpii-popup{

            position: fixed;

            top: 20px;
            right: 20px;

            z-index: 999999;

            font-family: Arial, sans-serif;
        }

        .bharat-box{

            width: 320px;

            background: white;

            border-radius: 16px;

            padding: 20px;

            box-shadow:
                0 6px 18px rgba(0,0,0,0.25);

            border: 1px solid #ddd;
        }

        .bharat-box h2{

            margin-top: 0;

            font-size: 24px;

            color: #222;
        }

        .risk{

            padding: 12px;

            border-radius: 10px;

            margin: 16px 0;

            font-weight: bold;

            text-align: center;

            color: white;

            font-size: 18px;
        }

        .risk.low{
            background: #2ecc71;
        }

        .risk.medium{
            background: #f39c12;
        }

        .risk.high{
            background: #e74c3c;
        }

        p{

            font-size: 15px;

            color: #444;

            line-height: 1.5;
        }

        .btns{

            display: flex;

            gap: 10px;

            margin-top: 18px;
        }

        .btns button{

            flex: 1;

            padding: 12px;

            border: none;

            border-radius: 10px;

            cursor: pointer;

            font-size: 14px;

            font-weight: bold;

            transition: 0.2s ease;
        }

        #bharat-yes{

            background: #111;

            color: white;
        }

        #bharat-yes:hover{

            background: #000;
        }

        #bharat-no{

            background: #e9ecef;

            color: #111;
        }

        #bharat-no:hover{

            background: #dfe3e6;
        }
    `;

    document.head.appendChild(style);
}

// ==========================================================
// INITIALIZE
// ==========================================================
console.log(
    "BharatPII content.js loaded"
);

interceptFileInputs();

// ==========================================================
// OBSERVE DYNAMIC DOM
// ==========================================================
new MutationObserver(
    interceptFileInputs
).observe(
    document.body,
    {
        childList: true,
        subtree: true
    }
);