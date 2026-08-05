#erp_components/mobile_scanner/scanner.py

# ==============================================================================
# erp_components/mobile_scanner/scanner.py
# MOBILE BARCODE SCANNER v3.1 STABLE
# HTML5 CAMERA + ZXING JS
# ==============================================================================

import streamlit as st
import streamlit.components.v1 as components


def mobile_scanner():

    st.subheader("📷 Barcode Scanner")


    html_code = """

    <video id="video"
           width="100%"
           autoplay
           playsinline>
    </video>


    <div id="result">
        📷 Waiting scan...
    </div>


    <script src="https://unpkg.com/@zxing/library@latest"></script>


    <script>

    const codeReader =
        new ZXing.BrowserMultiFormatReader();


    const video =
        document.getElementById("video");


    const resultBox =
        document.getElementById("result");


    let scanned = false;



    async function startScanner(){


        try{


            const devices =
            await codeReader.listVideoInputDevices();



            if(devices.length === 0){

                resultBox.innerHTML =
                "❌ No camera";

                return;

            }



            let cameraId =
            devices[devices.length-1].deviceId;



            for(const device of devices){


                let label =
                (device.label || "")
                .toLowerCase();


                if(
                    label.includes("back") ||
                    label.includes("rear") ||
                    label.includes("environment")
                ){

                    cameraId =
                    device.deviceId;

                }

            }



            codeReader.decodeFromVideoDevice(

                cameraId,

                video,


                (result,error)=>{


                    if(result && !scanned){


                        scanned = true;


                        const barcode =
                        result.text;



                        resultBox.innerHTML =
                        "✅ Barcode: " + barcode;



                        window.parent.postMessage(

                        {

                            type:
                            "barcode_scan",

                            value:
                            barcode

                        },

                        "*"

                        );



                        setTimeout(()=>{

                            scanned=false;

                        },1000);


                    }


                }

            );



        }

        catch(e){

            resultBox.innerHTML =
            "❌ " + e;

        }


    }



    startScanner();


    </script>

    """



    components.html(
        html_code,
        height=450
    )


    return None
