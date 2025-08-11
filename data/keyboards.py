from datetime import timedelta, datetime, timezone

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.repository import checkup_repository, days_checkups_repository, subscriptions_repository, users_repository, \
    user_timezone_repository, user_counters_repository
from settings import emoji_dict, speed_dict, table_names
from utils.checkups_sent import sent_today

admin_kb = [
        [KeyboardButton(text='Статистика')],
        [KeyboardButton(text='Выгрузка таблиц')],
        [KeyboardButton(text="Сделать рассылку")],
        [KeyboardButton(text="Добавить / удалить админа")],
        [KeyboardButton(text="Управление подписками")],
        [KeyboardButton(text="Сгенерировать промокод")]
    ]
admin_keyboard = ReplyKeyboardMarkup(keyboard=admin_kb, resize_keyboard=True)

menu_button = InlineKeyboardButton(text="в Меню", callback_data="start_menu")

edit_delete_notification_keyboard = InlineKeyboardBuilder()
edit_delete_notification_keyboard.row(InlineKeyboardButton(text="Изменить время отчета",
                                                           callback_data="edit_notification"))
edit_delete_notification_keyboard.row(InlineKeyboardButton(text="Отключить авто-отчет",
                                                           callback_data="delete_notification"))
edit_delete_notification_keyboard.row(InlineKeyboardButton(text="Отмена", callback_data="cancel"))


edit_activate_notification_keyboard = InlineKeyboardBuilder()
edit_activate_notification_keyboard.row(InlineKeyboardButton(text="Включить автоматическую отправку отчета",
                                                           callback_data="activate_notification"))
edit_activate_notification_keyboard.row(InlineKeyboardButton(text="в Меню", callback_data="start_menu"))

referral_keyboard = InlineKeyboardBuilder()
referral_keyboard.row(InlineKeyboardButton(text="Выпустить промокод", callback_data="create_promo_code"))
referral_keyboard.row(InlineKeyboardButton(text="Ввести промокод", callback_data="enter_promo_code"))
referral_keyboard.row(InlineKeyboardButton(text="Подарить подписку", callback_data="buy_gift"))
referral_keyboard.row(menu_button)


price_keyboard = InlineKeyboardBuilder()
price_keyboard.row(InlineKeyboardButton(text="249р/Неделя", callback_data="week"))
price_keyboard.row(InlineKeyboardButton(text="490р/Месяц", callback_data="month"))
price_keyboard.row(InlineKeyboardButton(text="990р/3 месяца", callback_data="three_month"))

menu_keyboard = InlineKeyboardBuilder()
menu_keyboard.row(menu_button)

discuss_problem_keyboard = InlineKeyboardBuilder()
discuss_problem_keyboard.row(InlineKeyboardButton(text="Разобрать", callback_data="start_problem_conversation"))
discuss_problem_keyboard.row(menu_button)

next_politic_keyboard = InlineKeyboardBuilder()
next_politic_keyboard.row(InlineKeyboardButton(text="Далее", callback_data="confirm_politic"))

have_promo_keyboard = InlineKeyboardBuilder()
have_promo_keyboard.row(InlineKeyboardButton(text="Да", callback_data="have_promo|yes"))
have_promo_keyboard.row(InlineKeyboardButton(text="Нет", callback_data="have_promo|no"))


add_delete_admin = InlineKeyboardBuilder()
add_delete_admin.row(InlineKeyboardButton(text="Добавить админа", callback_data="add_admin"))
add_delete_admin.row(InlineKeyboardButton(text="Удалить админа", callback_data="delete_admin"))

age_keyboard = InlineKeyboardBuilder()
age_keyboard.row(InlineKeyboardButton(text="18-24", callback_data="age|18-24"))
age_keyboard.row(InlineKeyboardButton(text="25-34", callback_data="age|25-34"))
age_keyboard.row(InlineKeyboardButton(text="35-44", callback_data="age|35-44"))
age_keyboard.row(InlineKeyboardButton(text="45+", callback_data="age|45+"))
age_keyboard.row(InlineKeyboardButton(text="Пропустить", callback_data="age|No"))

menu_age_keyboard = InlineKeyboardBuilder()
menu_age_keyboard.row(InlineKeyboardButton(text="18-24", callback_data="age|18-24"))
menu_age_keyboard.row(InlineKeyboardButton(text="25-34", callback_data="age|25-34"))
menu_age_keyboard.row(InlineKeyboardButton(text="35-44", callback_data="age|35-44"))
menu_age_keyboard.row(InlineKeyboardButton(text="45+", callback_data="age|45+"))
menu_age_keyboard.row(InlineKeyboardButton(text="Отмена", callback_data="system_settings"))

settings_cancel_keyboard = InlineKeyboardBuilder()
settings_cancel_keyboard.row(InlineKeyboardButton(text="Отмена", callback_data="system_settings"))

choice_bot_stat = InlineKeyboardBuilder()
choice_bot_stat.row(InlineKeyboardButton(text="Количество новых пользователей", callback_data="statistic|new_users"))
choice_bot_stat.row(InlineKeyboardButton(text="Количество всех запросов в GPT", callback_data="statistic|ai_requests"))
choice_bot_stat.row(InlineKeyboardButton(text="Количество запросов с фото в GPT", callback_data="statistic|photo_ai_requests"))
choice_bot_stat.row(InlineKeyboardButton(text="Количество операций по оплате", callback_data="statistic|operations"))
choice_bot_stat.row(InlineKeyboardButton(text="Отмена", callback_data="cancel"))

choice_bot_send = InlineKeyboardBuilder()
choice_bot_send.row(InlineKeyboardButton(text="Рассылка в боте", callback_data="mailing|all_bots"))
choice_bot_send.row(InlineKeyboardButton(text="Отмена", callback_data="cancel"))

cancel_keyboard = InlineKeyboardBuilder()
cancel_keyboard.row(InlineKeyboardButton(text="Отмена", callback_data="cancel"))

miss_keyboard = InlineKeyboardBuilder()
miss_keyboard.row(InlineKeyboardButton(text="Пропустить", callback_data="cancel"))

choice_gender_keyboard = InlineKeyboardBuilder()
choice_gender_keyboard.row(InlineKeyboardButton(text="В женском роде♀️", callback_data="gender|female"))
choice_gender_keyboard.row(InlineKeyboardButton(text="В мужском роде♂️", callback_data="gender|male"))
choice_gender_keyboard.row(InlineKeyboardButton(text="Пропустить", callback_data="gender|No"))

choice_gender_settings_keyboard = InlineKeyboardBuilder()
choice_gender_settings_keyboard.row(InlineKeyboardButton(text="В женском роде♀️", callback_data="gender|female"))
choice_gender_settings_keyboard.row(InlineKeyboardButton(text="В мужском роде♂️", callback_data="gender|male"))
choice_gender_settings_keyboard.row(InlineKeyboardButton(text="Отменить", callback_data="system_settings"))


exercises_keyboard = InlineKeyboardBuilder()
exercises_keyboard.row(InlineKeyboardButton(text="Упражнения", callback_data="choose_exercise_problem"))
exercises_keyboard.row(menu_button)


async def main_keyboard(user_id: int) -> InlineKeyboardBuilder:
    keyboard = InlineKeyboardBuilder()
    user_checkups = await checkup_repository.get_active_checkups_by_user_id(user_id=user_id)
    user_counters = await user_counters_repository.get_user_counters(user_id)
    user_timezone_delta = await user_timezone_repository.get_user_timezone_delta(user_id)
    today_tracking = False
    missed_tracking = False
    for checkup in user_checkups:
        active_days = await days_checkups_repository.get_active_day_checkups_by_checkup_id(checkup_id=checkup.id)
        for active_day in active_days:
            if active_day.creation_date.date() == datetime.now(timezone(user_timezone_delta)).date():
                if not await sent_today(checkup.id):
                    today_tracking = True
            elif datetime.now(timezone(user_timezone_delta)).date() - active_day.creation_date.date() < timedelta(days=4):
                missed_tracking = True

        if datetime.now(timezone.utc).time() < checkup.time_checkup and not await sent_today(checkup.id):
            today_tracking = True

    if today_tracking:
        keyboard.row(InlineKeyboardButton(text="Трекинги за СЕГОДНЯ", callback_data="go_checkup"))
    if missed_tracking:
        keyboard.row(InlineKeyboardButton(text="⚠️ПРОПУЩЕННЫЕ трекинги", callback_data="missed_tracking"))

    keyboard.row(InlineKeyboardButton(text="📝Упражнения", callback_data="choose_exercise_problem"))
    keyboard.add(InlineKeyboardButton(text="📉️Трекинги", callback_data="checkups"))
    keyboard.row(InlineKeyboardButton(text="📜О сервисе", callback_data="all_mechanics"))
    keyboard.add(InlineKeyboardButton(text="⚙️Настройки", callback_data="system_settings"))
    keyboard.row(InlineKeyboardButton(text="🎁Промокоды", callback_data="referral_system"))
    user_sub = await subscriptions_repository.get_active_subscription_by_user_id(user_id=user_id)
    if user_sub is None:
        sub_button_text = "🐿 КУПИТЬ ПОДПИСКУ"
    else:
        end_date = user_sub.creation_date + timedelta(days=user_sub.time_limit_subscription)
        sub_button_text = (f"🐿 МОЯ ПОДПИСКА (до"
                f" {end_date.strftime('%d.%m.%y')})")
    keyboard.row(InlineKeyboardButton(text=sub_button_text, callback_data="sub_management"))
    if user_counters.messages_count == 0:
        keyboard.row(InlineKeyboardButton(text="👉НАЧАТЬ ОБЩЕНИЕ", callback_data="start_problem_conversation"))
    return keyboard


def generate_sub_keyboard(mode_type: str | None = None):
    subscriptions_keyboard = InlineKeyboardBuilder()
    subscriptions_keyboard.row(InlineKeyboardButton(text="249р/неделя", callback_data=f"choice_sub|7|249.00|{mode_type}"))
    subscriptions_keyboard.row(InlineKeyboardButton(text="490р/месяц", callback_data=f"choice_sub|30|490.00|{mode_type}"))
    subscriptions_keyboard.row(InlineKeyboardButton(text="990р/3 месяца", callback_data=f"choice_sub|90|990.00|{mode_type}"))
    subscriptions_keyboard.row(menu_button)
    return subscriptions_keyboard

def generate_sub_management_keyboard(mode_type: str | None = None):
    subscriptions_keyboard = InlineKeyboardBuilder()
    subscriptions_keyboard.row(
        InlineKeyboardButton(text="Отменить подписку", callback_data=f"cancel_sub"))
    subscriptions_keyboard.row(menu_button)
    return subscriptions_keyboard

def get_rec_keyboard(mode_type: str):
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text="🐿 ПОДПИСКА", callback_data=f"subscribe|{mode_type}"))
    keyboard.row(menu_button)
    return keyboard

buy_sub_keyboard = InlineKeyboardBuilder()
buy_sub_keyboard.row(InlineKeyboardButton(text="<b>🐿 ПОДПИСКА</b>", callback_data=f"subscribe"))
buy_sub_keyboard.row(menu_button)


async def keyboard_for_pay(operation_id: str, url: str, time_limit: int, mode_type: str | None = None):
    pay_ai_keyboard = InlineKeyboardBuilder()
    pay_ai_keyboard.row(InlineKeyboardButton(text="Оплатить", web_app=WebAppInfo(url=url)))
    pay_ai_keyboard.row(InlineKeyboardButton(text="Оплата произведена",
                                             callback_data=f"is_paid|{operation_id}|{time_limit}|{mode_type}"))
    return pay_ai_keyboard


def get_go_deeper_rec_keyboard(go_deeper_id: int):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="Получить рекомендации", callback_data=f"get_go_deeper_rec|{go_deeper_id}"))
    return keyboard


checkup_type_keyboard = InlineKeyboardBuilder()
checkup_type_keyboard.row(InlineKeyboardButton(text="🤩Трекинг эмоций", callback_data="checkups|emotions"))
checkup_type_keyboard.row(InlineKeyboardButton(text="🚀Трекинг продуктивности", callback_data="checkups|productivity"))
checkup_type_keyboard.row(menu_button)

def emotions_keyboard(check_data: str):
    keyboard = InlineKeyboardBuilder()
    for emoji in emoji_dict.keys():
        keyboard.add(InlineKeyboardButton(text=emoji_dict.get(emoji), callback_data=f"enter_emoji|{emoji}|{check_data}"))
    keyboard.row(menu_button)
    return keyboard

def productivity_keyboard(check_data: str):
    keyboard = InlineKeyboardBuilder()
    for emoji in speed_dict.keys():
        keyboard.add(InlineKeyboardButton(text=speed_dict.get(emoji), callback_data=f"enter_emoji|{emoji}|{check_data}"))
    keyboard.row(menu_button)
    return keyboard

def get_ai_temperature_keyboard(user_ai_temperature: int):
    ai_temperature_keyboard = InlineKeyboardBuilder()
    ai_temperature_keyboard.row(InlineKeyboardButton(text=f"Прямолинейная версия{' ✅' if user_ai_temperature == 0.6 else ''}", callback_data="ai_temperature|0.6"))
    ai_temperature_keyboard.row(InlineKeyboardButton(text=f"Нейтральная версия{' ✅' if user_ai_temperature != 0.6 else ''}", callback_data="ai_temperature|1"))
    ai_temperature_keyboard.row(menu_button)
    return ai_temperature_keyboard


db_tables_keyboard = InlineKeyboardBuilder()
row_to_kb = 1
for table_name in table_names:
    if row_to_kb == 1:
        db_tables_keyboard.row(InlineKeyboardButton(text=table_name, callback_data=f"db_tables|{table_name}"))
        row_to_kb = 2
    else:
        db_tables_keyboard.add(InlineKeyboardButton(text=table_name, callback_data=f"db_tables|{table_name}"))
        row_to_kb = 1
db_tables_keyboard.row(InlineKeyboardButton(text="Отмена", callback_data="cancel"))


type_users_mailing_keyboard = InlineKeyboardBuilder()
type_users_mailing_keyboard.row(InlineKeyboardButton(text='Всем пользователям', callback_data="type_users_mailing|all"))
type_users_mailing_keyboard.row(InlineKeyboardButton(text='С подпиской', callback_data="type_users_mailing|sub"))
type_users_mailing_keyboard.row(InlineKeyboardButton(text='Без подписки', callback_data="type_users_mailing|not_sub"))
type_users_mailing_keyboard.row(InlineKeyboardButton(text="Отмена", callback_data="cancel"))


account_keyboard = InlineKeyboardBuilder()
account_keyboard.row(InlineKeyboardButton(text="Настройки", callback_data="system_settings"))
account_keyboard.row(InlineKeyboardButton(text="в Меню", callback_data="start_menu"))

statistics_keyboard = InlineKeyboardBuilder()
statistics_keyboard.row(InlineKeyboardButton(text="Количество новых пользователей", callback_data="statistics|users"))
statistics_keyboard.row(InlineKeyboardButton(text="Количество пользователей с активной подпиской", callback_data="statistics|active_subs"))
statistics_keyboard.row(InlineKeyboardButton(text="Количество запросов в GPT", callback_data="statistics|gpt"))


notification_keyboard = InlineKeyboardBuilder()
notification_keyboard.row(
    InlineKeyboardButton(text="Обсудить проблему", callback_data="start_problem_conversation")
)
notification_keyboard.row(
    InlineKeyboardButton(text="Упражнение", callback_data="choose_exercise_problem"),
    InlineKeyboardButton(text="Трекинг", callback_data="settings|checkups")
)


def delete_checkups_keyboard(type_checkup: str, checkup_id: int):
    keyboard = InlineKeyboardBuilder()
    if type_checkup == "emotions":
        keyboard.row(InlineKeyboardButton(text="❌Приостановить трекинг", callback_data=f"delete_checkups|emotions|{checkup_id}"))
        keyboard.row(InlineKeyboardButton(text="🚀Трекинг продуктивности", callback_data="checkups|productivity"))
    else:
        keyboard.row(InlineKeyboardButton(text="❌Приостановить трекинг", callback_data=f"delete_checkups|productivity|{checkup_id}"))
        keyboard.row(InlineKeyboardButton(text="🤩Трекинг эмоций", callback_data="checkups|emotions"))
    keyboard.row(menu_button)
    return keyboard


def create_practice_exercise_recommendation_keyboard(problem_id: int):
    practice_exercise_recommendation_keyboard = InlineKeyboardBuilder()
    practice_exercise_recommendation_keyboard.row(InlineKeyboardButton(text="📝Получить упражнение",
                                                                       callback_data=f"exercise_by_problem_id|{problem_id}"))
    return practice_exercise_recommendation_keyboard.as_markup()