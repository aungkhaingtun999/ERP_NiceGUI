# ==============================================================================
# ERP ENTERPRISE KBZ CRC TOOL v3.0
# ==============================================================================


import re


class KBZCRCTool:


    @staticmethod
    def split_crc(raw):


        result = {
            "payload": raw,
            "crc": ""
        }


        if not raw:
            return result



        # KBZ CRC pattern
        # F + 12 chars
        match = re.search(
            r"(F[A-Za-z0-9+]{12})$",
            raw
        )


        if match:


            crc = match.group(1)


            index = match.start()


            payload = raw[:index]


            result["payload"] = payload

            result["crc"] = crc



        return result



    @staticmethod
    def analyze_samples(samples):


        output = []


        for raw in samples:


            data = KBZCRCTool.split_crc(
                raw.strip()
            )


            output.append({

                "raw": raw,

                "payload":
                    data["payload"],

                "crc":
                    data["crc"],

                "payload_length":
                    len(data["payload"]),

                "crc_length":
                    len(data["crc"])

            })


        return output
