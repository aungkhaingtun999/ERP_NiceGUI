import { BrowserMultiFormatReader } from
"https://cdn.jsdelivr.net/npm/@zxing/library@latest/+esm";


const video = document.getElementById("video");

const status = document.createElement("p");
status.style.color = "white";
status.innerHTML = "Starting camera...";
document.body.appendChild(status);


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

            const name =
            (device.label || "")
            .toLowerCase();


            if(
                name.includes("back") ||
                name.includes("rear") ||
                name.includes("environment")
            ){

                cameraId =
                device.deviceId;

            }

        }



        status.innerHTML =
        "📷 Camera starting...";



        reader.decodeFromVideoDevice(

            cameraId,

            video,


            (result,error)=>{


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
        "❌ " + e;

    }

}


startScanner();
