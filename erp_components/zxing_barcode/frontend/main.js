import { BrowserMultiFormatReader } from 'https://cdn.jsdelivr.net/npm/@zxing/browser@0.1.5/+esm';

const video = document.getElementById('video');
const reader = new BrowserMultiFormatReader();

async function startScanner() {

    try {

        const devices =
            await BrowserMultiFormatReader.listVideoInputDevices();

        if (devices.length === 0) {

            document.body.innerHTML =
                '<div style="color:white;padding:20px">No camera found</div>';

            return;
        }

        let cameraId = devices[0].deviceId;

        for (const d of devices) {

            const label = (d.label || '').toLowerCase();

            if (
                label.includes('back') ||
                label.includes('rear') ||
                label.includes('environment')
            ) {
                cameraId = d.deviceId;
            }
        }

        reader.decodeFromVideoDevice(
            cameraId,
            video,
            (result, error) => {

                if (result) {

                    window.parent.postMessage(
                        {
                            type: 'streamlit:setComponentValue',
                            value: result.text
                        },
                        '*'
                    );

                    reader.reset();
                }
            }
        );

    } catch (e) {

        document.body.innerHTML =
            '<div style="color:red;padding:20px">Camera Error: ' +
            e +
            '</div>';

        console.error(e);
    }
}

startScanner();
