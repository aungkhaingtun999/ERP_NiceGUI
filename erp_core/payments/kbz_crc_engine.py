# ==============================================================================
# ERP ENTERPRISE KBZ CRC ENGINE v3.0
# ==============================================================================


import binascii



class KBZCRCEngine:



    @staticmethod
    def crc16_ccitt_false(data):


        crc = 0xFFFF


        for byte in data:


            crc ^= byte << 8


            for _ in range(8):


                if crc & 0x8000:

                    crc = (
                        crc << 1
                    ) ^ 0x1021


                else:

                    crc <<= 1



                crc &= 0xFFFF



        return format(
            crc,
            "04X"
        )




    @staticmethod
    def crc16_xmodem(data):


        crc = 0x0000


        for byte in data:


            crc ^= byte << 8


            for _ in range(8):


                if crc & 0x8000:

                    crc = (
                        crc << 1
                    ) ^ 0x1021


                else:

                    crc <<= 1



                crc &= 0xFFFF



        return format(
            crc,
            "04X"
        )




    @staticmethod
    def crc32(data):


        return format(

            binascii.crc32(data)
            &
            0xffffffff,

            "08X"

        )
import hashlib


class KBZCRCEngine:

    ...

    # =====================================================
    # HASH TRUNCATION TEST
    # =====================================================

    @staticmethod
    def hash_truncation_test(hex_data):

        data = bytes.fromhex(hex_data)

        sha1 = hashlib.sha1(data).hexdigest()
        md5 = hashlib.md5(data).hexdigest()

        return {

            "SHA1_FULL": sha1,

            "SHA1_FIRST_12": sha1[:12].upper(),

            "SHA1_LAST_12": sha1[-12:].upper(),

            "MD5_FULL": md5,

            "MD5_FIRST_12": md5[:12].upper(),

            "MD5_LAST_12": md5[-12:].upper()

        }
        


    # =====================================================
    # DECODED HEX CRC TEST
    # =====================================================

    @staticmethod
    def crc16_variants(hex_data):


        data = bytes.fromhex(
            hex_data
        )


        return {


            "CRC16_CCITT_FALSE":

                KBZCRCEngine.crc16_ccitt_false(
                    data
                ),


            "CRC16_XMODEM":

                KBZCRCEngine.crc16_xmodem(
                    data
                ),


            "CRC32":

                KBZCRCEngine.crc32(
                    data
                )

        }




    # =====================================================
    # PAYLOAD TEST
    # =====================================================

    @staticmethod
    def compare(
        payload,
        expected_crc
    ):


        data = payload.encode(
            "utf-8"
        )


        return {


            "expected_crc":

                expected_crc,


            "CRC16_CCITT_FALSE":

                KBZCRCEngine.crc16_ccitt_false(
                    data
                ),


            "CRC16_XMODEM":

                KBZCRCEngine.crc16_xmodem(
                    data
                ),


            "CRC32":

                KBZCRCEngine.crc32(
                    data
                )

        }

    # =====================================================
    # CRC RANGE SCANNER
    # =====================================================

    @staticmethod
    def scan_hex_ranges(hex_data):


        results = {}


        ranges = {


            "FULL":

                hex_data,


            "REMOVE_FIRST_BYTE":

                hex_data[2:],


            "REMOVE_FIRST_4":

                hex_data[8:],


            "BEFORE_AMOUNT_TAG":

                hex_data.split(
                    "9f24"
                )[0],


        }



        for name, value in ranges.items():


            try:

                results[name] = {

                    "HEX_LENGTH":
                        len(value),


                    "CRC16_CCITT_FALSE":
                        KBZCRCEngine.crc16_ccitt_false(
                            bytes.fromhex(value)
                        ),


                    "CRC16_XMODEM":
                        KBZCRCEngine.crc16_xmodem(
                            bytes.fromhex(value)
                        ),


                    "CRC32":
                        KBZCRCEngine.crc32(
                            bytes.fromhex(value)
                        )

                }


            except Exception as e:


                results[name] = str(e)



        return results
    # =====================================================
    # CRC STRING ANALYZER
    # =====================================================

    @staticmethod
    def analyze_crc_string(crc_string):

        if not crc_string:

            return {"error": "empty"}


        return {

            "raw": crc_string,

            "length": len(crc_string),

            "prefix": crc_string[0],

            "body": crc_string[1:],

            "body_length": len(crc_string[1:]),

            "contains_plus": "+" in crc_string,

            "contains_equal": "=" in crc_string,

            "is_hex_body": all(
                c in "0123456789abcdefABCDEF"
                for c in crc_string[1:]
            )

        }
        
    # =====================================================
    # CRC BODY TO INTEGER
    # =====================================================

    @staticmethod
    def crc_body_info(crc_string):

        body = crc_string[1:]

        if all(c in "0123456789abcdefABCDEF" for c in body):

            return {

                "body": body,

                "hex_int": int(body, 16),

                "bit_length": int(body, 16).bit_length()

            }

        return {

            "body": body,

            "hex_int": None,

            "bit_length": None

        }
        
        # =====================================================
    # PAYLOAD TAIL COMPARE
    # =====================================================

    @staticmethod
    def payload_tail_compare(hex_data, crc_string):

        body = crc_string[1:]

        if not all(c in "0123456789abcdefABCDEF" for c in body):

            return {
                "error": "CRC body is not hex"
            }

        crc_bytes = body.lower()

        return {

            "payload_tail_12": hex_data[-12:].lower(),

            "payload_tail_16": hex_data[-16:].lower(),

            "payload_tail_24": hex_data[-24:].lower(),

            "crc_body": crc_bytes,

            "tail12_match": hex_data[-12:].lower() == crc_bytes,

            "tail16_contains": crc_bytes in hex_data[-16:].lower(),

            "tail24_contains": crc_bytes in hex_data[-24:].lower()

        }
        
