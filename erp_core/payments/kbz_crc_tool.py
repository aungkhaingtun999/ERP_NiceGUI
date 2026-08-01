# ==============================================================================
# ERP ENTERPRISE KBZ CRC TOOL v2.0
# ==============================================================================


class KBZCRCTool:


    @staticmethod
    def split_crc(raw):

        if not raw:
            return {
                "payload": "",
                "crc": ""
            }


        # KBZ CRC starts after base64 payload padding
        # find last '=' padding

        pos = raw.rfind("=")


        if pos >= 0:

            payload = raw[:pos+1]

            crc = raw[pos+1:]


        else:

            # no padding
            # CRC normally starts at last F marker

            marker = raw.rfind("F")


            if marker > 0:

                payload = raw[:marker]

                crc = raw[marker:]


            else:

                payload = raw

                crc = ""



        return {

            "payload": payload,

            "crc": crc

        }



    @staticmethod
    def analyze_samples(samples):


        result = []


        for raw in samples:


            data = KBZCRCTool.split_crc(
                raw.strip()
            )


            result.append({

                "raw": raw,

                "payload": data["payload"],

                "crc": data["crc"],

                "payload_length": len(data["payload"]),

                "crc_length": len(data["crc"])

            })


        return result
