import streamlit.components.v1 as components


def zxing_scanner():

    html = """
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="https://unpkg.com/@zxing/library@latest"></script>
    </head>

    <body style="text-align:center">

    <video id="video"
        style="
        width:100%;
        max-width:400px;
        border-radius:10px;
        ">
    </video>

    <p id="result">
        📷 Waiting scan...
    </p>


    <script>

    const reader =
        new ZXing.BrowserMultiFormatReader();

    const video =
        document.getElementById("video");

    const result =
        document.getElementById("result");


    reader.decodeFromVideoDevice(
        null,
        video,
        (code, err)=>{

            if(code){

                result.innerHTML =
                    "✅ " + code.text;


                window.parent.postMessage(
                {
                    type:
                    "streamlit:setComponentValue",

                    value:
                    code.text
                },
                "*"
                );


                reader.reset();

            }

        }
    );

    </script>

    </body>
    </html>
    """

    return components.html(
        html,
        height=450
    )
