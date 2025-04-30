import random
import re
from datetime import datetime, date, timedelta
from os import getenv

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv, find_dotenv

storage_bot = MemoryStorage()
storage_admin_bot = MemoryStorage()


load_dotenv(find_dotenv("../.env"))
token_design_level = getenv("MAIN_BOT_TOKEN")
token_admin_bot = getenv("ADMIN_BOT_TOKEN")
business_connection_id = getenv("BUSINESS_CONNECTION_ID")
redis_host = getenv("HOST")

fast_help_promt = """Сгенерируй ТОЛЬКО ОДИН вопрос о ментальном состоянии человека,
 при этом сосредоточившись на узкой, конкретной проблеме(Если ты видишь, что человек в диалоге выше написал про
  какую-то проблему, то ты должен подбодрить и немного посочувствовать, а также уже после этого через отсутпив абзац(строку) задать
   вопрос). ВОПРОС ДОЛЖНЕ БЫТЬ ОДИН И ВСЕ!!! Вот список проблем, по которым можешь задавать
  вопросы(вопрос должен быть один и только на одну конкретную проблему)
 1. Самооценка
2. Эмоции
3. Отношения
4. Любовь 
5. Карьера
6. Финансы
7. Здоровье
8. Самореализация
9. Выгорание
10. Духовность
Учитывай предыдущие пять вопросов и не повторяй их(если вдруг видишь что-то неприемлемое, то просто не обращай
 внимания и генерируй вопрос на одну из проблем)"""

go_deeper_promt = """Выступай в роли ассистента, который свободно общается с пользователем о его ментальном состоянии,
 самочувствии и всём, что с этим связано.Желательно, если ты будешь общаться затрагивая такие проблемы, как:
1. Самооценка
2. Эмоции
3. Отношения
4. Любовь 
5. Карьера
6. Финансы
7. Здоровье
8. Самореализация
9. Выгорание
10. Духовность
Если ты хочешь задать какой-то вопрос, то сгенерируй ТОЛЬКО ОДИН вопрос и не более, сосредоточившись на какой-то одной теме
  При этом учитывай контекст предыдущих сообщений. Если в чате нет никаких
  сообщений или пользователь ничего не сказал о своих переживаниях, инициируй беседу, задав уточняющие или дружелюбные
   вопросы, чтобы помочь человеку раскрыться и обсудить его текущее состояние"""


class InputMessage(StatesGroup):
    enter_admin_id = State()
    enter_message_mailing = State()
    enter_promo = State()
    enter_initials = State()
    enter_answer_fast_help = State()
    enter_answer_go_deeper = State()
    enter_email = State()
    enter_time_checkup = State()
    edit_time_checkup = State()
    enter_answer_exercise = State()
    enter_promo_days = State()
    enter_max_activations_promo = State()

mechanic_text = ("🐿️Что я умею? \n\n■ Моделировать психологические сессии – в 4 раза дешевле, чем обычная консультация!"
                 " \n\n■ Давать полезные упражнения – чтобы ты не уходил с пустыми руками. "
                 "\n\n■ Отслеживать твое состояние – собираю статистику и показываю тебе динамику за неделю и месяц."
                 " \n\n■ Выдавать рекомендации приятным голосом. "
                 "\n\n■ Общаться как текстом, так и голосом – выбирай удобный формат. "
                 "\n\n■ Могу говорить прямо, без лишней нежности — если тебе важны только факты.   "
                 "\n\n📙 Я не только твой ментальный помощник, но и"
                 " полноценный ИИ — анализирую файлы и помогаю в любых задачах!")


start_referral_text = ("Помоги друзьям улучшить ментальное здоровье 🐿️\n\n"
                       "Просто поделись своим <b>уникальным промокодом</b>\n\n🥜 За одного приглашённого друга — 1 неделя"
                       " бесплатного использования.\n🥜 За 5 друзей — целый месяц в подарок.\n🥜 А если пригласишь"
                       " 10 друзей, получишь 3 месяца бесплатно.\n\n<b>А другу — неделя в подарок!</b> 🎁")

mechanic_checkup = ('Здесь ты можешь отслеживать своё состояние — <b>эмоциональное и продуктивное</b> — в динамике.\n\n📅Каждый'
                   ' день я буду присылать тебе сообщение в выбранное тобой время. В ответ ты просто выбираешь'
                    ' одно из пяти эмодзи, которое лучше всего отражает твой день.\n\n'
                    '📊В конце недели и месяца я пришлю тебе стильные и наглядные графики — по каждому дню, чтобы у'
                    ' тебя была возможность увидеть, как менялось твое самочувствие. А ещё — сравнение с предыдущей'
                    ' неделей, чтобы легче замечать прогресс или вовремя реагировать на изменения.  \n'
                    '\n🧡<b>Попробуем?</b> Тогда выбери, за каким состоянием будем следить на этой неделе')

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


checkup_emotions_photo = "AgACAgIAAxkBAAIDcWfloXCMz5MeVZh2JtOI8QGIrvUxAALm9jEb4OUwSzbwWz6yi_zvAQADAgADeQADNgQ"
checkup_productivity_photo = "AgACAgIAAxkBAAIDcmfloXlwnsex1ChuwyYTeIft4ipSAALn9jEb4OUwS8V9ktImoGm9AQADAgADeQADNgQ"

emoji_dict = {
    1: "😖",  # самый недовольный
    2: "😒",  # недовольный
    3: "😐",  # нейтральный
    4: "😌",  # спокойный
    5: "🤩"   # в восторге
}

speed_dict = {
    1: "🪵",  # полено — вообще не движется
    2: "🐌",  # улитка — очень медленно
    3: "🚲",  # велосипед — средне
    4: "🚗",  # машина — быстро
    5: "🚀"   # ракета — очень быстро
}


mechanic_dict = {
    "mental_helper": {
        "fast_help": '"Скорая помощь"\n\n'
                     'Здесь ты можешь быстро получить поддержку за счёт того, что я задаю только 6 наводящих'
                     ' вопрос и сразу выдаю рекомендации, которые рассчитаны на то,'
                     ' чтобы тебе “здесь и сейчас” стало легче”',
        "go_deeper": 'Здесь ты общаешься без ограничений.\n\n'
                     'Я тебе задаю достаточное количество наводящих вопросов, чтобы уйти в глубь. И даю развёрнутые'
                     ' рекомендации направленные на долгосрочный эффект.\n\n'
                     'А в платной версии ещё и используешь меня как универсального AI Ассистента”'
    },
    "exercises_by_problem": "Здесь ты получаешь <b>персональные упражнения</b> — под своё состояние\n\n"
                            "👀Я внимательно слежу за твоими ответами и подбираю то, что может реально помочь именно "
                            "тебе.\n\nКаждое упражнение — это короткая практика, которая помогает лучше понять себя,"
                            " снизить напряжение или стать продуктивнее — в зависимости от того,"
                            " что мы обсуждали с тобой до этого.\n\n"
                            "📙А на каждое упражнение я даю короткую обратную связь — и"
                            " всегда готова обсудить его с тобой после.\n\n🧡<b>Попробуем?</b>",

    "checkups": 'Здесь ты можешь отслеживать своё состояние — <b>эмоциональное и продуктивное</b> — в динамике.\n\n📅Каждый'
                ' день я буду присылать тебе сообщение в выбранное тобой время. В ответ ты просто выбираешь'
                ' одно из пяти эмодзи, которое лучше всего отражает твой день.\n\n'
                '📊В конце недели и месяца я пришлю тебе стильные и наглядные графики — по каждому дню, чтобы у'
                ' тебя была возможность увидеть, как менялось твое самочувствие. А ещё — сравнение с предыдущей'
                ' неделей, чтобы легче замечать прогресс или вовремя реагировать на изменения.\n\n'
                '🧡<b>Попробуем?</b> Тогда выбери, за каким состоянием будем следить на этой неделе',
    "referral_system": 'Помоги друзьям улучшить ментальное здоровье 🐿️\n\n'
                       'Просто поделись своим уникальным промокодом \n\n'
                       '• За каждого приглашённого друга — 1 неделя бесплатного использования.\n\n'
                       '• За 5 друзей — целый месяц в подарок.\n\n'
                       '• А если пригласишь 10 друзей, получишь 3 месяца бесплатно.\n\n'
                       '<b>А другу - неделя в подарок!</b> 🎁'
}

ai_temperature_text = ("Я также умею говорить прямо — без сюсюканья и лишней мягкости.\n🎯Если тебе комфортнее, когда"
                       " с тобой говорят по делу, чётко и без обёрток — просто включи прямолинейный режим.\n\nПример,"
                       " как я не буду:\n\n“Ты справляешься, даже если чувствуешь усталость."
                       " Всё ок, просто постарайся немного замедлиться.” 🐿️Пример, как я буду:\n\n"
                       "“Ты выгорел, потому что сам себя загнал. Отдохни уже, а не героически страдай.”\n\n🌰"
                       "доступно только в платной версии.")

def generate_random_dates() -> list[date]:
    """
    Генерирует список из 10 случайных дат типа `date`
    между 2023-01-01 и сегодняшним днём.
    """
    count = 7
    start_date = date(2023, 1, 1)
    end_date = date.today()
    delta_days = (end_date - start_date).days

    return [start_date + timedelta(days=random.randint(0, delta_days)) for _ in range(count)]


mental_problems_function = {
    "type": "function",
    "function": {
        "name": "extract_mental_problems",
        "description": "Вызывается абсолютно всегда. Получает данные о ментальных проблемах из текстового описания."
                       "Если проблемы в тексте нет, то у проблемы стоит значение False."
                       " Возвращает словарь, где ключи — названия проблем, а значения — булевы: True если проблема присутствует, иначе False.",
        "parameters": {
            "type": "object",
            "properties": {
                "self_esteem": {
                    "type": "boolean",
                    "description": "Проблема с самооценкой."
                },
                "emotions": {
                    "type": "boolean",
                    "description": "Проблема с эмоциями."
                },
                "relationships": {
                    "type": "boolean",
                    "description": "Проблема с отношениями (для Дани: с кем угодно, кроме романтических)."
                },
                "love": {
                    "type": "boolean",
                    "description": "Проблема с любовью."
                },
                "career": {
                    "type": "boolean",
                    "description": "Проблема с карьерой."
                },
                "finances": {
                    "type": "boolean",
                    "description": "Проблема с финансами."
                },
                "health": {
                    "type": "boolean",
                    "description": "Проблема со здоровьем."
                },
                "self_actualization": {
                    "type": "boolean",
                    "description": "Проблема с самореализацией."
                },
                "burnout": {
                    "type": "boolean",
                    "description": "Проблема с выгоранием."
                },
                "spirituality": {
                    "type": "boolean",
                    "description": "Проблема с духовностью (смысл жизни и т.д.)."
                }
            },
            "required": [
                "self_esteem", "emotions", "relationships", "love", "career",
                "finances", "health", "self_actualization", "burnout", "spirituality"
            ],
            "additionalProperties": False
        },
        "strict": True
    }
}

mental_helper_photo = "AgACAgIAAxkBAAIVLGf4PQZAaioiIcQJ-RVAIcbSb8gvAALH-TEbvALBS35A4o562evlAQADAgADeQADNgQ"

exercises_photo = "AgACAgIAAxkBAAIVMmf4PT32Mt65cQpfqQmvd59G1FMuAALI-TEbvALBS1idbaVxrVwnAQADAgADeQADNgQ"

checkups_graphic_photo = "AgACAgIAAxkBAAIVNGf4PW7m1Bn_TZCDMaI8OEYAASt_1AACyfkxG7wCwUtB83au90374gEAAwIAA3kAAzYE"

checkups_types_photo = "AgACAgIAAxkBAAIVNmf4PdRlSFhWzoU3tEfQzY1MHnSVAALK-TEbvALBS229tRkfCiwtAQADAgADeQADNgQ"

temperature_ai_photo = "AgACAgIAAxkBAAIVOGf4PgenKjMydR8FzECg1VkSJbOHAALL-TEbvALBSzuJZUsQVzucAQADAgADeQADNgQ"

universal_ai_photo = "AgACAgIAAxkBAAIVOmf4PlYCpejQ1wAB-pY4R7N0ls3gbAACzPkxG7wCwUuApyqgQK8ljQEAAwIAA3kAAzYE"

payment_photo = "AgACAgIAAxkBAAIVQGf4Prm4v66nJCvQ7AJ7TVYPmvZQAALO-TEbvALBS2yQ8L-raBlPAQADAgADeQADNgQ"

menu_photo = "AgACAgIAAxkBAAIVPGf4PouaoenmxBho_TkYYJBX-GWvAALN-TEbvALBSxgRvdgL8ya3AQADAgADeQADNgQ"

system_setting_photo = "AgACAgIAAxkBAAIVQmf4PuJtMiYyWiOVQ-NogrNpnLIFAALP-TEbvALBS2dQC3-UarUiAQADAgADeQADNgQ"

sub_description_photo = "AgACAgIAAxkBAAIT3Wf3AAGV2PfKyIjbAa62HbEXGMjqzAACrfMxG-e7uUuH4hxlRxr2ZQEAAwIAA3kAAzYE"

you_fooher_photo = "AgACAgIAAxkBAAIT4Gf3AUKY86PHRJAh9oN5ozOf2cGEAAKu8zEb57u5S0V5ESoJHFbnAQADAgADeQADNgQ"

sub_description_photo2 = "AgACAgIAAxkBAAIT42f3Aa-MWumK9XTGMn6llxiX56-aAAKv8zEb57u5Sw4LlVPxZp_KAQADAgADeQADNgQ"

how_are_you_photo = "AgACAgIAAxkBAAIVzGf44X3GtTQ1cBi14pMguh3ftiqQAALL7zEbvALJS02iZKnOMdsJAQADAgADeQADNgQ"

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



