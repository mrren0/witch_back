import base64
import hashlib


class Encryption:

    @staticmethod
    def is_valid_token(phone: str, x_api_key: str, SALT_BEELINE: str) -> bool:
        if x_api_key == Encryption.hash_str(phone, SALT_BEELINE):
            return True
        return False

    @staticmethod
    def hash_str(*args: str) -> str:
        concatenated_str = ''.join(args).encode('utf-8')
        hash_result = hashlib.sha1(concatenated_str).hexdigest()
        return hash_result

    @staticmethod
    def encoded(string):
        encoded_bytes = base64.b64encode(string.encode("utf-8"))
        encoded_string = encoded_bytes.decode("utf-8")
        return encoded_string
