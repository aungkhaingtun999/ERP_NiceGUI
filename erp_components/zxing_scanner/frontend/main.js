import { BrowserMultiFormatReader } from
"https://cdn.jsdelivr.net/npm/@zxing/library@latest/+esm";


const video = document.getElementById("video");
const status = document.getElementById("status");


const reader = new BrowserMultiFormatReader();



function sendValue(value){

    window.parent.postMessage(

        {
            type:"streamlit:setComponentValue",
            value:value
        },

        "*"

    );

}



async function startScanner(){

    try{


        const devices =
            await reader.listVideoInputDevices();



        if(devices.length === 0){

            status.innerHTML =
            "❌ No camera found";

            return;

        }



        let cameraId =
            devices[devices.length - 1].deviceId;



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
        "📷 Camera OK - Scan barcode";



        reader.decodeFromVideoDevice(

            cameraId,

            video,


            (result, error)=>{


                if(result){


                    const code =
                    result.text;



                    status.innerHTML =
                    "✅ " + code;



                    sendValue(code);



                    reader.reset();


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
