# ==============================================================================
# erp_components/mobile_scanner/scanner.py
# MOBILE BARCODE SCANNER v3.0
# HTML5 CAMERA + ZXING JS
# ==============================================================================

import streamlit as st
import streamlit.components.v1 as components


def mobile_scanner():

    st.subheader("📷 Barcode Scanner")

    html_code = """
    <div>
        <video id="video" 
               width="100%" 
               autoplay 
               playsinline>
        </video>

        <div id="result">
            Waiting scan...
        </div>
    </div>

    <script src="https://unpkg.com/@zxing/library@latest"></script>

    <script>

    const codeReader = new ZXing.BrowserMultiFormatReader();

    const video = document.getElementById("video");
    const resultBox = document.getElementById("result");

    let scanned = false;


    async function startScanner(){

        try{

            const devices =
                await codeReader.listVideoInputDevices();


            if(devices.length === 0){

                resultBox.innerHTML =
                "❌ No camera found";

                return;
            }


            let cameraId =
                devices[devices.length-1].deviceId;


            codeReader.decodeFromVideoDevice(
                cameraId,
                video,
                (result, err)=>{


                    if(result && !scanned){

                        scanned = true;


                        const barcode =
                        result.text;


                        resultBox.innerHTML =
                        "✅ Barcode: " + barcode;


                        window.parent.postMessage(
                        {
                            type:
                            "streamlit:setComponentValue",
                            value:
                            barcode
                        },
                        "*"
                        );


                        setTimeout(()=>{

                            codeReader.reset();

                        },500);

                    }

                }
            );


        }
        catch(e){

            resultBox.innerHTML =
            "❌ Camera Error: " + e;

        }

    }


    startScanner();

    </script>
    """


    barcode = components.html(
        html_code,
        height=450
    )


    return barcode
