from os import getenv

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

main_bot_token = getenv("MAIN_BOT_TOKEN")
admin_bot_token = getenv("ADMIN_BOT_TOKEN")
business_connection_id = getenv("BUSINESS_CONNECTION_ID")
openai_api_key = getenv("GPT_TOKEN")
gemini_api_key = getenv("GEMINI_API_KEY")

yookassa_shop_id = getenv("SHOP_ID")
yookassa_shop_secret_key = getenv("SECRET_KEY")

