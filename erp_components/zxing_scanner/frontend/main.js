import {

BrowserMultiFormatReader

}

from

"https://cdn.jsdelivr.net/npm/@zxing/browser@0.1.5/+esm";



const reader =
new BrowserMultiFormatReader();



const video =
document.getElementById(
"video"
);



async function start(){


const devices =
await BrowserMultiFormatReader.listVideoInputDevices();



let camera =
devices[0].deviceId;



for(
const d of devices
){

if(
d.label.toLowerCase()
.includes("back")
){

camera =
d.deviceId;

}

}



reader.decodeFromVideoDevice(

camera,

video,

(result,error)=>{


if(result){


window.parent.postMessage(

{

type:
"streamlit:setComponentValue",

value:
result.text

},

"*"

);


}

}

);


}


start();
