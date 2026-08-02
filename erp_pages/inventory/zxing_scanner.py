# ==============================================================================
# erp_pages/inventory/zxing_scanner.py
# MOBILE INVENTORY v3
# ZXing Browser Live Scanner
# Streamlit Cloud Compatible
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



async function startCamera(){


try{


const devices =
await codeReader.listVideoInputDevices();



if(devices.length === 0)
{

document.getElementById("status").innerHTML =
"No camera found";

return;

}



let deviceId =
devices[0].deviceId;



for(
const d of devices
){

if(
d.label.toLowerCase()
.includes("back")
){

deviceId =
d.deviceId;

}

}



document.getElementById("status").innerHTML =
"Camera started";



codeReader.decodeFromVideoDevice(

deviceId,

video,

(result, error)=>{


if(result)
{

document.getElementById("result").innerHTML =
"Barcode: "
+
result.text;


window.parent.postMessage(

{

type:
"barcode_scan",

barcode:
result.text

},

"*"

);


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



startCamera();



</script>


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
border-radius:12px;
background:black;
"

autoplay

playsinline

muted>

</video>



<h4 id="result">

Point camera at barcode

</h4>



</body>


</html>

"""


    components.html(

        html_code,

        height=500

    )


    return None
