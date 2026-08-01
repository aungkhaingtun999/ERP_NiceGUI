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
def extract_account(hex_data):

    try:

        marker = "60"


        pos = hex_data.find(
            marker
        )


        if pos == -1:
            return None


        data = hex_data[pos:]


        # 60 92xxxxxxxxxx d2
        start = data.find(
            "92"
        )


        end = data.find(
            "d2",
            start
        )


        if start >= 0 and end > start:

            account_hex = data[
                start+2:
                end
            ]


            return "0" + account_hex



    except Exception:

        pass


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
