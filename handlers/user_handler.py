import asyncio
import logging
import traceback

from aiogram import Router, F, Bot
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state
from aiogram.types import Message, CallbackQuery

from data.keyboards import next_politic_keyboard, have_promo_keyboard, age_keyboard, \
    main_keyboard, choice_gender_keyboard, settings_cancel_keyboard, skip_enter_name_keyboard, \
    skip_enter_promocode_keyboard

from db.repository import users_repository
from handlers.standard_handler import user_request_handler
from settings import photos_pages, menu_photo, messages_dict
from utils.messages_provider import send_main_menu
from utils.paginator import MechanicsPaginator
from utils.promocode import user_entered_promo_code
from utils.state_models import InputMessage
from utils.subscription import check_is_subscribed

user_router = Router()


@user_router.callback_query(F.data == "cancel", any_state)
@user_router.callback_query(F.data == "start_menu", any_state)
async def start_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = call.from_user.id

    await send_main_menu(user_id)
    await user_request_handler.AI_handler.exit(user_id)
    await call.message.delete()

@user_router.callback_query(F.data == "start_use", any_state)
async def start_use(call: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = call.from_user.id
    user = await users_repository.get_user_by_user_id(user_id)
    await send_main_menu(user_id)
    await user_request_handler.AI_handler.exit(user_id)
    await call.message.delete()
    await asyncio.sleep(10)
    if not await check_is_subscribed(user_id):
        await call.message.answer(
            messages_dict["free_account_message"]
        )
    await asyncio.sleep(10)
    await call.message.answer(
        f"{(user.name + ', е') if user.name else 'Е'}сли что-то крутится в голове — <b>расскажи</b> 😌."
        " Это может быть просто ощущение, мысль или вопрос без ответа.",
    )

@user_router.message(Command("menu"))
@user_router.message(CommandStart(deep_link=True))
@user_router.message(CommandStart())
async def send_user_message(message: Message, command: CommandObject, state: FSMContext, bot: Bot):
    user = await users_repository.get_user_by_user_id(message.from_user.id)
    user_id = message.from_user.id
    if command.args:
        try:
            await user_entered_promo_code(user_id, command.args)
        except:
            logging.error(f"Invalid start payload: {command.args}")
            pass

    if not user:
        await users_repository.add_user(user_id=message.from_user.id, username=message.from_user.username)
        user = await users_repository.get_user_by_user_id(message.from_user.id)

    if not user.confirm_politic:
        await message.answer(messages_dict["user_agreement_message_text"],
                                 disable_web_page_preview=True,
                                 reply_markup=next_politic_keyboard.as_markup())
    elif not user.full_registration:
        if user.name is None:
            await go_to_enter_initials(bot=bot, call=message, state=state)
        elif user.gender is None:
            await message.answer("В каком роде мне к тебе обращаться?",
                                 reply_markup=choice_gender_keyboard.as_markup())
        elif user.age is None:
            await message.answer(
                "Какой возрастной диапазон тебе ближе?(Чтобы я мог лучше адаптироваться под твои запросы 🧡)",
                reply_markup=age_keyboard.as_markup())
    else:
        await send_main_menu(user_id)

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
        await state.set_state(InputMessage.enter_initials)
        message_delete = await call.message.answer("Давай знакомиться!🐿️\n\nКак мне к тебе лучше обращаться?",
                                                   reply_markup=skip_enter_name_keyboard.as_markup())
        await state.update_data(message_delete=message_delete.message_id)
        try:
            await call.message.delete()
        finally:
            return
    else:
        await state.set_state(InputMessage.enter_initials)
        message_delete = await call.answer("Давай знакомиться!🐿️\n\nКак мне к тебе лучше обращаться?",
                                           reply_markup=skip_enter_name_keyboard.as_markup())
        await state.update_data(message_delete=message_delete.message_id)
        await call.delete()


@user_router.callback_query(F.data.startswith("have_promo"))
async def have_promo(call: CallbackQuery, state: FSMContext, bot: Bot):
    answer = call.data.split("|")[1]
    if answer == "yes":
        await state.set_state(InputMessage.enter_promo)
        delete_message = await call.message.answer("🥜Отлично — введи <b>промокод</b>, который тебе передал твой друг!",
                                                   reply_markup=skip_enter_promocode_keyboard.as_markup())
        await state.update_data(delete_message_id=delete_message.message_id)
        await call.message.delete()
        return
    await go_to_enter_initials(call, state, bot)


@user_router.callback_query(F.data == "skip_enter_promo", InputMessage.enter_promo)
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


@user_router.callback_query(F.data == "skip_enter_name", InputMessage.enter_initials)
async def skip_enter_name(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer("В каком роде мне к тебе обращаться?",
                              reply_markup=choice_gender_keyboard.as_markup())
    await call.message.delete()


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

    await message.answer("В каком роде мне к тебе обращаться?",
                         reply_markup=choice_gender_keyboard.as_markup())


@user_router.callback_query(F.data.startswith("gender"), any_state)
async def user_enter_gender(call: CallbackQuery, state: FSMContext):
    user = await users_repository.get_user_by_user_id(call.from_user.id)
    gender = call.data.split("|")[1]
    await users_repository.update_gender_by_user_id(user_id=call.from_user.id, gender=gender)
    if not user.full_registration:
        await call.message.answer("Какой возрастной диапазон тебе ближе?"
                                  " (Чтобы я мог лучше адаптироваться под твои запросы 🧡)",
                                  reply_markup=age_keyboard.as_markup())
    else:
        await call.message.answer(
            "Пол сохранён!",
            reply_markup=settings_cancel_keyboard.as_markup()
        )
    await call.message.delete()


@user_router.callback_query(F.data.startswith("age"))
async def user_choice_age(call: CallbackQuery, state: FSMContext):
    age = call.data.split("|")[1]
    user_id = call.from_user.id
    user = await users_repository.get_user_by_user_id(user_id)
    if not user.full_registration:
        paginator = MechanicsPaginator(page_now=1)
        keyboard = paginator.generate_now_page()

        await call.message.answer_photo(photo=photos_pages.get(paginator.page_now),
                                        reply_markup=keyboard)
    else:
        await call.message.answer(
            "Возраст сохранён!",
            reply_markup=settings_cancel_keyboard.as_markup()
        )
    await users_repository.update_age_by_user_id(user_id=user_id, age=age)
    await users_repository.update_full_reg_by_user_id(user_id=user_id)
    await call.message.delete()
