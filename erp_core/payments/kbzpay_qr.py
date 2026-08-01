# ==============================================================================
# ERP ENTERPRISE KBZ PAY QR SERVICE v1.0
#
# KBZ Payment QR Generator
# ==============================================================================

import io
import base64

import qrcode

from qrcode.constants import ERROR_CORRECT_M


class KBZPayQRService:


    # --------------------------------------------------------------------------
    # BUILD PAYLOAD
    # --------------------------------------------------------------------------

    @staticmethod
    def build_payload(
        account_no,
        amount,
        sale_id=None
    ):

        """
        KBZ payload placeholder layer

        This keeps payment engine separated
        from QR image generation.
        """


        amount_text = f"{float(amount):.1f}"


        payload = (
            f"KBZPayaNO|"
            f"ACCOUNT:{account_no}|"
            f"AMOUNT:{amount_text}|"
            f"SALE:{sale_id or ''}"
        )


        return payload



    # --------------------------------------------------------------------------
    # GENERATE QR IMAGE
    # --------------------------------------------------------------------------

    @staticmethod
    def generate_qr(
        account_no,
        amount,
        sale_id=None
    ):


        payload = KBZPayQRService.build_payload(
            account_no,
            amount,
            sale_id
        )


        qr = qrcode.QRCode(
            version=None,
            error_correction=ERROR_CORRECT_M,
            box_size=10,
            border=4
        )


        qr.add_data(payload)

        qr.make(
            fit=True
        )


        img = qr.make_image(
            fill_color="black",
            back_color="white"
        )


        buffer = io.BytesIO()


        img.save(
            buffer,
            format="PNG"
        )


        buffer.seek(0)


        return buffer



    # --------------------------------------------------------------------------
    # GET RAW PAYLOAD
    # --------------------------------------------------------------------------

    @staticmethod
    def get_raw_payload(
        account_no,
        amount,
        sale_id=None
    ):

        return KBZPayQRService.build_payload(
            account_no,
            amount,
            sale_id
        )