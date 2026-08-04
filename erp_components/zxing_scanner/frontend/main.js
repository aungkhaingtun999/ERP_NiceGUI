import { BrowserMultiFormatReader } from
"https://cdn.jsdelivr.net/npm/@zxing/library@latest/+esm";


const video = document.getElementById("video");


const reader = new BrowserMultiFormatReader();


function sendValue(value){

    window.parent.postMessage(
        {
            type: "streamlit:setComponentValue",
            value: value
        },
        "*"
    );

}



async function startScanner(){

    try{


        const devices =
            await reader.listVideoInputDevices();


        if(devices.length === 0){

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



        reader.decodeFromVideoDevice(

            cameraId,

            video,


            (result,error)=>{


                if(result){


                    const code =
                        result.text;


                    sendValue(code);


                    reader.reset();


                }


            }

        );


    }
    catch(e){

        console.log(e);

    }

}



startScanner();
