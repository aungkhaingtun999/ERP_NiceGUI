# ==============================================================================
# ERP ENTERPRISE KBZ CRC ENGINE v2.0
#
# KBZ QR CRC Research Engine
# ==============================================================================


import binascii


class KBZCRCEngine:


    # ==========================================================================
    # CRC CANDIDATES
    # ==========================================================================

    @staticmethod
    def crc16_ccitt(data):

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
    def crc32(data):

        return format(
            binascii.crc32(data) & 0xffffffff,
            "08X"
        )



    # ==========================================================================
    # TEST GENERATOR
    # ==========================================================================

    @staticmethod
    def calculate_candidates(payload):


        data = payload.encode(
            "utf-8"
        )


        return {

            "CRC16_CCITT":

                KBZCRCEngine.crc16_ccitt(
                    data
                ),


            "CRC32":

                KBZCRCEngine.crc32(
                    data
                )

        }



    # ==========================================================================
    # COMPARE
    # ==========================================================================

    @staticmethod
    def compare(
        payload,
        expected_crc
    ):


        candidates = (
            KBZCRCEngine.calculate_candidates(
                payload
            )
        )


        matched = []


        for name, value in candidates.items():

            if value in expected_crc:

                matched.append(
                    name
                )



        return {

            "payload":
                payload,

            "expected_crc":
                expected_crc,

            "candidates":
                candidates,

            "matched":
                matched

        }
