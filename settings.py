import random
import re
from datetime import datetime, date, timedelta
from os import getenv

from PIL import Image
from aiogram.fsm.state import State, StatesGroup
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


class InputMessage(StatesGroup):
    enter_admin_id = State()
    enter_message_mailing = State()
    enter_promo = State()
    enter_initials = State()
    enter_answer_fast_help = State()
    enter_answer_go_deeper = State()
    enter_email = State()
    enter_time_checkup = State()
    enter_timezone = State()
    edit_time_checkup = State()
    enter_answer_exercise = State()
    enter_promo_days = State()
    enter_max_activations_promo = State()


class AccountSettingsStates(StatesGroup):
    edit_name = State()
    edit_age = State()
    edit_gender = State()
    edit_email = State()
    edit_timezone = State()


start_referral_text = ("Помоги друзьям улучшить ментальное здоровье 🐿️\n\n"
                       "Просто поделись своим <b>уникальным промокодом</b>\n\n🥜 За одного приглашённого друга — 1 неделя"
                       " бесплатного использования.\n🥜 За 5 друзей — целый месяц в подарок.\n🥜 А если пригласишь"
                       " 10 друзей, получишь 3 месяца бесплатно.\n\n<b>А другу — неделя в подарок!</b> 🎁")

mechanic_checkup = (
    'Здесь ты можешь отслеживать своё состояние — <b>эмоциональное</b> и <b>продуктивное</b> — в динамике.\n\n'
    '📅Каждый день я буду присылать тебе сообщение в выбранное тобой время. В ответ — просто выбери одно из пяти эмодзи, которое лучше всего отражает твой день.\n\n'
    '📈В конце каждой <u>недели</u> ты получишь <b>наглядный график</b> — как менялось твое состояние по дням. Это поможет увидеть закономерности и вовремя отреагировать на спады.\n\n'
    '🗓️В конце <u>месяца</u> я пришлю тебе <b>календарь</b> с полной статистикой — весь месяц как на ладони: какой был ритм, где ты чувствовал(а) себя лучше всего.\n\n'
    '🏆А ещё — я выберу <b>лучшую</b> по состоянию <u>неделю</u> месяца и <b>отмечу</b> её <i>по завершении</i>. Так будет проще замечать, когда ты был(а) на пике — и что этому способствовало.\n\n',
    '\n🧡<b>Попробуем? Выбери</b>, за каким состоянием будем следить на этой неделе.')


async def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if re.match(email_regex, email):
        return True
    else:
        return False


def is_valid_time(time_str: str) -> bool:
    try:
        # Если формат 'HH:MM' некорректен, будет сгенерирован ValueError
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False


checkup_emotions_photo = FSInputFile("assets/checkup_emotions_photo.jpg")
checkup_productivity_photo = FSInputFile("assets/checkup_productivity_photo.jpg")

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

mechanic_dict = {
    "exercises_by_problem": "Здесь ты получаешь <b>персональные упражнения</b> — под своё состояние\n\n"
                            "👀Я внимательно слежу за твоими ответами и подбираю то, что может реально помочь именно "
                            "тебе.\n\nКаждое упражнение — это короткая практика, которая помогает лучше понять себя,"
                            " снизить напряжение или стать продуктивнее — в зависимости от того,"
                            " что мы обсуждали с тобой до этого.\n\n"
                            "📙А на каждое упражнение я даю короткую обратную связь — и"
                            " всегда готов обсудить его с тобой после.\n\n🧡<b>Попробуем?</b>"}

ai_temperature_text = ("Я также умею говорить прямо — без сюсюканья и лишней мягкости.\n\n🎯Если тебе комфортнее, когда"
                       " с тобой говорят по делу, чётко и без обёрток — просто включи прямолинейный режим.\n\nПример,"
                       " как я не буду:\n“Ты справляешься, даже если чувствуешь усталость."
                       " Всё ок, просто постарайся немного замедлиться.🐿️”\n\n Пример, как я буду:\n"
                       "“Ты выгорел, потому что сам себя загнал. Отдохни уже, а не героически страдай.”\n\n🌰"
                       "доступно только в платной версии.")

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

sub_description_photo = FSInputFile("assets/sub_description_photo.jpg")

you_fooher_photo = FSInputFile("assets/you_fooher_photo.jpg")

sub_description_photo2 = FSInputFile("assets/sub_description_photo2.jpg")

how_are_you_photo = FSInputFile("assets/how_are_you_photo.jpg")

photos_pages = {
    1: mental_helper_photo,
    2: exercises_photo,
    3: checkups_graphic_photo,
    4: checkups_types_photo,
    5: temperature_ai_photo,
    6: universal_ai_photo,
    7: payment_photo,
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
