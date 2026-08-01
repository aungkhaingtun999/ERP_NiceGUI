# ==============================================================================
# ERP ENTERPRISE KBZ QR ANALYZER v2.0
#
# KBZ Pay QR Binary TLV Decoder
# ==============================================================================


import base64


class KBZQRAnalyzer:


    # ==========================================================================
    # HEX CONVERT
    # ==========================================================================
@staticmethod
def decode_base64_part(raw):

    try:

        # Remove CRC suffix
        if "==" in raw:

            data = raw.split("==")[0] + "=="


        elif "=" in raw:

            data = raw.split("=")[0] + "="


        else:

            data = raw



        decoded = base64.b64decode(
            data
        )


        return decoded.hex()


    except Exception as e:

        print(
            "BASE64 ERROR:",
            e
        )

        return None



    # ==========================================================================
    # FIND ACCOUNT
    # ==========================================================================

    @staticmethod
    def extract_account(hex_data):

        try:

            # Example:
            # 71609267772367

            start = hex_data.find(
                "609"
            )


            if start >= 0:

                account = hex_data[
                    start+1:
                    start+13
                ]

                return account


        except Exception:

            pass


        return None




    # ==========================================================================
    # FIND AMOUNT
    # ==========================================================================

    @staticmethod
    def extract_amount(hex_data):


        try:

            # TLV amount tag
            tag = "9f24"


            pos = hex_data.find(
                tag
            )


            if pos == -1:

                return None



            length = int(

                hex_data[
                    pos+4:
                    pos+6
                ],

                16

            )



            value_hex = hex_data[

                pos+6:

                pos+6+(length*2)

            ]



            amount = bytes.fromhex(

                value_hex

            ).decode()



            return amount



        except Exception:


            return None




    # ==========================================================================
    # MAIN ANALYZE
    # ==========================================================================

    @staticmethod
    def analyze(raw):


        result = {

            "provider":
            "KBZ Pay",

            "raw":
            raw,

            "account_no":
            None,

            "amount":
            None,

            "valid":
            False,

            "decoded":
            None,

            "decoded_hex":
            None

        }



        if not raw:

            return result



        hex_data = KBZQRAnalyzer.decode_base64_part(
            raw
        )


        result["decoded_hex"] = hex_data



        if not hex_data:

            return result



        account = KBZQRAnalyzer.extract_account(
            hex_data
        )


        amount = KBZQRAnalyzer.extract_amount(
            hex_data
        )



        result["account_no"] = account

        result["amount"] = amount



        result["valid"] = True



        return result
