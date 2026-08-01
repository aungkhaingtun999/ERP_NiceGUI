# ==============================================================================
# ERP ENTERPRISE KBZ QR ANALYZER v3.0
#
# KBZ Pay QR Binary TLV Decoder
#
# Features:
# - Base64 Payload Decode
# - Account Number Extract
# - Amount Extract
# - QR Validation
#
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



            # Remove CRC suffix
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


            # Account field marker
            marker = "57"


            pos = hex_data.find(
                marker
            )


            if pos == -1:

                return None



            data = hex_data[
                pos + 2:
            ]



            # next TLV tag
            end = data.find(
                "d2"
            )



            if end == -1:

                return None



            account_hex = data[
                :end
            ]



            account = bytes.fromhex(

                account_hex

            ).decode()



            return account



        except Exception as e:


            print(
                "ACCOUNT PARSE ERROR:",
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

                "AMOUNT PARSE ERROR:",
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




        if not raw:

            return result





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





        if result["account_no"] or result["amount"]:

            result["valid"] = True





        return result
