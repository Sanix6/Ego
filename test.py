import json
import uuid
import hmac
import hashlib
import base64
import logging
from decimal import Decimal

import requests


NAMBA_BASE_URL = "https://api.nambaone.app/"
NAMBA_MERCHANT_ID = "a8ca74d3-29a7-44ff-9040-afa6437cfc12"
NAMBA_SECRET = "w6WTYKyhWrifBUt_EL4sPpo47STGDb-TjSzK"

WEBHOOK_URL = "https://ego.kg/api/payment/webhook/namba/"
LOG_FILE = "namba_payment_test.log"

import requests
import uuid
import json
import hmac
import hashlib
import base64
import traceback
from datetime import datetime
from decimal import Decimal



def write_log(title, data=None):
    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write("\n" + "=" * 80 + "\n")
        file.write(f"{datetime.now()} | {title}\n")
        file.write("=" * 80 + "\n")

        if data is not None:
            if isinstance(data, (dict, list)):
                file.write(json.dumps(data, ensure_ascii=False, indent=4))
            else:
                file.write(str(data))

        file.write("\n")


def generate_signature(secret: str, path: str, body: str, salt: str) -> str:
    message = f"{path}{body}{salt}"

    digest = hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha512
    ).digest()

    return base64.b64encode(digest).decode("utf-8")


def create_namba_payment(amount_som: str):
    external_id = str(uuid.uuid4())

    path = f"/public/merchant/payment/v2/{NAMBA_MERCHANT_ID}/one-time"
    url = f"{NAMBA_BASE_URL}{path}"

    amount_tyiyn = int(Decimal(amount_som) * 100)

    payload = {
        "externalId": external_id,
        "webhookUrl": WEBHOOK_URL,
        "amount": str(amount_tyiyn),
        "amountCanBeChanged": False
    }

    body = json.dumps(payload, separators=(",", ":"))
    salt = str(uuid.uuid4())

    signature = generate_signature(
        secret=NAMBA_SECRET,
        path=path,
        body=body,
        salt=salt
    )

    headers = {
        "Content-Type": "application/json",
        "x-merchant-api-salt": salt,
        "x-merchant-api-signature": signature
    }

    write_log("NAMBA REQUEST", {
        "method": "POST",
        "url": url,
        "path": path,
        "external_id": external_id,
        "amount_som": amount_som,
        "amount_tyiyn": amount_tyiyn,
        "payload": payload,
        "body": body,
        "headers": headers
    })

    try:
        response = requests.post(
            url,
            data=body,
            headers=headers,
            timeout=15
        )

        write_log("NAMBA RAW RESPONSE", {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "text": response.text
        })

        try:
            response_json = response.json()
        except Exception:
            response_json = None

        write_log("NAMBA JSON RESPONSE", response_json)

        response.raise_for_status()

        return response_json

    except Exception as e:
        write_log("NAMBA ERROR", {
            "error": str(e),
            "traceback": traceback.format_exc()
        })
        raise


if __name__ == "__main__":
    result = create_namba_payment("10")

    print("RESULT:")
    print(json.dumps(result, ensure_ascii=False, indent=4))