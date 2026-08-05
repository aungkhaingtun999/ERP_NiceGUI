const codeReader = new ZXing.BrowserMultiFormatReader();

const video = document.getElementById("video");
const status = document.getElementById("status");

let scanned = false;



async function startScanner(){

    try {

        status.innerHTML = "📷 Opening camera...";


        // Force video visible
        video.style.display = "block";
        video.style.visibility = "visible";
        video.style.opacity = "1";


        const devices =
            await codeReader.listVideoInputDevices();


        if(!devices || devices.length === 0){

            status.innerHTML =
            "❌ No camera found";

            return;
        }



        let cameraId =
        devices[0].deviceId;



        // Prefer back camera
        for(const device of devices){

            const label =
            (device.label || "").toLowerCase();


            if(
                label.includes("back") ||
                label.includes("rear") ||
                label.includes("environment")
            ){

                cameraId =
                device.deviceId;

                break;
            }

        }



        status.innerHTML =
        "📷 Camera ready...";


        codeReader.decodeFromVideoDevice(
            cameraId,
            video,
            (result, error)=>{


                if(result && !scanned){

                    scanned = true;


                    const barcode =
                    result.getText();



                    status.innerHTML =
                    "✅ Barcode: " + barcode;



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

                    },1000);


                }


            }
        );



        // Wait video render
        setTimeout(()=>{

            video.play()
            .then(()=>{

                video.style.display="block";

            })
            .catch(()=>{});


        },1000);



    }
    catch(e){

        status.innerHTML =
        "❌ Camera Error: " + e.message;

    }

}



startScanner();
