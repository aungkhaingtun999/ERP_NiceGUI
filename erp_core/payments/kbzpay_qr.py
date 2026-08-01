# ==============================================================================
# ERP ENTERPRISE KBZ PAY QR SERVICE v2.0
# KBZ Compatible QR Payload
# ==============================================================================

import io
import base64
import qrcode
from qrcode.constants import ERROR_CORRECT_M


class KBZPayQRService:


    # --------------------------------------------------------------------------
    # BUILD KBZ PAYLOAD
    # --------------------------------------------------------------------------
    @staticmethod
    def build_payload(
        account_no,
        amount,
        sale_id=None
    ):

        """
        Build KBZ-compatible payload from observed QR samples.
        This is a practical implementation for merchant QR generation.
        """

        amount_text = f"{float(amount):.1f}"

        # Merchant account part
        account_part = f"Q{account_no}"

        raw = (
            f"KBZPayaNO"
            f"{account_part}"
            f"|{amount_text}"
            f"|{sale_id or ''}"
        )

        payload = base64.b64encode(
            raw.encode("utf-8")
        ).decode("utf-8")

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
        qr.make(fit=True)

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
    # DEBUG
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
