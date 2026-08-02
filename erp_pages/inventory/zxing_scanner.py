# ==============================================================================
# erp_pages/inventory/zxing_scanner.py
# MOBILE INVENTORY v3
# ZXing Live Mobile Barcode Scanner
# ==============================================================================


import streamlit as st
import streamlit.components.v1 as components



def scan_barcode():


    st.subheader(
        "📷 Live Barcode Scanner"
    )


    scanner_html = r"""

<!DOCTYPE html>

<html>


<head>

<meta charset="UTF-8">


<style>

body {

margin:0;

padding:0;

}


video {

width:100%;

border-radius:12px;

background:black;

}


#result {

font-size:18px;

font-weight:bold;

margin-top:10px;

}

</style>


</head>



<body>



<video

id="video"

autoplay

playsinline

muted>

</video>



<div id="status">

Starting camera...

</div>


<div id="result">

Point the camera at a barcode

</div>




<script type="module">


import {

BrowserMultiFormatReader

}

from

"https://cdn.jsdelivr.net/npm/@zxing/browser@0.1.5/+esm";




const codeReader =

new BrowserMultiFormatReader();




const video =

document.getElementById(
"video"
);



const status =

document.getElementById(
"status"
);



const resultBox =

document.getElementById(
"result"
);





async function startScanner(){



try{



const devices =

await BrowserMultiFormatReader
.listVideoInputDevices();




if(devices.length === 0){


status.innerHTML =
"No camera found";


return;


}





let selectedCamera =

devices[0].deviceId;




// Prefer Back Camera

for(

const camera of devices

){



const label =

camera.label.toLowerCase();



if(

label.includes("back")

||

label.includes("rear")

||

label.includes("environment")

){


selectedCamera =

camera.deviceId;


break;


}


}




status.innerHTML =
"Back camera selected";





codeReader.decodeFromVideoDevice(


selectedCamera,


video,


(result,error)=>{



if(result){



resultBox.innerHTML =

"Barcode: "
+
result.text;



}





}



);



}


catch(error){


status.innerHTML =

"Camera Error: "
+
error;



}



}





startScanner();



</script>


</body>


</html>

"""


    components.html(

        scanner_html,

        height=550

    )


    return None
