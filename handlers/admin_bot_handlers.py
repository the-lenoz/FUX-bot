from datetime import timedelta

from aiogram import Router, types, Bot, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state
from aiogram.types import InlineKeyboardButton, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bots import main_bot
from data.keyboards import admin_keyboard, add_delete_admin, cancel_keyboard, db_tables_keyboard, \
    type_users_mailing_keyboard, statistics_keyboard
from db.repository import admin_repository, users_repository, subscriptions_repository, \
    referral_system_repository, events_repository
from utils.generate_promo import generate_single_promo_code
from utils.get_table_db_to_excel import export_table_to_memory
from utils.is_main_admin import is_main_admin
from utils.list_admins_keyboard import AdminsKeyboard
from utils.paginator import create_paginated_keyboard
from utils.promocode import user_entered_promo_code
from utils.state_models import InputMessage, AdminBotStates

admin_router = Router()


@admin_router.callback_query(F.data=="cancel", any_state)
@is_main_admin
async def admin_cancel(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    await state.clear()
    await call.message.answer(text="Вы находитесь на стартовой панели, выберите свои дальнейшие действия", reply_markup=admin_keyboard)
    await call.message.delete()


@admin_router.callback_query(F.data.startswith("db_tables|"), any_state)
@is_main_admin
async def choice_table_db(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    table_name = call.data.split("|")[1]
    await state.clear()
    db_table = export_table_to_memory(table_name=table_name)
    if db_table == "Error":
        await call.message.answer("Произошла какая-то ошибка при выгрузке данной таблицы, попробуйте еще раз")
        return
    await call.message.answer_document(document=BufferedInputFile(file=db_table,
                                                               filename=f"{table_name}.xlsx"))


@admin_router.message(F.text=="/start", any_state)
@is_main_admin
async def admin_start(message: types.Message, state: FSMContext, bot: Bot):
    await state.clear()
    await message.delete()
    await message.answer(text="Это Админ бот. С помощью него вы можете получать статистику,"
                              " а также делать дополнительные рассылки по пользователям🤖", reply_markup=admin_keyboard)


@admin_router.message(F.text=="Сделать рассылку")
@is_main_admin
async def new_mailing(message: types.Message, state: FSMContext, bot: Bot):
    await state.clear()
    await message.answer("Выбери тип пользователей, по которым хочешь сделать рассылку",
                         reply_markup=type_users_mailing_keyboard.as_markup())


@admin_router.message(F.text=="Статистика")
@is_main_admin
async def get_statistics(message: types.Message, state: FSMContext, bot: Bot):
    await state.clear()
    await message.answer("Выбери раздел, статистику которого ты хочешь посмотреть",
                         reply_markup=statistics_keyboard.as_markup())


@admin_router.message(F.text=="Управление подписками")
@is_main_admin
async def manage_subscriptions(message: types.Message, state: FSMContext, bot: Bot):
    await state.clear()
    users = await users_repository.select_all_users()
    subscriptions = await subscriptions_repository.select_all_subscriptions()
    active_subscriber_ids = {subscription.user_id for subscription in subscriptions if subscription.active}
    items = {}

    for user in users:
        items[f"@{user.username if user.username else '--БЕЗ НИКНЕЙМА--'} "
              + ('💰' if user.user_id in active_subscriber_ids else '')] = user.user_id

    keyboard = create_paginated_keyboard(items, "manage_user_subscription|{}",
                                         "manage_subscription_paging|{}",
                                         cancel_callback_data="cancel")

    await message.answer(text="Выбери пользователя, чью подписку хочешь изменить (💰 == УЖЕ подписан)",
                                 reply_markup=keyboard)


@admin_router.callback_query(F.data.startswith("manage_subscription_paging|"))
@is_main_admin
async def manage_subscription_paging(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    page = int(call.data.split("|")[1])
    await state.clear()
    users = await users_repository.select_all_users()
    subscriptions = await subscriptions_repository.select_all_subscriptions()
    active_subscriber_ids = {subscription.user_id for subscription in subscriptions if subscription.active}
    items = {}

    for user in users:
        items[f"@{user.username if user.username else '--БЕЗ НИКНЕЙМА--'} "
              + ('💰' if user.user_id in active_subscriber_ids else '')] = user.user_id

    keyboard = create_paginated_keyboard(items, "manage_user_subscription|{}",
                                         "manage_subscription_paging|{}",
                                         cancel_callback_data="cancel",
                                         page=page)

    await call.message.edit_reply_markup(reply_markup=keyboard)
    await call.answer()


@admin_router.callback_query(F.data.startswith("manage_user_subscription|"))
@is_main_admin
async def manage_user_subscription(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    await state.clear()
    user_id = int(call.data.split("|")[1])
    subscription = await subscriptions_repository.get_active_subscription_by_user_id(user_id)
    user = await users_repository.get_user_by_user_id(user_id)
    keyboard_builder = InlineKeyboardBuilder()
    text = f"@{user.username if user.username else '--БЕЗ НИКНЕЙМА--'} "
    if subscription:
        end_date = subscription.creation_date + timedelta(days=subscription.time_limit_subscription)
        text += f"- подписка активна до {end_date.strftime('%d.%m.%y')}"
        keyboard_builder.row(InlineKeyboardButton(text="Лишить подписки",
                                                  callback_data=f"delete_subscriber|{user_id}"))
    else:
        text += "- не подписан"

    keyboard_builder.row(InlineKeyboardButton(text="Активировать промокод",
                                              callback_data=f"grant_promocode_to_user|{user_id}"))
    keyboard_builder.row(InlineKeyboardButton(text="Отмена", callback_data="manage_subscription_paging|0"))

    await call.message.answer(
        text,
        reply_markup=keyboard_builder.as_markup()
    )

    await call.message.delete()


@admin_router.callback_query(F.data.startswith("delete_subscriber|"))
@is_main_admin
async def delete_subscriber(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    subscriber_id = int(call.data.split("|")[1])
    subscription = await subscriptions_repository.get_active_subscription_by_user_id(subscriber_id)
    await subscriptions_repository.deactivate_subscription(subscription.id)
    await call.message.answer(text="Пользователь лишён подписки."
                                 f" выберите свои дальнейшие действия!", reply_markup=admin_keyboard)
    await call.message.delete()

@admin_router.callback_query(F.data.startswith("grant_promocode_to_user|"))
@is_main_admin
async def grant_promocode_to_user(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    user_id = int(call.data.split("|")[1])
    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.row(InlineKeyboardButton(text="Отмена", callback_data=f"manage_user_subscription|{user_id}"))

    await call.message.answer(
        "Введи промокод, который ты хочешь активировать для пользователя",
        reply_markup=keyboard_builder.as_markup()
    )
    await state.set_state(AdminBotStates.enter_promocode)
    await state.update_data(active_user_id=user_id)
    await call.message.delete()


@admin_router.message(F.text, AdminBotStates.enter_promocode)
@is_main_admin
async def user_enter_promo_code(message: types.Message, state: FSMContext, bot: Bot):
    promo_code = message.text
    user_id = await state.get_value("active_user_id")
    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.row(InlineKeyboardButton(text="Назад", callback_data="manage_subscription_paging|0"))
    await state.clear()

    if await user_entered_promo_code(user_id, promo_code):
        await message.answer("Промокод был активирован для пользователя!", reply_markup=keyboard_builder.as_markup())
    else:
        await message.answer("Промокод не был активирован для пользователя, попробуй другой", reply_markup=keyboard_builder.as_markup())



@admin_router.message(Command("unsubscribe"))
@is_main_admin
async def delete_subscriber_command(message: types.Message, state: FSMContext, bot: Bot):
    try:
        subscriber_id = int(message.text.split()[-1])
    except ValueError:
        await message.answer("Использование: /unsubscribe <user_id>")
        return
    subscription = await subscriptions_repository.get_active_subscription_by_user_id(subscriber_id)
    if subscription:
        await subscriptions_repository.deactivate_subscription(subscription.id)
        await message.answer(text="Пользователь лишён подписки."
                                       f" выберите свои дальнейшие действия!", reply_markup=admin_keyboard)
    else:
        await message.answer(
            f"Пользователь с id {subscriber_id} не найден среди подписчиков."
        )


@admin_router.callback_query(F.data.startswith("statistics"), any_state)
@is_main_admin
async def enter_type_users_for_mailing(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    type_statistics = call.data.split("|")[1]
    await state.clear()
    if type_statistics == "users":
        user_stat = await users_repository.get_user_creation_statistics()
        text_message = (f"Количество новых пользователей:\n\n"
                        f"Статистика за день: <b>{user_stat.get('day')}</b>\n"
                        f"Статистика за неделю: <b>{user_stat.get('week')}</b>\n"
                        f"Статистика за месяц: <b>{user_stat.get('month')}</b>\n"
                        f"Статистика за квартал: <b>{user_stat.get('quarter')}</b>\n"
                        f"Статистика за все время <b>{user_stat.get('all_time')}</b>")
    elif type_statistics == "paid_users":
        subscriptions = await subscriptions_repository.select_all_active_subscriptions()
        count = 0
        for subscription in subscriptions:
            if subscription.recurrent:
                count += 1
        text_message = f"Количество пользователей, которые платят за подписку: <b>{count}</b>"
    else:
        subscriptions = await subscriptions_repository.get_active_subscriptions_count()
        text_message = f"Количество пользователей, у которых на данный подписка: <b>{subscriptions}</b>"
    await call.message.answer(text=text_message, parse_mode="HTML")
    await call.message.delete()



@admin_router.callback_query(F.data.startswith("type_users_mailing"), any_state)
@is_main_admin
async def enter_type_users_for_mailing(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    await state.clear()
    type_users = call.data.split("|")[1]
    if type_users == "all":
        await call.message.answer(text="Напиши сообщение, которое ВСЕМ разошлётся пользователям",
                                  reply_markup=cancel_keyboard.as_markup())
    elif type_users == "sub":
        await call.message.answer(text="Напиши сообщение, которое  разошлётся пользователям С ПОДПИСКОЙ",
                                  reply_markup=cancel_keyboard.as_markup())
    elif type_users == "not_sub":
        await call.message.answer(text="Напиши сообщение, которое разошлётся пользователям БЕЗ ПОДПИСКИ",
                                  reply_markup=cancel_keyboard.as_markup())
    elif type_users == "passive":
        await call.message.answer(text="Напиши сообщение, которое разошлётся ПАССИВНЫМ пользователям",
                                  reply_markup=cancel_keyboard.as_markup())
    await state.set_state(InputMessage.enter_message_mailing)
    await state.update_data(message_id=call.message.message_id, type_users=type_users)



@admin_router.message(F.text=="Выгрузка таблиц")
@is_main_admin
async def get_db_tables(message: types.Message, state: FSMContext, bot: Bot):
    await state.clear()
    message = await message.answer(text="Выбери таблицу, данные которой ты хочешь выгрузить",
                                   reply_markup=db_tables_keyboard.as_markup())


@admin_router.message(F.text, InputMessage.enter_message_mailing)
@is_main_admin
async def enter_message_mailing(message: types.Message, state: FSMContext, bot: Bot):
    state_data = await state.get_data()
    type_users = state_data.get("type_users")
    message_id = state_data.get("message_id")
    users = await users_repository.select_all_users()
    if type_users == "all":
        for user in users:
            try:
                await main_bot.send_message(chat_id=user.user_id, text=message.text)
            except:
                continue
    elif type_users == "sub":
        for user in users:
            user_sub = await subscriptions_repository.get_active_subscription_by_user_id(user_id=user.user_id)
            if user_sub:
                try:
                    await main_bot.send_message(chat_id=user.user_id, text=message.text)
                except:
                    continue
    elif type_users == "not_sub":
        for user in users:
            user_sub = await subscriptions_repository.get_active_subscription_by_user_id(user_id=user.user_id)
            if user_sub is None:
                try:
                    await main_bot.send_message(chat_id=user.user_id, text=message.text)
                except:
                    continue
    elif type_users == "passive":
        for user in users:
            last_user_event = await events_repository.get_last_event_by_user_id(user.user_id)
            if last_user_event.creation_date - user.creation_date < timedelta(hours=24):
                try:
                    await main_bot.send_message(chat_id=user.user_id, text=message.text)
                except:
                    continue
    await message.answer(text="Ваша рассылка отправлена всем выбранным пользователям бота", reply_markup=admin_keyboard)
    await bot.delete_message(message_id=message_id, chat_id=message.from_user.id)
    await state.clear()


@admin_router.message(F.text=="Добавить / удалить админа")
@is_main_admin
async def add_or_delete_admin(message: types.Message, state: FSMContext, bot: Bot):
    await state.clear()
    await message.answer(text="Выберите свои дальнейшие действия", reply_markup=add_delete_admin.as_markup())


@admin_router.callback_query(F.data == "add_admin")
@is_main_admin
async def enter_new_admin_id(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    await call.message.edit_text(text="Отлично, теперь введи telegram id нового админа! Учти,"
                                      " что у нового админа должен быть чат с данным ботом",
                                 reply_markup=cancel_keyboard.as_markup())
    await state.set_state(InputMessage.enter_admin_id)


@admin_router.callback_query(F.data == "delete_admin")
@is_main_admin
async def delete_old_admin(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    keyboard = await AdminsKeyboard().generate_list()
    await call.message.edit_text(text="Отлично, теперь выбери из представленных админов, которого хочешь удалить",
                                 reply_markup=keyboard.as_markup())


@admin_router.callback_query(F.data.startswith("admin|"))
@is_main_admin
async def actions_admin(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    admin_id = call.data.split("|")[1]
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="Удалить админа", callback_data=f"delete|{admin_id}"))
    keyboard.row(InlineKeyboardButton(text="Отмена", callback_data=f"cancel"))
    await call.message.edit_text(text="Выбери свои дальнейшие действия с админом!",
                                 reply_markup=keyboard.as_markup())


@admin_router.callback_query(F.data.startswith("delete|"))
@is_main_admin
async def choice_delete_admin(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    admin_id = call.data.split("|")[1]
    await admin_repository.delete_admin_by_admin_id(int(admin_id))
    await call.message.answer(text=f"Отлично, вы удалили админа с telegram id {admin_id},"
                                   f" выберите свои дальнейшие действия!", reply_markup=admin_keyboard)
    await call.message.delete()


@admin_router.message(F.text, InputMessage.enter_admin_id)
@is_main_admin
async def add_mew_admin(message: types.Message, state: FSMContext, bot: Bot):
    try:
        message_admin = await bot.send_message(chat_id=message.text, text="Вас добавили в данного бота, как админа!")
        await admin_repository.add_admin(admin_id=int(message.text), username=message_admin.chat.username)
        await message.answer(text="Отлично, вы успешно добавили нового админа!", reply_markup=admin_keyboard)
        await message.delete()
        await state.clear()
    except:
        await message.answer(text="Данного telegram id не существует или у нового админа нет чата с ботом, убедитесь"
                                  " в корректности данных и попробуйте снова!",
                             reply_markup=cancel_keyboard.as_markup())


@admin_router.message(F.text=="Сгенерировать промокод")
@is_main_admin
async def gen_promo(message: types.Message, state: FSMContext, bot: Bot):
    await state.clear()
    await state.set_state(InputMessage.enter_promo_days)
    await message.answer("Пожалуйста, введи количество дней, которое будет давать активация данного промокода",
                         reply_markup=cancel_keyboard.as_markup())


@admin_router.message(F.text, InputMessage.enter_promo_days)
@is_main_admin
async def enter_promo_days(message: types.Message, state: FSMContext, bot: Bot):
    max_days = message.text
    if max_days.isdigit():
        await state.clear()
        await message.answer("Отлично, теперь введи максимальное количество активаций данного промокода",
                             reply_markup=cancel_keyboard.as_markup())
        await state.set_state(InputMessage.enter_max_activations_promo)
        await state.update_data(max_days=max_days)
        return
    await message.answer("Ты ввел не число, попробуй еще раз ввести количество дней,"
                         " которое будет давать активация данного промокода",
                         reply_markup=cancel_keyboard.as_markup())


@admin_router.message(F.text, InputMessage.enter_max_activations_promo)
@is_main_admin
async def enter_max_activations(message: types.Message, state: FSMContext, bot: Bot):
    max_activations = message.text
    state_data = await state.get_data()
    max_days = int(state_data.get("max_days"))
    if max_activations.isdigit():
        max_activations = int(max_activations)
        await state.clear()
        promo_code = await generate_single_promo_code()
        await referral_system_repository.add_promo(promo_code=promo_code,
                                                   max_days=max_days,
                                                   max_activations=max_activations,
                                                   type_promo="from_admin")
        await message.answer(f"Отлично, ты выпустил промокод!\n\nПромокод: <code>{promo_code}</code>")
        return
    await message.answer("Ты ввел не число, попробуй еще раз ввести"
                         " максимальное количество активаций данного промокода",
                         reply_markup=cancel_keyboard.as_markup())
