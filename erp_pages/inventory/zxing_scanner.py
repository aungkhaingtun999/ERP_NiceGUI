# ==============================================================================
# erp_pages/inventory/zxing_scanner.py
# MOBILE INVENTORY v3
# ZXing Browser Live Scanner
# ==============================================================================


import streamlit as st
import streamlit.components.v1 as components



def zxing_live_scanner():


    st.subheader(
        "📷 Live Barcode Scanner"
    )


    html_code = r"""

<!DOCTYPE html>

<html>


<head>

<meta charset="UTF-8">


</head>


<body>


<h4 id="status">
Starting camera...
</h4>


<video
id="video"
width="100%"
height="350"
style="
background:black;
border-radius:10px;
"
autoplay
playsinline
muted>
</video>


<h4 id="result">
Waiting barcode...
</h4>



<script type="module">


import {

BrowserMultiFormatReader

}

from

"https://cdn.jsdelivr.net/npm/@zxing/browser@0.1.5/+esm";



const codeReader =
new BrowserMultiFormatReader();



const video =
document.getElementById("video");



async function start(){


try{


const devices =
await BrowserMultiFormatReader.listVideoInputDevices();



if(!devices.length)
{

document.getElementById("status").innerHTML =
"No camera found";

return;

}



let cameraId =
devices[0].deviceId;



for(
const cam of devices
){

if(
cam.label.toLowerCase()
.includes("back")
)
{

cameraId =
cam.deviceId;

}

}



document.getElementById("status").innerHTML =
"Camera ready";



codeReader.decodeFromVideoDevice(

cameraId,

video,

(result,error)=>{


if(result)
{


document.getElementById("result").innerHTML =
"Barcode: "
+
result.text;


}



}

);



}


catch(e)
{


document.getElementById("status").innerHTML =
"Camera Error: "
+
e;


}


}



start();



</script>


</body>

</html>

"""


    components.html(

        html_code,

        height=500

    )
