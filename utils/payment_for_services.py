import asyncio
from os import getenv

from dotenv import load_dotenv, find_dotenv
from requests import HTTPError
from yookassa import Configuration, Payment


load_dotenv(find_dotenv("../.env"))
Configuration.account_id = getenv("SHOP_ID")
Configuration.secret_key = getenv("SECRET_KEY")

async def create_payment(email: str,
                         amount: str,
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


async def check_payment(payment_id):
    payment = Payment.find_one(payment_id)
    return payment.status == 'succeeded'