import streamlit.components.v1 as components

def zxing_scanner():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <script src="https://unpkg.com/@zxing/library@latest"></script>
    </head>
    <body style="margin:0;padding:0;text-align:center;">

      <video id="video" width="100%" style="border:1px solid #ccc;border-radius:8px;"></video>
      <p id="result">Waiting scan...</p>

      <script>
      const codeReader = new ZXing.BrowserMultiFormatReader();
      const video = document.getElementById("video");
      const resultBox = document.getElementById("result");

      async function startScanner() {
        try {
          const devices = await codeReader.listVideoInputDevices();

          if (devices.length === 0) {
            resultBox.innerHTML = "❌ No camera found";
            return;
          }

          let cameraId = devices[devices.length - 1].deviceId;

          codeReader.decodeFromVideoDevice(
            cameraId,
            video,
            (result, err) => {
              if (result) {
                resultBox.innerHTML = "✅ Barcode: " + result.text;

                window.parent.postMessage(
                  {
                    type: "streamlit:setComponentValue",
                    value: result.text
                  },
                  "*"
                );

                codeReader.reset();
              }
            }
          );
        } catch (e) {
          resultBox.innerHTML = "❌ Camera Error: " + e;
        }
      }

      startScanner();
      </script>

    </body>
    </html>
    """

    return components.html(html, height=450)
