import asyncio
import traceback
from datetime import timedelta, datetime

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state
from aiogram.types import Message, CallbackQuery

from data.keyboards import next_politic_keyboard, have_promo_keyboard, cancel_keyboard, age_keyboard, \
    main_keyboard, choice_gender_keyboard, menu_keyboard, miss_keyboard
# from data.keyboards import choice_keyboard
# from data.messages import start_message, wait_manager, update_language
from db.repository import users_repository, referral_system_repository, \
    promo_activations_repository, subscriptions_repository
from handlers.standard_handler import user_request_handler
from settings import InputMessage, photos_pages, menu_photo
from utils.paginator import MechanicsPaginator
from utils.promocode import user_entered_promo_code

user_router = Router()


@user_router.callback_query(F.data=="cancel", any_state)
@user_router.callback_query(F.data == "start_menu", any_state)
async def start_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = call.from_user.id

    text = "✍️Для общения - просто пиши, ничего выбирать не надо"
    keyboard = await main_keyboard(user_id=user_id)
    await call.message.answer_photo(photo=menu_photo,
                                    caption=text,
                                    reply_markup=keyboard.as_markup())
    await call.message.delete()
    await user_request_handler.AI_handler.exit(user_id)


@user_router.message(F.text == "/menu", any_state)
@user_router.message(F.text == "/start", any_state)
async def send_user_message(message: Message, state: FSMContext, bot: Bot):
    user = await users_repository.get_user_by_user_id(message.from_user.id)
    user_id = message.from_user.id

    if not user or not user.confirm_politic:
        if user is None:
            try:
                await users_repository.add_user(user_id=message.from_user.id, username=message.from_user.username)
            finally:
                await message.answer('🐿️📙Для начала работы необходимо согласиться с политикой и правилами'
                                     ' нашего сервиса. Наш сервис полностью защищён и работает в соответствии с 152-ФЗ.\n\n'
                                     '<b>Пользовательское соглашение</b> — https://fuhmental.ru/user\n'
                                     '<b>Соглашение об обработке персональных данных</b> — https://fuhmental.ru/agreement',
                                     disable_web_page_preview=True,
                                     reply_markup=next_politic_keyboard.as_markup())
    elif not user.full_registration:
        if user.name is None:
            await go_to_enter_initials(bot=bot, call=message, state=state)
        elif user.gender is None:
            await message.answer("В каком роде мне к тебе обращаться?🧡",
                                 reply_markup=choice_gender_keyboard.as_markup())
        elif user.age is None:
            await message.answer(
                "Какой возрастной диапазон тебе ближе?(Чтобы я мог лучше адаптироваться под твои запросы🧡)",
                reply_markup=age_keyboard.as_markup())
    else:
        text = "✍️Для общения - просто пиши, ничего выбирать не надо"
        keyboard = await main_keyboard(user_id=user_id)
        await message.answer_photo(caption=text,
                                   photo=menu_photo,
                                   reply_markup=keyboard.as_markup())

    await user_request_handler.AI_handler.exit(user_id)


@user_router.callback_query(F.data == "confirm_politic")
async def confirm_politic(call: CallbackQuery):
    await call.message.delete()
    await call.message.answer("У тебя есть промокод?🥜", reply_markup=have_promo_keyboard.as_markup())
    await users_repository.update_confirm_politic_by_user_id(user_id=call.from_user.id)


async def go_to_enter_initials(call: CallbackQuery | Message, state: FSMContext, bot: Bot):
    state_data = await state.get_data()
    message_delete = state_data.get("message_delete")
    if message_delete:
        try:
            await bot.delete_message(chat_id=call.from_user.id, message_id=message_delete)
        except:
            print(traceback.format_exc())
    if type(call) is CallbackQuery:
        # if call.from_user.first_name is None:
        await state.set_state(InputMessage.enter_initials)
        message_delete = await call.message.answer("Давай знакомиться!🐿️\n\nКак мне к тебе лучше обращаться?🧡",
                                                   reply_markup=miss_keyboard.as_markup())
        await state.update_data(message_delete=message_delete.message_id)
        try:
            await call.message.delete()
        finally:
            return
    else:
        # if call.from_user.first_name is None:
        await state.set_state(InputMessage.enter_initials)
        message_delete = await call.answer("Давай знакомиться!🐿️\n\nКак мне к тебе лучше обращаться?🧡",
                                           reply_markup=miss_keyboard.as_markup())
        await state.update_data(message_delete=message_delete.message_id)
        await call.delete()


@user_router.callback_query(F.data.startswith("have_promo"))
async def have_promo(call: CallbackQuery, state: FSMContext, bot: Bot):
    answer = call.data.split("|")[1]
    if answer == "yes":
        await state.set_state(InputMessage.enter_promo)
        delete_message = await call.message.answer("🥜Отлично — введи <b>промокод</b>, который тебе передал твой друг!",
                                                   reply_markup=miss_keyboard.as_markup())
        await state.update_data(delete_message_id=delete_message.message_id)
        await call.message.delete()
        return
    await go_to_enter_initials(call, state, bot)


@user_router.callback_query(F.data == "cancel", InputMessage.enter_promo)
async def cancel_promo(call: CallbackQuery, state: FSMContext, bot: Bot):
    user = await users_repository.get_user_by_user_id(user_id=call.from_user.id)
    user_id = call.from_user.id
    if (user is not None) and user.full_registration:
        keyboard = await main_keyboard(user_id=user_id)
        await call.message.answer_photo(photo=menu_photo,
                                        reply_markup=keyboard.as_markup())
        await call.message.delete()
        return
    await state.clear()
    await call.message.delete()
    await call.message.answer('Если в дальнейшем захочешь ввести промокод, то'
                              ' ты сможешь это сделать в разделе "Реферальная система" после небольшой регистрации)')
    await asyncio.sleep(1)
    await go_to_enter_initials(call, state, bot)


@user_router.message(F.text, InputMessage.enter_promo)
async def user_enter_promo_code(message: Message, state: FSMContext, bot: Bot):
    promo_code = message.text
    user_id = message.from_user.id
    state_data = await state.get_data()
    delete_message_id = state_data.get("delete_message_id")
    from_referral = state_data.get("from_referral")
    if delete_message_id is not None:
        await bot.delete_message(chat_id=user_id, message_id=delete_message_id)

    await user_entered_promo_code(user_id, promo_code, from_referral)

    if from_referral:
        await state.clear()
    else:
        await go_to_enter_initials(message, state, bot)

@user_router.callback_query(F.data == "cancel", InputMessage.enter_initials)
async def cancel_promo(call: CallbackQuery, state: FSMContext):
    await state.clear()
    # await call.message.answer("Какой возрастной диапазон тебе ближе?"
    #                      " (Чтобы я мог лучше адаптироваться под твои запросы🧡)",
    #                      reply_markup=age_keyboard.as_markup())
    await call.message.answer("В каком роде мне к тебе обращаться?🧡",
                              reply_markup=choice_gender_keyboard.as_markup())
    await call.message.delete()
    await users_repository.update_initials_id_by_user_id(user_id=call.from_user.id, first_name="NoName")


@user_router.message(F.text, InputMessage.enter_initials)
async def user_entered_initials(message: Message, state: FSMContext, bot: Bot):
    state_data = await state.get_data()
    message_delete = state_data.get("message_delete")
    if message_delete:
        try:
            await bot.delete_message(chat_id=message.from_user.id, message_id=message_delete)
        except:
            print(traceback.format_exc())
    data = message.text.split()
    name = data[0]
    await users_repository.update_initials_id_by_user_id(user_id=message.from_user.id,
                                                         first_name=name)

    await message.answer("В каком роде мне к тебе обращаться?🧡",
                         reply_markup=choice_gender_keyboard.as_markup())


@user_router.callback_query(F.data.startswith("gender"), any_state)
async def user_enter_gender(call: CallbackQuery, state: FSMContext):
    gender = call.data.split("|")[1]
    await users_repository.update_gender_by_user_id(user_id=call.from_user.id, gender=gender)
    await call.message.answer("Какой возрастной диапазон тебе ближе?"
                              " (Чтобы я мог лучше адаптироваться под твои запросы🧡)",
                              reply_markup=age_keyboard.as_markup())
    await call.message.delete()


@user_router.callback_query(F.data.startswith("age"))
async def user_choice_age(call: CallbackQuery, state: FSMContext):
    age = call.data.split("|")[1]
    user_id = call.from_user.id
    paginator = MechanicsPaginator(page_now=1)
    keyboard = paginator.generate_now_page()
    await call.message.answer_photo(photo=photos_pages.get(paginator.page_now),
                                    reply_markup=keyboard)
    await call.message.delete()
    await users_repository.update_age_by_user_id(user_id=user_id, age=age)
    await users_repository.update_full_reg_by_user_id(user_id=user_id)
