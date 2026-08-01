import io
import qrcode
import base64


class KBZPayQRService:


    @staticmethod
    def encode_amount(amount):

        text = f"{float(amount):.1f}"

        raw = text.encode()

        encoded = base64.b64encode(
            raw
        ).decode()


        return encoded



    @staticmethod
    def build_payload(
        template,
        amount
    ):

        amount_code = (
            KBZPayQRService
            .encode_amount(amount)
        )


        payload = template.replace(
            "{AMOUNT}",
            amount_code
        )


        return payload



    @staticmethod
    def generate_qr(
        template,
        amount
    ):


        payload = (
            KBZPayQRService
            .build_payload(
                template,
                amount
            )
        )


        qr = qrcode.QRCode(
            version=None,
            box_size=10,
            border=4
        )


        qr.add_data(
            payload
        )


        qr.make(
            fit=True
        )


        image = qr.make_image()


        buffer = io.BytesIO()

        image.save(
            buffer,
            format="PNG"
        )


        buffer.seek(0)

        return buffer