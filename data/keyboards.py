from datetime import timedelta, datetime

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.repository import checkup_repository, days_checkups_repository, subscriptions_repository
from settings import emoji_dict, speed_dict, table_names
from utils.checkups_ended import sent_today

admin_kb = [
        [KeyboardButton(text='Статистика')],
        [KeyboardButton(text='Выгрузка таблиц')],
        [KeyboardButton(text="Сделать рассылку")],
        [KeyboardButton(text="Добавить / удалить админа")],
        [KeyboardButton(text="Сгенерировать промокод")]
    ]
admin_keyboard = ReplyKeyboardMarkup(keyboard=admin_kb, resize_keyboard=True)

menu_button = InlineKeyboardButton(text="В меню", callback_data="start_menu")

edit_delete_notification_keyboard = InlineKeyboardBuilder()
edit_delete_notification_keyboard.row(InlineKeyboardButton(text="Изменить время отчета",
                                                           callback_data="edit_notification"))
edit_delete_notification_keyboard.row(InlineKeyboardButton(text="Отключить авто-отчет",
                                                           callback_data="delete_notification"))
edit_delete_notification_keyboard.row(InlineKeyboardButton(text="Отмена", callback_data="cancel"))


edit_activate_notification_keyboard = InlineKeyboardBuilder()
edit_activate_notification_keyboard.row(InlineKeyboardButton(text="Включить автоматическую отправку отчета",
                                                           callback_data="activate_notification"))
edit_activate_notification_keyboard.row(InlineKeyboardButton(text="В меню", callback_data="start_menu"))

referral_keyboard = InlineKeyboardBuilder()
referral_keyboard.row(InlineKeyboardButton(text="Выпустить промокод", callback_data="create_promo_code"))
referral_keyboard.row(InlineKeyboardButton(text="Ввести промокод", callback_data="enter_promo_code"))
referral_keyboard.row(menu_button)


price_keyboard = InlineKeyboardBuilder()
price_keyboard.row(InlineKeyboardButton(text="299р/Неделя", callback_data="week"))
price_keyboard.row(InlineKeyboardButton(text="799р/Месяц", callback_data="month"))
price_keyboard.row(InlineKeyboardButton(text="1990р/3 месяца", callback_data="three_month"))

menu_keyboard = InlineKeyboardBuilder()
menu_keyboard.row(menu_button)


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

back_to_bots_keyboard = InlineKeyboardBuilder()
back_to_bots_keyboard.row(InlineKeyboardButton(text="Назад к выбору ботов", callback_data="back_to_bots"))

choice_gender_keyboard = InlineKeyboardBuilder()
choice_gender_keyboard.row(InlineKeyboardButton(text="В женском роде♀️", callback_data="gender|female"))
choice_gender_keyboard.row(InlineKeyboardButton(text="В мужском роде♂️", callback_data="gender|male"))
choice_gender_keyboard.row(InlineKeyboardButton(text="Пропустить", callback_data="gender|No"))


exercises_keyboard = InlineKeyboardBuilder()
exercises_keyboard.row(InlineKeyboardButton(text="Упражнения", callback_data="exercises_by_problem"))
exercises_keyboard.row(menu_button)


async def main_keyboard(user_id: int) -> InlineKeyboardBuilder:
    keyboard = InlineKeyboardBuilder()
    user_checkups = await checkup_repository.get_active_checkups_by_user_id(user_id=user_id)
    finish_checkup_day = True
    for checkup in user_checkups:
        active_day = await days_checkups_repository.get_active_day_checkup_by_checkup_id(checkup_id=checkup.id)
        if active_day is not None or (datetime.now().time() < checkup.time_checkup
                                      and not await sent_today(checkup.id)):
            finish_checkup_day = False
            break
    if finish_checkup_day is False:
        keyboard.row(InlineKeyboardButton(text="Пройти трекинг", callback_data="go_checkup"))
    # keyboard.row(InlineKeyboardButton(text="⭐Режимы общения", callback_data="mental_helper"))
    keyboard.row(InlineKeyboardButton(text="📝Упражнения", callback_data="exercises_by_problem"))
    keyboard.add(InlineKeyboardButton(text="🗓️Трекинг состояния", callback_data="checkups"))
    keyboard.row(InlineKeyboardButton(text="📜Механика сервиса", callback_data="all_mechanics"))
    keyboard.add(InlineKeyboardButton(text="⚙️Настройки", callback_data="system_settings"))
    keyboard.row(InlineKeyboardButton(text="🎁 Реферальная система", callback_data="referral_system"))
    user_sub = await subscriptions_repository.get_active_subscription_by_user_id(user_id=user_id)
    if user_sub is None:
        sub_button_text = "💸 Купить подписку"
    else:
        end_date = user_sub.creation_date + timedelta(days=user_sub.time_limit_subscription)
        sub_button_text = (f"Моя подписка (до"
                f" {end_date.strftime('%d.%m.%y, %H:%M')} +GMT3)")
    keyboard.row(InlineKeyboardButton(text=sub_button_text, callback_data="sub_management"))
    return keyboard


fast_help_keyboard = InlineKeyboardBuilder()
fast_help_keyboard.row(InlineKeyboardButton(text="Скорая помощь", callback_data="fast_help_only"))
fast_help_keyboard.row(menu_button)

go_deeper_keyboard = InlineKeyboardBuilder()
go_deeper_keyboard.row(InlineKeyboardButton(text="Уйти вглубь", callback_data="go_deeper"))
go_deeper_keyboard.row(menu_button)

mental_helper_keyboard = InlineKeyboardBuilder()
mental_helper_keyboard.row(InlineKeyboardButton(text="Скорая помощь", callback_data="fast_help"))
mental_helper_keyboard.row(InlineKeyboardButton(text="Уйти вглубь", callback_data="go_deeper"))
mental_helper_keyboard.row(menu_button)


def generate_sub_keyboard(mode_type: str | None = None):
    subscriptions_keyboard = InlineKeyboardBuilder()
    subscriptions_keyboard.row(InlineKeyboardButton(text="390р/неделя", callback_data=f"choice_sub|7|390.00|{mode_type}"))
    subscriptions_keyboard.row(InlineKeyboardButton(text="790р/месяц", callback_data=f"choice_sub|30|790.00|{mode_type}"))
    subscriptions_keyboard.row(InlineKeyboardButton(text="1990р/3 месяца", callback_data=f"choice_sub|90|1990.00|{mode_type}"))
    subscriptions_keyboard.row(menu_button)
    return subscriptions_keyboard

def get_rec_keyboard(mode_type: str):
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text="Подписка", callback_data=f"subscribe|{mode_type}"))
    keyboard.row(menu_button)
    return keyboard

buy_sub_keyboard = InlineKeyboardBuilder()
buy_sub_keyboard.row(InlineKeyboardButton(text="Подписка", callback_data=f"subscribe"))
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

end_fast_help_keyboard = InlineKeyboardBuilder()
end_fast_help_keyboard.row(InlineKeyboardButton(text="Уйти в глубь", callback_data="go_deeper"))
end_fast_help_keyboard.row(menu_button)


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

ai_temperature_keyboard = InlineKeyboardBuilder()
ai_temperature_keyboard.row(InlineKeyboardButton(text="Мягкая версия", callback_data="ai_temperature|1.3"))
ai_temperature_keyboard.row(InlineKeyboardButton(text="Прямолинейная версия", callback_data="ai_temperature|0.6"))
ai_temperature_keyboard.row(InlineKeyboardButton(text="Нейтральная версия (по умолчанию)", callback_data="ai_temperature|1"))
ai_temperature_keyboard.row(menu_button)


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


statistics_keyboard = InlineKeyboardBuilder()
statistics_keyboard.row(InlineKeyboardButton(text="Количество новых пользователей", callback_data="statistics|users"))
statistics_keyboard.row(InlineKeyboardButton(text="Количество пользователей с активной подпиской", callback_data="statistics|active_subs"))
statistics_keyboard.row(InlineKeyboardButton(text="Количество запросов в GPT", callback_data="statistics|gpt"))


notification_keyboard = InlineKeyboardBuilder()
notification_keyboard.row(
    InlineKeyboardButton(text="Обсудить проблему", callback_data="start_problem_conversation")
)
notification_keyboard.row(
    InlineKeyboardButton(text="Упражнение", callback_data="exercises_by_problem"),
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
                                                                       callback_data=f"recommendation_exercise|{problem_id}"))
    return practice_exercise_recommendation_keyboard.as_markup()