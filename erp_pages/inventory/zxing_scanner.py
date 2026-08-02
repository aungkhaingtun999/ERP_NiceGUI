# ==============================================================================
# erp_pages/inventory/zxing_scanner.py
# MOBILE INVENTORY v3
# ZXing Live Scanner Bridge
# ==============================================================================


import streamlit as st
import streamlit.components.v1 as components

from streamlit_js_eval import streamlit_js_eval



def scan_barcode():


    st.subheader(
        "📷 Live Barcode Scanner"
    )


    scanner = r"""

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


let camera =
devices[devices.length-1].deviceId;



for(const d of devices){

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


localStorage.setItem(
"barcode_result",
result.text
);


}

}

);


}


start();


</script>



<video

id="video"

width="100%"

height="350"

autoplay

playsinline

muted>

</video>


"""


    components.html(
        scanner,
        height=400
    )



    barcode = streamlit_js_eval(

        js_expressions=
        "localStorage.getItem('barcode_result')",

        key="barcode_reader"

    )


    return barcode
