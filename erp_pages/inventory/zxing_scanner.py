# ==============================================================================
# erp_pages/inventory/zxing_scanner.py
# MOBILE INVENTORY v3
# ZXING LIVE CAMERA
# ==============================================================================


import streamlit.components.v1 as components



def scan_barcode():


    html = r"""

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


<h4 id="result">
Point the camera at a barcode
</h4>



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
await BrowserMultiFormatReader.listVideoInputDevices();



let deviceId =
devices[0].deviceId;



reader.decodeFromVideoDevice(

deviceId,

"video",

(result,error)=>{


if(result){


document.getElementById(
"result"
).innerHTML =

"Barcode: "
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

        html,

        height=450

    )


    return None
