import base64


class KBZQRAnalyzer:


    @staticmethod
    def analyze(qr_text):


        result = {

            "provider": "KBZ Pay",
            "raw": qr_text,
            "decoded": None,
            "valid": False

        }


        try:

            raw = qr_text.strip()


            # remove last checksum part
            parts = raw.split("F")


            for part in parts:


                if len(part) > 20:


                    try:

                        decoded = base64.b64decode(
                            part + "=="
                        )


                        result["decoded_hex"] = (
                            decoded.hex()
                        )


                        result["decoded_text"] = (
                            decoded.decode(
                                "utf-8",
                                errors="ignore"
                            )
                        )


                        result["valid"] = True


                    except:

                        pass



            return result


        except Exception as e:

            result["error"] = str(e)

            return result
