import hmac
import hashlib
import base64


class NambaSignatureService:

    @staticmethod
    def generate_signature(secret, path, body, salt):
        message = f"{path}{body}{salt}"

        signer = hmac.new(
            key=secret.encode(),
            msg=message.encode(),
            digestmod=hashlib.sha512
        )

        return base64.b64encode(signer.digest()).decode()