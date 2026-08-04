import { BrowserMultiFormatReader }
from "https://cdn.jsdelivr.net/npm/@zxing/browser@0.1.5/+esm";

const reader = new BrowserMultiFormatReader();

const video = document.getElementById("video");
const statusBox = document.getElementById("status");
const startBtn = document.getElementById("startBtn");

let controls = null;

async function startCamera(){

    try{

        statusBox.innerHTML = "Requesting camera permission...";

        const devices =
            await BrowserMultiFormatReader.listVideoInputDevices();

        if(devices.length === 0){
            statusBox.innerHTML = "❌ No camera found";
            return;
        }

        let cameraId = devices[devices.length - 1].deviceId;

        for(const d of devices){

            const label = (d.label || "").toLowerCase();

            if(
                label.includes("back") ||
                label.includes("rear") ||
                label.includes("environment")
            ){
                cameraId = d.deviceId;
            }
        }

        controls = await reader.decodeFromVideoDevice(
            cameraId,
            video,
            (result, error) => {

                if(result){

                    const barcode = result.text;

                    statusBox.innerHTML =
                        "✅ " + barcode;

                    window.parent.postMessage(
                        {
                            type:"streamlit:setComponentValue",
                            value:barcode
                        },
                        "*"
                    );
                }
            }
        );

        statusBox.innerHTML = "📷 Camera started";

    }catch(e){

        console.error(e);

        statusBox.innerHTML =
            "❌ Camera Error: " + e.message;
    }
}

startBtn.addEventListener("click", startCamera);
