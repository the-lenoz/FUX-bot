from bots import main_bot
from data.keyboards import next_politic_keyboard, choice_gender_keyboard, age_keyboard, have_promo_keyboard
from db.repository import ai_requests_repository, checkup_repository, events_repository, exercises_user_repository, \
    mental_problems_repository, payment_methods_repository, recommendations_repository, \
    subscriptions_repository, user_timezone_repository, users_repository, pending_messages_repository
from settings import messages_dict


async def delete_user(user_id: int):
    await ai_requests_repository.delete_requests_by_user_id(user_id)

    await checkup_repository.delete_checkups_by_user_id(user_id)

    await events_repository.delete_events_by_user_id(user_id)

    await exercises_user_repository.delete_exercises_by_user_id(user_id)

    await payment_methods_repository.delete_payment_method_by_user_id(user_id)

    await pending_messages_repository.delete_pending_messages_by_user_id(user_id)

    await recommendations_repository.delete_recommendations_by_user_id(user_id)

    await subscriptions_repository.delete_subscriptions_by_user_id(user_id)

    await user_timezone_repository.delete_user_timezone_by_user_id(user_id)

    await mental_problems_repository.delete_problems_by_user_id(user_id)

    await users_repository.delete_user_by_id(user_id)

async def continue_registration(user_id: int):
    user = await users_repository.get_user_by_user_id(user_id)
    if not user.confirm_politic:
        await main_bot.send_message(user_id, messages_dict["user_agreement_message_text"],
                             disable_web_page_preview=True,
                             reply_markup=next_politic_keyboard.as_markup())
    elif not user.name:
        await main_bot.send_message(user_id, "У тебя есть промокод?🥜", reply_markup=have_promo_keyboard.as_markup())
    elif not user.gender:
        await main_bot.send_message(user_id, "В каком роде мне к тебе обращаться?",
                            reply_markup=choice_gender_keyboard.as_markup())
    elif not user.age:
        await main_bot.send_message(user_id,
            "Какой возрастной диапазон тебе ближе?(Чтобы я мог лучше адаптироваться под твои запросы 🧡)",
            reply_markup=age_keyboard.as_markup())