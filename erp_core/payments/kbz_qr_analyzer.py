# ==============================================================================
# ERP ENTERPRISE KBZ QR ANALYZER v1.0
#
# Decode KBZ Pay QR Payload
#
# ==============================================================================


import base64
import re


class KBZQRAnalyzer:


    # ==========================================================================
    # MAIN ANALYZE
    # ==========================================================================

    @staticmethod
    def analyze(qr_text):


        result = {

            "provider": "KBZ Pay",

            "raw": qr_text,

            "account_no": None,

            "amount": None,

            "valid": False

        }



        try:


            # ----------------------------------------------------------
            # Remove spaces
            # ----------------------------------------------------------

            qr_text = qr_text.strip()



            # ----------------------------------------------------------
            # Decode Base64 Part
            # ----------------------------------------------------------

            decoded = ""


            try:

                decoded_bytes = base64.b64decode(
                    qr_text
                )

                decoded = decoded_bytes.decode(
                    "utf-8",
                    errors="ignore"
                )


            except Exception:

                decoded = qr_text



            result["decoded"] = decoded



            # ----------------------------------------------------------
            # Find Account
            # ----------------------------------------------------------

            account_match = re.search(

                r'(09\d{8,10})',

                decoded

            )


            if account_match:

                result["account_no"] = (
                    account_match.group(1)
                )



            # ----------------------------------------------------------
            # Find Amount
            # ----------------------------------------------------------

            amount_match = re.search(

                r'(\d+\.\d+)',

                decoded

            )


            if amount_match:

                result["amount"] = (
                    amount_match.group(1)
                )



            # ----------------------------------------------------------
            # Validation
            # ----------------------------------------------------------

            if (
                result["account_no"]
                or
                result["amount"]
            ):

                result["valid"] = True



            return result



        except Exception as e:


            result["error"] = str(e)


            return result
