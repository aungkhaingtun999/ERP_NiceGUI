# ==============================================================================
# ERP ENTERPRISE KBZ QR ANALYZER v5.0
# KBZ Pay QR Binary TLV Decoder
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

            # remove checksum suffix after ==
            if '==' in raw:
                data = raw.split('==')[0] + '=='

            else:
                data = raw.split('F')[0]

            decoded = base64.b64decode(data)

            return decoded.hex()

        except Exception as e:

            print('BASE64 ERROR:', e)

            return None



    # ==========================================================================
    # ACCOUNT NUMBER
    # ==========================================================================
    @staticmethod
    def extract_account(hex_data):

        try:

            marker = '105716'

            pos = hex_data.find(marker)

            if pos == -1:
                return None

            start = pos + len(marker)

            account_hex = hex_data[start:start+14]

            digits = ''

            for i in range(0, len(account_hex), 2):

                byte = account_hex[i:i+2]

                digits += byte[0]

                if byte[1].lower() != 'f':
                    digits += byte[1]

            digits = ''.join(
                ch for ch in digits
                if ch.isdigit()
            )

            if digits.startswith('09'):
                return digits[:11]

            return digits

        except Exception as e:

            print('ACCOUNT ERROR:', e)

            return None



    # ==========================================================================
    # AMOUNT
    # ==========================================================================
    @staticmethod
    def extract_amount(hex_data):

        try:

            tag = '9f24'

            pos = hex_data.find(tag)

            if pos == -1:
                return None

            length = int(
                hex_data[pos+4:pos+6],
                16
            )

            value_hex = hex_data[
                pos+6:
                pos+6+(length*2)
            ]

            return bytes.fromhex(
                value_hex
            ).decode()

        except Exception as e:

            print('AMOUNT ERROR:', e)

            return None



    # ==========================================================================
    # MAIN ANALYZE
    # ==========================================================================
    @staticmethod
    def analyze(raw):

        result = {

            'provider': 'KBZ Pay',
            'raw': raw,
            'account_no': None,
            'amount': None,
            'valid': False,
            'decoded_hex': None

        }

        if not raw:
            return result

        hex_data = KBZQRAnalyzer.decode_base64_part(raw)

        result['decoded_hex'] = hex_data

        if not hex_data:
            return result

        result['account_no'] = KBZQRAnalyzer.extract_account(hex_data)

        result['amount'] = KBZQRAnalyzer.extract_amount(hex_data)

        if result['amount']:
            result['valid'] = True

        return result

