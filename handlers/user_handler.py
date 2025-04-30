import asyncio
import traceback
from datetime import timedelta, datetime

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state
from aiogram.types import Message, CallbackQuery

from data.keyboards import next_politic_keyboard, have_promo_keyboard, cancel_keyboard, age_keyboard, \
    main_keyboard, choice_gender_keyboard, menu_keyboard, miss_keyboard
# from data.keyboards import choice_keyboard
# from data.messages import start_message, wait_manager, update_language
from db.repository import users_repository, referral_system_repository, \
    promo_activations_repository, subscriptions_repository
from settings import InputMessage, photos_pages, menu_photo
from utils.paginator import MechanicsPaginator

user_router = Router()


@user_router.callback_query(F.data == "start_menu", any_state)
async def start_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = call.from_user.id
    user_sub = await subscriptions_repository.get_active_subscription_by_user_id(user_id=user_id)
    if user_sub is None:
        text = "На данный момент у тебя базовый режим 🐿️"
    else:
        end_date = user_sub.creation_date + timedelta(days=user_sub.time_limit_subscription)
        text = (f"🐿️Твоя подписка активна до"
                f" {end_date.strftime('%d.%m.%y, %H:%M')} +GMT3")
    keyboard = await main_keyboard(user_id=user_id)
    await call.message.answer_photo(photo=menu_photo,
                                    caption=text,
                                    reply_markup=keyboard.as_markup())
    await call.message.delete()



@user_router.message(F.text == "/menu", any_state)
@user_router.message(F.text == "/start", any_state)
async def send_user_message(message: Message, state: FSMContext, bot: Bot):
    user = await users_repository.get_user_by_user_id(message.from_user.id)
    user_id = message.from_user.id
    # quote = "> Это цитата, выделенная с помощью MarkdownV2"
    # explanation = "Это обучающий текст, который объясняет смысл приведённой цитаты\."
    #
    # # Объединяем части через два перевода строки (первый перевод может быть использован для разрыва цитаты, а второй для начала нового абзаца)
    # message_text = f"{quote}\n\n{explanation}"
    # await message.answer(message_text, parse_mode="MarkdownV2")
    if user is None or not user.confirm_politic:
        if user is None:
            try:
                await users_repository.add_user(user_id=message.from_user.id, username=message.from_user.username)
            finally:
                await message.answer('🐿️📙Для начала работы необходимо согласиться с политикой и правилами'
                                     ' нашего сервиса. Наш сервис полностью защищён и работает в соответствии с 152-ФЗ.\n\n'
                                     '<b>Пользовательское соглашение:</b> https://disk.yandex.ru/i/3xWhbQXOrWdAig\n\n<b>Соглашение'
                                     ' об обработке персональных данных:</b> https://disk.yandex.ru/i/pJmigSHkLXekLQ',
                                     disable_web_page_preview=True,
                                     reply_markup=next_politic_keyboard.as_markup())
    elif not user.full_registration:
        if user.name is None:
            await go_to_enter_initials(bot=bot, call=message, state=state)
        elif user.gender is None:
            await message.answer("В каком роде мне к тебе обращаться?🧡",
                                 reply_markup=choice_gender_keyboard.as_markup())
        elif user.age is None:
            await message.answer("Какой возрастной диапазон тебе ближе?(Чтобы я мог лучше адаптироваться под твои запросы🧡)",
                                 reply_markup=age_keyboard.as_markup())
    else:
        user_sub = await subscriptions_repository.get_active_subscription_by_user_id(user_id=user_id)
        if user_sub is None:
            text = "На данный момент у тебя базовый режим 🐿️"
        else:
            end_date = user_sub.creation_date + timedelta(days=user_sub.time_limit_subscription)
            text = (f"🐿️Твоя подписка активна до"
                    f" {end_date.strftime('%d.%m.%y, %H:%M')} +GMT3")
        keyboard = await main_keyboard(user_id=user_id)
        await message.answer_photo(caption=text,
                                   photo=menu_photo,
                                    reply_markup=keyboard.as_markup())


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
        message_delete = await call.answer("Давай знакомиться!🐿️\n\nКак мне к тебе лучше обращаться?🧡", reply_markup=miss_keyboard.as_markup())
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
    promo = await referral_system_repository.get_promo_by_promo_code(promo_code=promo_code)
    if promo is None:
        await message.answer("Такого промокода не существует",
                             reply_markup=cancel_keyboard.as_markup())
        return
    elif promo.bring_user_id == message.from_user.id and promo.type_promo == "standard":
        await message.answer("Ты не можешь активировать промокод, который ты сам же выпустил)",
                             reply_markup=menu_keyboard.as_markup())
        return
    await state.clear()
    # delete_message = await message.answer("Секундочку, загружаем информацию о промокоде)")
    if promo.type_promo == "standard":
        user = await users_repository.get_user_by_user_id(user_id=user_id)
        if user.activate_promo:
            if from_referral is None or not from_referral:
                await message.answer("К сожалению, мы вынуждены отказать. Ты уже активировал бонусы ранее")
                await go_to_enter_initials(message, state, bot)
            else:
                await message.answer("К сожалению, мы вынуждены отказать. Ты уже активировал бонусы ранее",
                                     reply_markup=menu_keyboard.as_markup())
            return
        await referral_system_repository.update_activations_by_promo_id(promo_id=promo.id)
        await promo_activations_repository.add_activation(promo_id=promo.id, activate_user_id=user_id)
        await users_repository.update_activate_promo_by_user_id(user_id=user_id)
        activate_user_sub = await subscriptions_repository.get_active_subscription_by_user_id(user_id=user_id)
        if activate_user_sub is None:
            await subscriptions_repository.add_subscription(user_id=user_id,
                                                            time_limit_subscription=7)
            end_date = datetime.now() + timedelta(days=7)
            text = f"✅ Теперь у тебя есть <b>недельная подписка</b>! Подписка действует до {end_date.strftime('%d.%m.%y, %H:%M')} (GMT+3)"
        else:
            await subscriptions_repository.update_time_limit_subscription(subscription_id=activate_user_sub.id,
                                                                          new_time_limit=7)
            end_date = activate_user_sub.creation_date + timedelta(days=activate_user_sub.time_limit_subscription + 7)
            text = f"✅ К текущему плану тебе добавили <b>одну неделю</b>! Подписка действует до {end_date.strftime('%d.%m.%y, %H:%M')} (GMT+3)"
        await message.answer(text=text)



        if from_referral is None and not from_referral:
            await go_to_enter_initials(message, state, bot)
        await asyncio.sleep(2)
        promo = await referral_system_repository.get_promo_by_bring_user_id(bring_user_id=promo.bring_user_id)
        activations = promo.activations
        bring_user_subscription = await subscriptions_repository.get_active_subscription_by_user_id(user_id=promo.bring_user_id)
        if activations > 10:
            try:
                await bot.send_message(chat_id=promo.bring_user_id,
                                       text="Поздравляем, выпущенный тобой промокод только что бы активирован,"
                                     " но, к сожалению, больше бонусов мы не можем тебе дать,"
                                     " так как этот промокод был активирован более 10 раз",
                                     reply_markup=menu_keyboard.as_markup())
            except:
                print(traceback.format_exc())
        elif activations == 5:
            if bring_user_subscription is None:
                end_date = datetime.now() + timedelta(days=30)
                await subscriptions_repository.add_subscription(user_id=promo.bring_user_id,
                                                                time_limit_subscription=30)
                text = (f"<b>Пять друзей</b> активировали твой промокод. ✅"
                        f" Теперь у тебя есть подписка на один месяц! Подписка действует"
                        f" до {end_date.strftime('%d.%m.%y, %H:%M')} (GMT+3)")
            else:
                end_date = bring_user_subscription.creation_date + timedelta(days=bring_user_subscription.time_limit_subscription + 30)
                await subscriptions_repository.update_time_limit_subscription(subscription_id=bring_user_subscription.id,
                                                                              new_time_limit=30)
                text = (f"Пять друзей активировали твой промокод. ✅"
                        f" К текущему плану тебе добавили <b>один месяц</b>!"
                        f" Теперь твоя подписка действует до {end_date.strftime('%d.%m.%y, %H:%M')} (GMT+3)")
            try:
                await bot.send_message(chat_id=promo.bring_user_id, text=text,
                                     reply_markup=menu_keyboard.as_markup())
            except:
                print(traceback.format_exc())
        elif activations == 10:
            if bring_user_subscription is None:
                end_date = datetime.now() + timedelta(days=30)
                await subscriptions_repository.add_subscription(user_id=promo.bring_user_id,
                                                                time_limit_subscription=90)
                text = (f"<b>Десять друзей</b> активировали твой промокод. ✅"
                        f" Теперь у тебя есть подписка на три месяца!"
                        f" Подписка действует до {end_date.strftime('%d.%m.%y, %H:%M')} (GMT+3")
            else:
                end_date = bring_user_subscription.creation_date + timedelta(
                    days=bring_user_subscription.time_limit_subscription + 90)
                await subscriptions_repository.update_time_limit_subscription(subscription_id=bring_user_subscription.id,
                                                                              new_time_limit=90)
                text = (f"Десять друзей активировали твой промокод. ✅"
                        f" К текущему плану тебе добавили <b>три месяца</b>!"
                        f" Теперь твоя подписка действует до {end_date.strftime('%d.%m.%y, %H:%M')} (GMT+3)")
            try:
                await bot.send_message(chat_id=promo.bring_user_id, text=text,
                                     reply_markup=menu_keyboard.as_markup())
            except:
                print(traceback.format_exc())
        elif activations == 1:
            if bring_user_subscription is None:
                end_date = datetime.now() + timedelta(days=7)
                await subscriptions_repository.add_subscription(user_id=promo.bring_user_id,
                                                                time_limit_subscription=7)
                text = (f"Твой друг активировал промокод. ✅ "
                        f"Теперь у тебя есть <b>недельная подписка</b>! Подписка действует до {end_date.strftime('%d.%m.%y, %H:%M')} (GMT+3)")
            else:
                end_date = bring_user_subscription.creation_date + timedelta(
                    days=bring_user_subscription.time_limit_subscription + 7)
                await subscriptions_repository.update_time_limit_subscription(subscription_id=bring_user_subscription.id,
                                                                              new_time_limit=7)
                text = (f"Твой друг активировал промокод. ✅"
                        f" К текущему плану тебе добавили одну неделю!"
                        f" Теперь твоя подписка действует до {end_date.strftime('%d.%m.%y, %H:%M')} (GMT+3)")
            try:
                await bot.send_message(chat_id=promo.bring_user_id, text=text,
                                     reply_markup=menu_keyboard.as_markup())
            except:
                print(traceback.format_exc())
        else:
            await bot.send_message(chat_id=promo.bring_user_id, text=f"Твой друг активировал промокод. ✅"
                                                                     f" По твоему промокоду уже {activations} активаций",
                                   reply_markup=menu_keyboard.as_markup())
    else:
        promo_activations = await promo_activations_repository.get_activations_by_promo_id(promo_id=promo.id)
        if promo.active is False:
            if from_referral is None or not from_referral:
                await message.answer("К сожалению, данный промокод уже неактивен")
                await go_to_enter_initials(message, state, bot)
            else:
                await message.answer("К сожалению, данный промокод уже неактивен",
                                     reply_markup=menu_keyboard.as_markup())
            return
        if len(promo_activations) >= promo.max_activations:
            if from_referral is None or not from_referral:
                await message.answer("К сожалению, данный промокод был активирован максимальное количество раз")
                await go_to_enter_initials(message, state, bot)
            else:
                await message.answer("К сожалению, данный промокод был активирован максимальное количество раз",
                                     reply_markup=menu_keyboard.as_markup())
            return
        if user_id in [promo_activation.activate_user_id for promo_activation in promo_activations]:
            if from_referral is None or not from_referral:
                await message.answer("Ты уже активировал данный промокод ранее")
                await go_to_enter_initials(message, state, bot)
            else:
                await message.answer("Ты уже активировал данный промокод ранее",
                                     reply_markup=menu_keyboard.as_markup())
            return
        await referral_system_repository.update_activations_by_promo_id(promo_id=promo.id)
        await promo_activations_repository.add_activation(promo_id=promo.id, activate_user_id=user_id)
        # await users_repository.update_activate_promo_by_user_id(user_id=user_id)
        activate_user_sub = await subscriptions_repository.get_active_subscription_by_user_id(user_id=user_id)
        if activate_user_sub is None:
            await subscriptions_repository.add_subscription(user_id=user_id,
                                                            time_limit_subscription=promo.days_sub)
            end_date = datetime.now() + timedelta(days=promo.days_sub)
            text = f"✅ Теперь у тебя есть подписка на <b>{promo.days_sub} дней</b>! Подписка действует до {end_date.strftime('%d.%m.%y, %H:%M')} (GMT+3)"
        else:
            await subscriptions_repository.update_time_limit_subscription(subscription_id=activate_user_sub.id,
                                                                          new_time_limit=promo.days_sub)
            end_date = activate_user_sub.creation_date + timedelta(days=activate_user_sub.time_limit_subscription + promo.days_sub)
            text = f"✅ К текущему плану тебе добавили <b>{promo.days_sub} дней</b>! Подписка действует до {end_date.strftime('%d.%m.%y, %H:%M')} (GMT+3)"
        await message.answer(text=text)

        if from_referral is None and not from_referral:
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
async def user_enter_promo_code(message: Message, state: FSMContext, bot: Bot):
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
    # await message.answer("Какой возрастной диапазон тебе ближе?"
    #                           " (Чтобы я мог лучше адаптироваться под твои запросы🧡)",
    #                           reply_markup=age_keyboard.as_markup())
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
