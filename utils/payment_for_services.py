from dotenv import load_dotenv, find_dotenv
from requests import HTTPError
from yookassa import Configuration, Payment

from data.secrets import yookassa_shop_id, yookassa_shop_secret_key

load_dotenv(find_dotenv("../.env"))
Configuration.account_id = yookassa_shop_id
Configuration.secret_key = yookassa_shop_secret_key

async def create_payment(email: str,
                         amount: int,
                         currency: str = "RUB",
                         description: str = "Оплата подписки на ai ассистента по ментальному состоянию",
                         return_url: str = "https://t.me/FuhMentalBot"):
    try:
        payment = Payment.create({
            "amount": {
                "value": str(amount),
                "currency": currency
            },
            "confirmation": {
                "type": "redirect",
                "return_url": return_url
            },
            "capture": True,
            "description": description,
            "save_payment_method": True,
            "receipt": {
                "customer": {
                    "email": email
                },
                "items": [
                    {
                        "description": description,
                        "quantity": "1.00",
                        "amount": {
                            "value": amount,
                            "currency": currency
                        },
                        "vat_code": "4",
                        "payment_subject": "service",
                        "payment_mode": "full_payment"
                    }

                ]
            }

        })
        return payment.id, payment.confirmation.confirmation_url

    except HTTPError as e:
        print(e.response.text)

async def get_payment(payment_id):
    return Payment.find_one(payment_id)

async def check_payment(payment_id):
    payment = Payment.find_one(payment_id)
    return payment.status == 'succeeded'

async def get_payment_method_id(payment_id):
    payment = Payment.find_one(payment_id)
    if payment.payment_method.saved:
        return payment.payment_method.id
    else:
        return None



async def charge_subscriber(payment_method_id: str, amount: int, email: str):
    try:
        payment = Payment.create({
            "amount": {
                "value": "%.2f" % amount,
                "currency": "RUB"
            },
            "capture": True,
            "payment_method_id": payment_method_id,
            "description": "Оплата подписки на ai ассистента по ментальному состоянию",
            "receipt": {
                "customer": {
                    "email": email
                },
                "items": [
                    {
                        "description": "Оплата подписки на ai ассистента по ментальному состоянию",
                        "quantity": "1.00",
                        "amount": {
                            "value": amount,
                            "currency": "RUB"
                        },
                        "vat_code": "4",
                        "payment_subject": "service",
                        "payment_mode": "full_payment"
                    }

                ]
            }
        })
        return payment.id
    except HTTPError as e:
        print(e.response.text)

