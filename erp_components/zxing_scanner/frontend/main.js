// ==============================================================================
// ZXING LIVE BARCODE SCANNER v2
// Streamlit Custom Component
// ==============================================================================


const video = document.getElementById("video");
const status = document.getElementById("status");


// ZXing reader

const codeReader =
    new ZXing.BrowserMultiFormatReader();



let scanned = false;



async function startScanner(){


    try{


        const devices =
            await codeReader.listVideoInputDevices();



        if(devices.length === 0){

            status.innerHTML =
                "❌ No camera found";

            return;
        }



        let cameraId =
            devices[devices.length - 1].deviceId;



        // Prefer back camera

        for(const device of devices){


            const label =
                (device.label || "")
                .toLowerCase();



            if(

                label.includes("back") ||

                label.includes("rear") ||

                label.includes("environment")

            ){

                cameraId =
                    device.deviceId;

            }

        }




        status.innerHTML =
            "📷 Starting scanner...";




        codeReader.decodeFromVideoDevice(

            cameraId,

            video,

            (result, error)=>{


                if(result && !scanned){


                    scanned = true;


                    const barcode =
                        result.text;



                    status.innerHTML =
                        "✅ Barcode: " + barcode;



                    // Send value to Streamlit

                    window.parent.postMessage(

                        {

                            type:
                            "streamlit:setComponentValue",

                            value:
                            barcode

                        },

                        "*"

                    );



                    codeReader.reset();

                }


            }

        );



    }

    catch(e){


        status.innerHTML =
            "❌ Scanner Error: " + e.message;


    }


}



startScanner();
