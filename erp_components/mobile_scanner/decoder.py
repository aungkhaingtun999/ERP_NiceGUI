import cv2
from pyzbar import pyzbar


def decode_barcode(frame):

    if frame is None:
        return None


    gray = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2GRAY
    )


    barcodes = pyzbar.decode(gray)


    for barcode in barcodes:

        data = barcode.data.decode(
            "utf-8"
        )

        return data


    return None
