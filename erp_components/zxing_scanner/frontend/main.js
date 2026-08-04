import { BrowserMultiFormatReader } from
"https://cdn.jsdelivr.net/npm/@zxing/library@latest/+esm";


const video = document.getElementById("video");
const status = document.getElementById("status");


const reader = new BrowserMultiFormatReader();



function sendBarcode(code){

    window.parent.postMessage(

        {
            type:"streamlit:setComponentValue",
            value:code
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
        "📷 Scan barcode...";



        reader.decodeFromVideoDevice(

            cameraId,

            video,


            (result,error)=>{


                if(result){


                    const code =
                    result.text;



                    status.innerHTML =
                    "✅ " + code;



                    sendBarcode(code);



                    reader.reset();


                }


            }

        );



    }
    catch(error){


        status.innerHTML =
        "❌ " + error;


    }


}



startScanner();
