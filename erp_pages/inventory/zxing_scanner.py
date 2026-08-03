import streamlit as st
import streamlit.components.v1 as components


def scan_barcode():

    st.subheader("📷 Live Barcode Scanner")

    scanner_html = r"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0;padding:0;background:#000;">

        <video
            id="video"
            width="100%"
            height="350"
            autoplay
            playsinline
            muted
            style="border-radius:12px;">
        </video>

        <h3 id="result" style="color:white;text-align:center;">
            Waiting scan...
        </h3>

        <script type="module">

        import { BrowserMultiFormatReader }
        from "https://cdn.jsdelivr.net/npm/@zxing/browser@0.1.5/+esm";

        const reader = new BrowserMultiFormatReader();

        async function start() {

            try {

                const devices =
                    await BrowserMultiFormatReader.listVideoInputDevices();

                if (devices.length === 0) {

                    document.getElementById("result").innerHTML =
                        "❌ No camera found";

                    return;
                }

                let camera = devices[devices.length - 1].deviceId;

                for (const d of devices) {

                    const label = (d.label || "").toLowerCase();

                    if (
                        label.includes("back") ||
                        label.includes("rear") ||
                        label.includes("environment")
                    ) {
                        camera = d.deviceId;
                    }
                }

                reader.decodeFromVideoDevice(
                    camera,
                    "video",
                    (result, error) => {

                        if (result) {

                            document.getElementById("result").innerHTML =
                                "✅ Barcode: " + result.text;

                            window.parent.postMessage(
                                {
                                    type: "streamlit:setComponentValue",
                                    value: result.text
                                },
                                "*"
                            );

                            reader.reset();
                        }
                    }
                );

            } catch (e) {

                document.getElementById("result").innerHTML =
                    "❌ Camera Error: " + e;
            }
        }

        start();

        </script>

    </body>
    </html>
    """

    barcode = components.html(
        scanner_html,
        height=500
    )

    if barcode is None:
        return ""

    return str(barcode).strip()
