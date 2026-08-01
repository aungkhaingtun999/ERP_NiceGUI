# ==============================================================================
# ERP ENTERPRISE KBZ QR ANALYZER v3.1
# KBZ Pay QR Binary TLV Decoder
# ==============================================================================


import base64


class KBZQRAnalyzer:


    # ==========================================================================
    # BASE64 DECODE
    # ==========================================================================
    @staticmethod
    def extract_account(hex_data):

        try:

        # known KBZ phone pattern
               
            for number in [
            "09267772367"
        ]:

            encoded = number.encode().hex()

                if encoded in hex_data:

                    return number



                    # TLV search
                    marker = "5716"

        pos = hex_data.find(marker)

              if pos == -1:
                  return None


        part = hex_data[
            pos+4:
            pos+40
        ]


        text = bytes.fromhex(
            part
        ).decode(
            errors="ignore"
        )


        digits = "".join(
            x for x in text
            if x.isdigit()
        )


            return digits or None



        except Exception:

            return None

    # ==========================================================================
    # ACCOUNT NUMBER
    # ==========================================================================

    @staticmethod
    def extract_account(hex_data):

        try:

            marker = "57"


            pos = hex_data.find(
                marker
            )


            if pos == -1:
                return None



            # tag + length skip
            value_start = pos + 4


            length = int(

                hex_data[
                    pos+2:
                    pos+4
                ],

                16

            )


            value_hex = hex_data[

                value_start:

                value_start + (length * 2)

            ]



            account = bytes.fromhex(

                value_hex

            ).decode(

                errors="ignore"

            )


            account = "".join(

                x for x in account

                if x.isdigit()

            )


            return account



        except Exception as e:

            print(
                "ACCOUNT ERROR:",
                e
            )

            return None




    # ==========================================================================
    # AMOUNT
    # ==========================================================================

    @staticmethod
    def extract_amount(hex_data):

        try:

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


            return bytes.fromhex(

                value_hex

            ).decode()



        except Exception as e:

            print(
                "AMOUNT ERROR:",
                e
            )

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



        hex_data = KBZQRAnalyzer.decode_base64_part(
            raw
        )


        result["decoded_hex"] = hex_data



        if not hex_data:

            return result



        result["account_no"] = KBZQRAnalyzer.extract_account(
            hex_data
        )


        result["amount"] = KBZQRAnalyzer.extract_amount(
            hex_data
        )


        if result["amount"]:

            result["valid"] = True



        return result
