const video = document.getElementById("video");
const resultBox = document.getElementById("result");

let stream = null;

async function startCamera(){

    try{

        resultBox.innerHTML = "Requesting camera permission...";

        stream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: { ideal: "environment" }
            },
            audio: false
        });

        video.srcObject = stream;

        resultBox.innerHTML = "📷 Camera started";

    }catch(e){

        console.error(e);

        resultBox.innerHTML =
            "❌ Camera Error: " + e.message;
    }
}

startCamera();
