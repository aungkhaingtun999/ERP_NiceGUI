# ==============================================================================
# ERP ENTERPRISE KBZ CRC TOOL v1.0
#
# Analyze KBZ QR checksum suffix
# ==============================================================================


class KBZCRCTool:


    @staticmethod
    def split_qr(raw):

        result = {
            'payload': None,
            'crc': None
        }


        if not raw:
            return result


        if '==' in raw:

            pos = raw.find('==') + 2

            result['payload'] = raw[:pos]

            result['crc'] = raw[pos:]

            return result


        if '=' in raw:

            pos = raw.find('=') + 1

            result['payload'] = raw[:pos]

            result['crc'] = raw[pos:]

            return result


        result['payload'] = raw

        result['crc'] = ''

        return result



    @staticmethod
    def analyze_samples(samples):

        rows = []


        for raw in samples:

            parts = KBZCRCTool.split_qr(raw)

            rows.append({
                'raw': raw,
                'payload': parts['payload'],
                'crc': parts['crc'],
                'payload_length': len(parts['payload'] or ''),
                'crc_length': len(parts['crc'] or '')
            })


        return rows
