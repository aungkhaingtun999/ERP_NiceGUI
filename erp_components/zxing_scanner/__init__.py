import streamlit.components.v1 as components
import uuid

def zxing_scanner(key=None, height=420):
    component_key = key or f"zxing-{uuid.uuid4()}"

    html_code = """
    <div style="text-align:center">
        <video id="video" width="100%" autoplay playsinline
               style="border-radius:12px;border:1px solid #ddd;"></video>
        <p id="status">📷 Camera starting...</p>
    </div>

    <script src="https://unpkg.com/@zxing/library@latest"></script>
    <script>
    const codeReader = new ZXing.BrowserMultiFormatReader();
    const video = document.getElementById("video");
    const statusEl = document.getElementById("status");

    let scanned = false;

    async function startScanner() {
        try {
            const devices = await codeReader.listVideoInputDevices();

            if (devices.length === 0) {
                statusEl.innerHTML = "❌ No camera found";
                return;
            }

            let cameraId = devices[devices.length - 1].deviceId;

            for (const device of devices) {
                const label = (device.label || "").toLowerCase();
                if (
                    label.includes("back") ||
                    label.includes("rear") ||
                    label.includes("environment")
                ) {
                    cameraId = device.deviceId;
                }
            }

            statusEl.innerHTML = "📷 Camera ready";

            codeReader.decodeFromVideoDevice(
                cameraId,
                video,
                (result, error) => {
                    if (result && !scanned) {
                        scanned = true;

                        const barcode = result.text;
                        statusEl.innerHTML = "✅ Scanned: " + barcode;

                        window.parent.postMessage(
                            {
                                type: "streamlit:setComponentValue",
                                value: barcode
                            },
                            "*"
                        );

                        // scan ပြီးမှ camera ပိတ်
                        setTimeout(() => {
                            codeReader.reset();
                        }, 500);
                    }
                }
            );
        } catch (e) {
            statusEl.innerHTML = "❌ Camera Error: " + e;
        }
    }

    startScanner();
    </script>
    """

    return components.html(html_code, height=height, key=component_key)
