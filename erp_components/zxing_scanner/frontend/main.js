const codeReader =
new ZXing.BrowserMultiFormatReader();



const video =
document.getElementById(
"video"
);



async function start(){


const devices =
await codeReader.listVideoInputDevices();



let camera =
devices[0].deviceId;



for(
let d of devices
){

if(
d.label.toLowerCase()
.includes("back")
){

camera =
d.deviceId;

}

}



codeReader.decodeFromVideoDevice(

camera,

video,

(result,error)=>{


if(result){


window.parent.postMessage(

{

type:"streamlit:setComponentValue",

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