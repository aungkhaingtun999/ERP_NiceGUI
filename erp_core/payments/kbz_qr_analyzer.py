# ==============================================================================
# ERP ENTERPRISE KBZ QR ANALYZER v4.0
# KBZ Pay QR Binary TLV Decoder
# ==============================================================================

import base64
import re


class KBZQRAnalyzer:


    # ==========================================================================
    # BASE64 DECODE
    # ==========================================================================
    @staticmethod
    def decode_base64_part(raw):

        try:

            if not raw:
                return None

            # keep only base64 part
            if '==' in raw:
                data = raw.split('==')[0] + '=='

            elif '=' in raw:
                data = raw.split('=')[0] + '='

            else:
                data = raw

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

            text = bytes.fromhex(hex_data).decode(
                errors='ignore'
            )

            match = re.search(r'09\d{9}', text)

            if match:
                return match.group(0)

            return None

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

            return bytes.fromhex(value_hex).decode()

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

