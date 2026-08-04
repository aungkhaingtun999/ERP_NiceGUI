# ==============================================================================
# ZXING MOBILE CAMERA BARCODE SCANNER
# STREAMLIT SAFE VERSION
# ==============================================================================

import streamlit.components.v1 as components


def zxing_scanner():

    html = """

    <!DOCTYPE html>

    <html>

    <head>

    <meta name="viewport"
          content="width=device-width, initial-scale=1">

    <script src="https://unpkg.com/@zxing/library@latest"></script>

    </head>


    <body style="
        margin:0;
        padding:0;
        text-align:center;
    ">


    <video
        id="video"
        style="
        width:100%;
        max-width:400px;
        border-radius:10px;
        border:1px solid #ccc;
        "
    ></video>


    <h4 id="status">
        📷 Starting camera...
    </h4>


    <script>


    const codeReader =
        new ZXing.BrowserMultiFormatReader();


    const video =
        document.getElementById("video");


    const status =
        document.getElementById("status");



    async function startScanner(){


        try{


            const devices =
                await codeReader.listVideoInputDevices();


            if(devices.length === 0){

                status.innerHTML =
                "❌ Camera not found";

                return;
            }



            let cameraId =
                devices[devices.length-1].deviceId;



            for(const device of devices){


                let name =
                (device.label || "")
                .toLowerCase();


                if(
                    name.includes("back") ||
                    name.includes("rear") ||
                    name.includes("environment")
                ){

                    cameraId =
                    device.deviceId;

                }

            }



            codeReader.decodeFromVideoDevice(

                cameraId,

                video,


                (result,error)=>{


                    if(result){


                        let code =
                        result.text;



                        status.innerHTML =
                        "✅ " + code;



                        window.parent.postMessage(

                        {

                        type:
                        "streamlit:setComponentValue",

                        value:
                        code

                        },

                        "*"

                        );



                        codeReader.reset();


                    }

                }

            );



        }

        catch(e){


            status.innerHTML =
            "❌ " + e;


        }


    }



    startScanner();


    </script>


    </body>

    </html>

    """


    return components.html(
        html,
        height=500
    )
