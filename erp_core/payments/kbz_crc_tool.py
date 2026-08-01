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



        # remove final base64 padding only for searching
        clean = raw.rstrip("=")


        # KBZ CRC pattern
        # F + 12 chars at the end
        match = re.search(
            r"(F[A-Za-z0-9+]{12})$",
            clean
        )


        if match:


            crc = match.group(1)

            start = match.start()


            payload = clean[:start]


            # restore base64 padding
            padding = raw[len(clean):]


            payload = payload + padding



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

                "payload": data["payload"],

                "crc": data["crc"],

                "payload_length": len(data["payload"]),

                "crc_length": len(data["crc"])

            })


        return output
