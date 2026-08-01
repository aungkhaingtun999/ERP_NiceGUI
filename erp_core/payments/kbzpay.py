import io
import qrcode



class KBZPayQRService:


    @staticmethod
    def generate_from_template(
        template,
        amount
    ):


        payload = (
            template
            .replace(
                "{amount}",
                str(amount)
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


        img = qr.make_image()


        buffer = io.BytesIO()


        img.save(
            buffer,
            format="PNG"
        )


        buffer.seek(0)


        return buffer