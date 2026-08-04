const video = document.getElementById("video");
const status = document.getElementById("status");


async function startCamera(){

    try {

        const stream = await navigator.mediaDevices.getUserMedia({

            video:{
                facingMode:{
                    ideal:"environment"
                }
            },

            audio:false

        });


        video.srcObject = stream;


        await video.play();


        status.innerHTML =
            "📷 Camera OK";


    }
    catch(e){

        status.innerHTML =
            "❌ Camera Error: " + e;

    }

}


startCamera();
