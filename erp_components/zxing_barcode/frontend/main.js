const codeReader = new ZXing.BrowserMultiFormatReader();

const video = document.getElementById("video");
const resultBox = document.getElementById("result");


async function startScanner(){

    try{

        const devices =
            await codeReader.listVideoInputDevices();


        if(devices.length === 0){

            resultBox.innerHTML = "❌ No Camera";
            return;

        }


        let cameraId =
            devices[devices.length - 1].deviceId;



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


                if(result){


                    const barcode =
                        result.text;



                    resultBox.innerHTML =
                        "✅ Barcode: " + barcode;



                    console.log(
                        "BARCODE:",
                        barcode
                    );



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
    catch(error){

        resultBox.innerHTML =
            "ERROR: " + error;

    }

}


startScanner();
