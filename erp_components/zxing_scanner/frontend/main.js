const codeReader = new ZXing.BrowserMultiFormatReader();

const video = document.getElementById("video");
const resultBox = document.getElementById("result");

let scanned = false;

async function startScanner(){

    try {

        const constraints = {
            video: {
                facingMode: {
                    ideal: "environment"
                },
                width: {
                    ideal: 1280
                },
                height: {
                    ideal: 720
                }
            }
        };


        const stream = await navigator.mediaDevices.getUserMedia(constraints);

        video.srcObject = stream;


        await video.play();


        codeReader.decodeFromStream(
            stream,
            video,
            (result, error)=>{

                if(result && !scanned){

                    scanned = true;

                    let barcode = result.text;


                    resultBox.innerHTML =
                    "✅ Barcode : " + barcode;


                    window.parent.postMessage(
                    {
                        type:"streamlit:setComponentValue",
                        value:barcode
                    },
                    "*"
                    );


                    codeReader.reset();

                }

            }
        );


    }
    catch(e){

        resultBox.innerHTML =
        "❌ Camera Error : " + e;

    }

}


startScanner();
