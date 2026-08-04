const codeReader = new ZXing.BrowserMultiFormatReader();

const video = document.getElementById("video");
const resultBox = document.getElementById("result");

let sent = false;

async function startScanner(){

    try{

        const devices =
            await codeReader.listVideoInputDevices();

        if(devices.length === 0){

            resultBox.innerHTML = "❌ No camera found";
            return;
        }

        // Prefer back camera
        let cameraId = devices[devices.length - 1].deviceId;

        for(const device of devices){

            const label =
                (device.label || "").toLowerCase();

            if(
                label.includes("back") ||
                label.includes("rear") ||
                label.includes("environment")
            ){
                cameraId = device.deviceId;
            }
        }

        resultBox.innerHTML = "📷 Camera started";

        codeReader.decodeFromVideoDevice(

            cameraId,

            video,

            (result, error) => {

                if(result && !sent){

                    sent = true;

                    const barcode = result.text;

                    resultBox.innerHTML =
                        "✅ Barcode: " + barcode;

                    // Send barcode to Streamlit
                    window.parent.postMessage(
                        {
                            type: "streamlit:setComponentValue",
                            value: barcode
                        },
                        "*"
                    );

                    // Stop camera after successful scan
                    setTimeout(() => {
                        codeReader.reset();
                    }, 300);
                }
            }
        );

    }catch(e){

        console.error(e);

        resultBox.innerHTML =
            "❌ Camera Error: " + e.message;
    }
}

startScanner();
