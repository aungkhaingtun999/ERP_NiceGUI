const codeReader = new ZXing.BrowserMultiFormatReader();

const video = document.getElementById("video");
const status = document.getElementById("status");

let scanned = false;


async function startScanner(){

    try {

        status.innerHTML = "📷 Opening camera...";


        const devices =
            await codeReader.listVideoInputDevices();


        if(devices.length === 0){

            status.innerHTML =
            "❌ No camera found";

            return;
        }


        let cameraId = devices[0].deviceId;


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



        codeReader.decodeFromVideoDevice(
            cameraId,
            video,
            (result, error)=>{


                if(result && !scanned){

                    scanned = true;


                    const barcode =
                    result.getText();


                    status.innerHTML =
                    "✅ " + barcode;



                    window.parent.postMessage(
                    {
                        type:
                        "streamlit:setComponentValue",

                        value:
                        barcode
                    },
                    "*"
                    );



                    setTimeout(()=>{

                        codeReader.reset();

                    },500);


                }


            }
        );


    }
    catch(e){

        status.innerHTML =
        "❌ Camera Error: " + e;

    }

}



startScanner();
