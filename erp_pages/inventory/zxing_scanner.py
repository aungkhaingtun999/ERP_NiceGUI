import streamlit as st
import streamlit.components.v1 as components


def scan_barcode():

    st.subheader(
        "📷 Live Barcode Scanner"
    )


    scanner_html = r"""

<!DOCTYPE html>

<html>

<body>


<video

id="video"

width="100%"

height="350"

autoplay

playsinline

muted>

</video>


<h3 id="result">
Waiting scan...
</h3>



<script type="module">


import {

BrowserMultiFormatReader

}

from

"https://cdn.jsdelivr.net/npm/@zxing/browser@0.1.5/+esm";



const reader =
new BrowserMultiFormatReader();



async function start(){


const devices =
await BrowserMultiFormatReader
.listVideoInputDevices();



let camera =
devices[devices.length-1].deviceId;



for(
const d of devices
){

if(
d.label.toLowerCase()
.includes("back")
){

camera=d.deviceId;

}

}



reader.decodeFromVideoDevice(

camera,

"video",

(result,error)=>{


if(result){


document.getElementById(
"result"
).innerHTML =

"✅ Barcode: "
+
result.text;



}


}

);



}


start();


</script>


</body>

</html>

"""


    components.html(

        scanner_html,

        height=500

    )


    return None
