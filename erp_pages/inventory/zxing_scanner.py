# ==============================================================================
# erp_pages/inventory/zxing_scanner.py
# MOBILE INVENTORY v2
# ZXing Browser Live Barcode Scanner
# ==============================================================================


import streamlit as st
import streamlit.components.v1 as components



# ==============================================================================
# LIVE SCANNER
# ==============================================================================


def zxing_live_scanner():


    st.subheader(
        "📷 Live Barcode Scanner"
    )


    scanner_html = """

    <div>

    <video
        id="video"
        width="100%"
        style="border-radius:10px;"
        autoplay
        playsinline>
    </video>


    <h4 id="result">
        Waiting for barcode...
    </h4>


    </div>


    <script type="module">


    import {
        BrowserMultiFormatReader
    }
    from "https://cdn.jsdelivr.net/npm/@zxing/library@0.20.0/+esm";


    const codeReader =
        new BrowserMultiFormatReader();


    const video =
        document.getElementById("video");


    const result =
        document.getElementById("result");



    async function startScanner(){


        try{


            const devices =
                await codeReader.listVideoInputDevices();



            let selectedDeviceId =
                devices[0].deviceId;



            for(
                const device of devices
            ){

                if(
                    device.label.toLowerCase()
                    .includes("back")
                ){

                    selectedDeviceId =
                    device.deviceId;

                }

            }



            codeReader.decodeFromVideoDevice(

                selectedDeviceId,

                video,

                (scanResult, error)=>{


                    if(scanResult){


                        result.innerHTML =
                        "Barcode: "
                        + scanResult.text;


                        window.parent.postMessage(

                            {
                                type:
                                "barcode",

                                value:
                                scanResult.text
                            },

                            "*"

                        );

                    }

                }

            );


        }

        catch(error){


            result.innerHTML =
            "Camera Error: "
            + error;


        }


    }



    startScanner();


    </script>

    """



    components.html(

        scanner_html,

        height=500

    )



    return None