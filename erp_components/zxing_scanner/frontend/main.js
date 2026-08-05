const video = document.getElementById("video");
const status = document.getElementById("status");


async function startCamera(){

    try {

        status.innerHTML = "📷 Requesting camera...";


        const stream =
        await navigator.mediaDevices.getUserMedia({

            video:{
                facingMode:{
                    ideal:"environment"
                },

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
        "✅ Camera preview OK";


    }
    catch(error){

        status.innerHTML =
        "❌ " + error.name + " : " + error.message;

    }

}


startCamera();
