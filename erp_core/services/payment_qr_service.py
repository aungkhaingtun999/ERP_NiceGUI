# ==============================================================================
# ERP ENTERPRISE PAYMENT QR SERVICE v3.0
# UNIVERSAL PAYMENT QR GENERATOR
#
# Support:
# - Static Raw Payload QR
# - Receipt Information QR
# - Payment Provider Ready
# ==============================================================================


import io
import qrcode

from qrcode.constants import ERROR_CORRECT_M



class PaymentQRService:


    # --------------------------------------------------------------------------
    # GENERATE QR
    # --------------------------------------------------------------------------

    @staticmethod
    def generate_qr(

        provider="",

        account_name="",

        account_no="",

        amount=0,

        sale_id="",

        raw_payload=None

    ):


        # ==================================================
        # MODE 1
        # PROVIDER RAW PAYLOAD
        # ==================================================

        if raw_payload:


            payload = raw_payload.strip()



        # ==================================================
        # MODE 2
        # INFORMATION QR
        # ==================================================

        else:


            amount_value = float(
                amount or 0
            )


            payload = (

                f"{provider.upper()} PAYMENT\n"

                f"--------------------\n"

                f"NAME: {account_name}\n"

                f"ACCOUNT: {account_no}\n"

                f"AMOUNT: {amount_value:,.0f} MMK\n"

                f"SALE ID: {sale_id}\n"

                f"--------------------\n"

                f"Thank You"

            )



        qr = qrcode.QRCode(

            version=None,

            error_correction=ERROR_CORRECT_M,

            box_size=10,

            border=4

        )


        qr.add_data(
            payload
        )


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
    # GET PAYLOAD FOR DEBUG
    # --------------------------------------------------------------------------

    @staticmethod
    def get_payload(

        provider="",

        account_name="",

        account_no="",

        amount=0,

        sale_id="",

        raw_payload=None

    ):


        if raw_payload:

            return raw_payload.strip()



        amount_value = float(
            amount or 0
        )


        return (

            f"{provider.upper()} PAYMENT\n"

            f"NAME: {account_name}\n"

            f"ACCOUNT: {account_no}\n"

            f"AMOUNT: {amount_value:,.0f} MMK\n"

            f"SALE ID: {sale_id}"

        )
