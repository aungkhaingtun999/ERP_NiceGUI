# ==============================================================================
# ERP ENTERPRISE KBZ QR ANALYZER v3.2
#
# KBZ Pay QR Binary TLV Decoder
# ==============================================================================


import base64



class KBZQRAnalyzer:



    # ==========================================================================
    # BASE64 DECODE
    # ==========================================================================

    @staticmethod
    def decode_base64_part(raw):

        try:

            if not raw:
                return None


            # remove CRC suffix
            if "==" in raw:

                data = raw.split("==")[0] + "=="


            else:

                data = raw.split("F")[0]



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
    # ACCOUNT NUMBER
    # ==========================================================================

    @staticmethod
    def extract_account(hex_data):

        try:


            # KBZ account TLV
            marker = "5716"



            pos = hex_data.find(
                marker
            )



            if pos == -1:

                return None




            # after 5716
            account_hex = hex_data[

                pos + 4 :

                pos + 4 + 24

            ]



            account = bytes.fromhex(

                account_hex

            ).decode(

                errors="ignore"

            )



            # only number

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

                    pos + 4 :

                    pos + 6

                ],

                16

            )



            value_hex = hex_data[

                pos + 6 :

                pos + 6 + (length * 2)

            ]



            amount = bytes.fromhex(

                value_hex

            ).decode()



            return amount




        except Exception as e:


            print(
                "AMOUNT ERROR:",
                e
            )


            return None




    # ==========================================================================
    # ANALYZE
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
