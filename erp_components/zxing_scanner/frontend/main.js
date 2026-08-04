import {
BrowserMultiFormatReader
}
from
"https://cdn.jsdelivr.net/npm/@zxing/browser@0.1.5/+esm";


const reader =
new BrowserMultiFormatReader();


const video =
document.getElementById("video");


let sent = false;


async function start(){


    const devices =
    await BrowserMultiFormatReader.listVideoInputDevices();


    if(devices.length === 0){
        return;
    }


    let camera =
    devices[devices.length - 1].deviceId;


    for(const d of devices){

        const label =
        (d.label || "").toLowerCase();

        if(
            label.includes("back") ||
            label.includes("rear") ||
            label.includes("environment")
        ){
            camera = d.deviceId;
        }
    }


    reader.decodeFromVideoDevice(

        camera,

        video,

        (result,error)=>{

            if(result && !sent){

                sent = true;

                window.parent.postMessage(
                {
                    type:"streamlit:setComponentValue",
                    value:result.text
                },
                "*");

                reader.reset();
            }
        }
    );
}


start();
