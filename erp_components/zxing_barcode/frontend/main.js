// ==============================================================================
// ZXING LIVE BARCODE SCANNER
// ==============================================================================


const codeReader =
    new ZXing.BrowserMultiFormatReader();



const video =
    document.getElementById("video");



async function startScanner(){


    try{


        const devices =
            await codeReader.listVideoInputDevices();


        if(devices.length === 0){

            document.body.innerHTML =
            "No Camera Found";

            return;

        }



        let cameraId =
            devices[0].deviceId;



        for(
            const device of devices
        ){

            if(
                device.label
                .toLowerCase()
                .includes("back")
            ){

                cameraId =
                device.deviceId;

            }

        }



        codeReader.decodeFromVideoDevice(

            cameraId,

            video,

            (result, error)=>{


                if(result){


                    const barcode =
                    result.text;



                    window.parent.postMessage(

                        {

                        type:
                        "streamlit:setComponentValue",

                        value:
                        barcode

                        },

                        "*"

                    );


                }


            }

        );


    }

    catch(error){


        console.error(error);


        document.body.innerHTML =
        "Camera Error: "
        + error;


    }


}



startScanner();
