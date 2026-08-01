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
    def extract_account(hex_data):

        try:

            marker = "57"

            pos = hex_data.find(marker)


            if pos == -1:
                return None


            # skip tag + length
            value_start = pos + 4


            # length byte
            length_hex = hex_data[
                pos + 2 :
                pos + 4
            ]


            length = int(
                length_hex,
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


            # remove non-number chars
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
