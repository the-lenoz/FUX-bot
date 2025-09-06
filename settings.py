import json
from datetime import timedelta
from os import getenv

from PIL import Image
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import FSInputFile
from dotenv import load_dotenv, find_dotenv

storage_bot = MemoryStorage()
storage_admin_bot = MemoryStorage()

load_dotenv(find_dotenv())

token_design_level = getenv("MAIN_BOT_TOKEN")
token_admin_bot = getenv("ADMIN_BOT_TOKEN")
business_connection_id = getenv("BUSINESS_CONNECTION_ID")
openai_api_key = getenv("GPT_TOKEN")
gemini_api_key = getenv("GEMINI_API_KEY")

DEFAULT_TIMEZONE = timedelta(hours=3)


SUBSCRIPTION_PLANS = {
    7: 249,
    30: 490,
    90: 990
}

SUBSCRIPTION_WORDS = {
    7: ("недельная", "неделю"),
    30: ("месячная", "месяц"),
    90: ("трёхмесячная", "три месяца")
}

POWER_MODE_DAY_DISCOUNT = 0.015

MAX_DAYS_FREEZE = 3


with open("messages.json") as messages_file:
    messages_dict = json.load(messages_file)

emoji_dict = {
    1: "😖",  # самый недовольный
    2: "😒",  # недовольный
    3: "😐",  # нейтральный
    4: "😌",  # спокойный
    5: "🤩"  # в восторге
}

speed_dict = {
    1: "🪵",  # полено — вообще не движется
    2: "🐌",  # улитка — очень медленно
    3: "🚲",  # велосипед — средне
    4: "🚗",  # машина — быстро
    5: "🚀"  # ракета — очень быстро
}

calendar_template_photo = Image.open(
    "assets/calendar_template.png"
).resize((1340, 1340))

mental_helper_photo = FSInputFile("assets/mental_helper_photo.jpg")
exercises_photo = FSInputFile("assets/exercises_photo.jpg")
checkups_graphic_photo = FSInputFile("assets/checkups_graphic_photo.jpg")
checkups_types_photo = FSInputFile("assets/checkups_types_photo.jpg")
temperature_ai_photo = FSInputFile("assets/temperature_ai_photo.jpg")
universal_ai_photo = FSInputFile("assets/universal_ai_photo.jpg")
payment_photo = FSInputFile("assets/payment_photo.jpg")
menu_photo = FSInputFile("assets/menu_photo.jpg")
system_setting_photo = FSInputFile("assets/system_setting_photo.jpg")
sub_description_photo_before = FSInputFile("assets/sub_description_photo_before.jpg")
you_fooher_photo = FSInputFile("assets/you_fooher_photo.jpg")
sub_description_photo_after = FSInputFile("assets/sub_description_photo_after.jpg")
how_are_you_photo = FSInputFile("assets/how_are_you_photo.jpg")
checkup_emotions_photo = FSInputFile("assets/checkup_emotions_photo.jpg")
checkup_productivity_photo = FSInputFile("assets/checkup_productivity_photo.jpg")
premium_sub_photo = FSInputFile("assets/premium_sub_photo.jpg")

productivity_emoji_description_photo = FSInputFile("assets/productivity_emoji_description_photo.jpg")
emotions_emoji_description_photo = FSInputFile("assets/emotions_emoji_description_photo.jpg")
emoji_description_photo = FSInputFile("assets/emoji_description_photo.jpg")

photos_pages = {
    1: mental_helper_photo,
    2: exercises_photo,
    3: emoji_description_photo,
    4: checkups_graphic_photo,
    5: temperature_ai_photo,
    6: universal_ai_photo,
    7: sub_description_photo_before,
    8: system_setting_photo
}

table_names = [
    "admins",
    "ai_requests",
    "checkups",
    "days_checkups",
    "events",
    "exercises_user",
    "fast_help",
    "fast_help_dialogs",
    "go_deeper",
    "go_deeper_dialogs",
    "mental_problems",
    "operations",
    "promo_activations",
    "recommendations_user",
    "referral_system",
    "subscriptions",
    "summary_user",
    "users"
]

