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
