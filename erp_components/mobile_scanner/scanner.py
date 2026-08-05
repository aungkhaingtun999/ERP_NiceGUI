# ==============================================================================
# erp_components/mobile_scanner/scanner.py
# MOBILE BARCODE SCANNER v3.2 STABLE
# HTML5 CAMERA + ZXING JS + SESSION STATE
# ==============================================================================

import streamlit as st
import streamlit.components.v1 as components


def mobile_scanner():

    if "barcode_value" not in st.session_state:
        st.session_state.barcode_value = ""


    html_code = """

    <video id="video"
           width="100%"
           autoplay
           playsinline>
    </video>


    <div id="result"
         style="
         font-size:20px;
         text-align:center;
         margin-top:10px;">
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
                        "✅ Barcode: "
                        + barcode;



                        window.parent.postMessage(

                        {

                            type:
                            "barcode_scan",

                            value:
                            barcode

                        },

                        "*"

                        );



                        // stop camera

                        setTimeout(()=>{


                            codeReader.reset();


                        },500);



                    }


                }

            );



        }

        catch(e){


            resultBox.innerHTML =
            "❌ Camera Error : "
            + e;


        }


    }



    startScanner();



    </script>

    """



    components.html(
        html_code,
        height=450
    )


    return st.session_state.get(
        "barcode_value",
        ""
    )
