const video = document.getElementById("video");
const status = document.getElementById("status");


navigator.mediaDevices.getUserMedia({

    video: {
        facingMode: {
            ideal: "environment"
        }
    },

    audio:false

})
.then(stream => {

    video.srcObject = stream;

    video.onloadedmetadata = () => {

        video.play();

    };


    status.innerHTML = "📷 Camera OK";

})
.catch(error => {

    status.innerHTML =
        "❌ " + error;

});
