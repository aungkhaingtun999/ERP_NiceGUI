const video = document.getElementById("video");
const status = document.getElementById("status");


async function startCamera(){

    try {

        const stream = await navigator.mediaDevices.getUserMedia({

            video:{
                facingMode:"environment",
                width:{
                    ideal:1280
                },
                height:{
                    ideal:720
                }
            },

            audio:false

        });


        video.srcObject = stream;


        video.setAttribute(
            "playsinline",
            true
        );


        await video.play();


        status.innerHTML =
            "📷 Camera Preview OK";


    }
    catch(error){

        status.innerHTML =
            "❌ Camera Error: " + error.message;

    }

}


startCamera();
