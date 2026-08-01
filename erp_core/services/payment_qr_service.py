# ==============================================================================
# ERP ENTERPRISE PAYMENT QR SERVICE v1.0
# STATIC QR GENERATOR
# ==============================================================================

import io
import qrcode


class PaymentQRService:

    @staticmethod
    def generate_qr(
        provider,
        account_name,
        account_no,
        amount,
        sale_id
    ):

        payload = (
            f"PROVIDER:{provider}\n"
            f"NAME:{account_name}\n"
            f"ACCOUNT:{account_no}\n"
            f"AMOUNT:{amount}\n"
            f"SALE:{sale_id}"
        )

        qr = qrcode.QRCode(
            version=1,
            box_size=8,
            border=2
        )

        qr.add_data(payload)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        return buffer