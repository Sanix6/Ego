import threading
import requests
from django.core.mail import EmailMessage
import os

NIKITA_LOGIN = os.getenv("NIKITA_LOGIN")
NIKITA_PASSWORD = os.getenv("NIKITA_PASSWORD")
NIKITA_SENDER = os.getenv("NIKITA_SENDER")

def send_sms(phone, message, code):
    new_phone = "".join(filter(str.isdigit, phone))
    xml_data = f"""<?xml version="1.0" encoding="UTF-8"?><message><login>{NIKITA_LOGIN}</login><pwd>{NIKITA_PASSWORD}</pwd><sender>{NIKITA_SENDER}</sender><text>{message} {code}</text><phones><phone>{new_phone}</phone></phones></message>"""

    headers = {"Content-Type": "application/xml"}

    url = "https://smspro.nikita.kg/api/message"

    response = requests.post(url, data=xml_data.encode("utf-8"), headers=headers)

    print(f"\n\n{response.text}\n\n")

    # with open("logs/nikita.txt", "a") as file:
    #     file.write(f"{response.text} - {new_phone}")

    if response.status_code == 200:
        return True
    return False


def send_verification_sms(user):
    code = user.generate_code()
    message = "Ваш код подтверждения:"
    return send_sms(user.phone, message, code)