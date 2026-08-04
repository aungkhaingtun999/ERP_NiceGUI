const video = document.getElementById("video");
const status = document.getElementById("status");


async function startCamera(){

    try {

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


        video.onloadedmetadata = async () => {

            await video.play();

            status.innerHTML =
                "📷 Camera Preview OK";

        };


    }
    catch(e){

        status.innerHTML =
            "❌ Camera Error: " + e.message;

    }

}


startCamera();
