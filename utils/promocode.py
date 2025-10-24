import logging
from datetime import datetime, timedelta, timezone

from bots import main_bot
from data.keyboards import cancel_keyboard, menu_keyboard
from db.repository import referral_system_repository, users_repository, promo_activations_repository, \
    subscriptions_repository, discount_repository
from db.time_provider import get_now_utc_time
from utils.callbacks import subscribed_callback
from utils.messages_provider import send_prolong_subscription_message

logger = logging.getLogger(__name__)

async def user_entered_promo_code(user_id: int, promo_code: str, from_referral: bool = False) -> bool:
    promo = await referral_system_repository.get_promo_by_promo_code(promo_code=promo_code)
    if promo is None:
        await main_bot.send_message(
            user_id,
            "Такого промокода не существует",
            reply_markup=cancel_keyboard.as_markup())
        return False
    elif promo.bring_user_id == user_id and (promo.type_promo == "standard" or promo.type_promo == "discount"):
        await main_bot.send_message(
            user_id,
            "Ты не можешь активировать промокод, который ты сам же выпустил)",
            reply_markup=menu_keyboard.as_markup())
        return False

    if promo.type_promo == "standard":
        user = await users_repository.get_user_by_user_id(user_id=user_id)
        if user.activate_promo:
            if not from_referral:
                await main_bot.send_message(user_id,
                                            "К сожалению, мы вынуждены отказать. Ты уже активировал бонусы ранее")
            else:
                await main_bot.send_message(user_id,
                                            "К сожалению, мы вынуждены отказать. Ты уже активировал бонусы ранее",
                                            reply_markup=menu_keyboard.as_markup())
            return False
        await referral_system_repository.update_activations_by_promo_id(promo_id=promo.id)
        await promo_activations_repository.add_activation(promo_id=promo.id, activate_user_id=user_id)
        await users_repository.update_activate_promo_by_user_id(user_id=user_id)
        active_user_sub = await subscriptions_repository.get_active_subscription_by_user_id(user_id=user_id)
        if active_user_sub is None:
            await subscriptions_repository.add_subscription(user_id=user_id,
                                                            time_limit_subscription=7)
            end_date = datetime.now(timezone.utc) + timedelta(days=7)
            text = f"✅ Теперь у тебя есть <b>недельная подписка</b>! Подписка действует до {end_date.strftime('%d.%m.%y, %H:%M')} (GMT+3)"
        else:
            await subscriptions_repository.increase_subscription_time_limit(subscription_id=active_user_sub.id,
                                                                            time_to_add=7)
            end_date = active_user_sub.creation_date + timedelta(days=active_user_sub.time_limit_subscription + 7)
            text = f"✅ К текущему плану тебе добавили <b>одну неделю</b>! Подписка действует до {end_date.strftime('%d.%m.%y, %H:%M')} (GMT+3)"
        await main_bot.send_message(user_id, text)


        promo = await referral_system_repository.get_promo_by_bring_user_id(bring_user_id=promo.bring_user_id)
        bring_user_subscription = await subscriptions_repository.get_active_subscription_by_user_id(
            user_id=promo.bring_user_id)
        if promo.activations > 10:
            try:
                await main_bot.send_message(chat_id=promo.bring_user_id,
                                       text="Поздравляем, выпущенный тобой промокод только что был активирован,"
                                            " но, к сожалению, больше бонусов мы не можем тебе дать,"
                                            " так как этот промокод был активирован более 10 раз",
                                       reply_markup=menu_keyboard.as_markup())
                return True
            except Exception as e:
                logger.error(e)
                return False
        elif promo.activations == 5:
            if bring_user_subscription is None:
                end_date = datetime.now(timezone.utc) + timedelta(days=30)
                await subscriptions_repository.add_subscription(user_id=promo.bring_user_id,
                                                                time_limit_subscription=30)
                text = (f"<b>Пять друзей</b> активировали твой промокод. ✅"
                        f" Теперь у тебя есть подписка на один месяц! Подписка действует"
                        f" до {end_date.strftime('%d.%m.%y, %H:%M')} (GMT+3)")
            else:
                end_date = bring_user_subscription.creation_date + timedelta(
                    days=bring_user_subscription.time_limit_subscription + 30)
                await subscriptions_repository.increase_subscription_time_limit(
                    subscription_id=bring_user_subscription.id,
                    time_to_add=30)
                text = (f"Пять друзей активировали твой промокод. ✅"
                        f" К текущему плану тебе добавили <b>один месяц</b>!"
                        f" Теперь твоя подписка действует до {end_date.strftime('%d.%m.%y, %H:%M')} (GMT+3)")
            try:
                await main_bot.send_message(chat_id=promo.bring_user_id, text=text,
                                       reply_markup=menu_keyboard.as_markup())
                return True
            except Exception as e:
                logger.error(e)
                return False
        elif promo.activations == 10:
            if bring_user_subscription is None:
                end_date = datetime.now(timezone.utc) + timedelta(days=30)
                await subscriptions_repository.add_subscription(user_id=promo.bring_user_id,
                                                                time_limit_subscription=90)
                text = (f"<b>Десять друзей</b> активировали твой промокод. ✅"
                        f" Теперь у тебя есть подписка на три месяца!"
                        f" Подписка действует до {end_date.strftime('%d.%m.%y, %H:%M')} (GMT+3")
            else:
                end_date = bring_user_subscription.creation_date + timedelta(
                    days=bring_user_subscription.time_limit_subscription + 90)
                await subscriptions_repository.increase_subscription_time_limit(
                    subscription_id=bring_user_subscription.id,
                    time_to_add=90)
                text = (f"Десять друзей активировали твой промокод. ✅"
                        f" К текущему плану тебе добавили <b>три месяца</b>!"
                        f" Теперь твоя подписка действует до {end_date.strftime('%d.%m.%y, %H:%M')} (GMT+3)")
            try:
                await main_bot.send_message(chat_id=promo.bring_user_id, text=text,
                                       reply_markup=menu_keyboard.as_markup())
                return True
            except Exception as e:
                logger.error(e)
                return False
        elif promo.activations == 1:
            if bring_user_subscription is None:
                end_date = datetime.now(timezone.utc) + timedelta(days=7)
                await subscriptions_repository.add_subscription(user_id=promo.bring_user_id,
                                                                time_limit_subscription=7)
                text = (f"Твой друг активировал промокод. ✅ "
                        f"Теперь у тебя есть <b>недельная подписка</b>! Подписка действует до {end_date.strftime('%d.%m.%y, %H:%M')} (GMT+3)")
            else:
                end_date = bring_user_subscription.creation_date + timedelta(
                    days=bring_user_subscription.time_limit_subscription + 7)
                await subscriptions_repository.increase_subscription_time_limit(
                    subscription_id=bring_user_subscription.id,
                    time_to_add=7)
                text = (f"Твой друг активировал промокод. ✅"
                        f" К текущему плану тебе добавили одну неделю!"
                        f" Теперь твоя подписка действует до {end_date.strftime('%d.%m.%y, %H:%M')} (GMT+3)")
            try:
                await main_bot.send_message(chat_id=promo.bring_user_id, text=text,
                                       reply_markup=menu_keyboard.as_markup())
                return True
            except Exception as e:
                logger.error(e)
                return False
        else:
            await main_bot.send_message(chat_id=promo.bring_user_id, text=f"Твой друг активировал промокод. ✅"
                                                                     f" По твоему промокоду уже {promo.activations} активаций",
                                   reply_markup=menu_keyboard.as_markup())
            return True
    elif promo.type_promo == "admin":
        promo_activations = await promo_activations_repository.get_activations_by_promo_id(promo_id=promo.id)
        if promo.active is False:
            if from_referral is None or not from_referral:
                await main_bot.send_message(user_id, "К сожалению, данный промокод уже неактивен")
            else:
                await main_bot.send_message(user_id,
                                            "К сожалению, данный промокод уже неактивен",
                                            reply_markup=menu_keyboard.as_markup())
            return False
        if len(promo_activations) >= promo.max_activations:
            if from_referral is None or not from_referral:
                await main_bot.send_message(user_id,
                                            "К сожалению, данный промокод был активирован максимальное количество раз")
            else:
                await main_bot.send_message(user_id,
                                            "К сожалению, данный промокод был активирован максимальное количество раз",
                                            reply_markup=menu_keyboard.as_markup())
            return False
        if user_id in [promo_activation.activate_user_id for promo_activation in promo_activations]:
            if from_referral is None or not from_referral:
                await main_bot.send_message(user_id, "Ты уже активировал данный промокод ранее")
            else:
                await main_bot.send_message(user_id,
                                            "Ты уже активировал данный промокод ранее",
                                            reply_markup=menu_keyboard.as_markup())
            return False
        await referral_system_repository.update_activations_by_promo_id(promo_id=promo.id)
        await promo_activations_repository.add_activation(promo_id=promo.id, activate_user_id=user_id)

        active_user_sub = await subscriptions_repository.get_active_subscription_by_user_id(user_id=user_id)
        if active_user_sub is None:
            await subscriptions_repository.add_subscription(user_id=user_id,
                                                            time_limit_subscription=promo.days_sub)

            await subscribed_callback(user_id, promo.days_sub)
        else:
            await subscriptions_repository.increase_subscription_time_limit(subscription_id=active_user_sub.id,
                                                                            time_to_add=promo.days_sub)
            await send_prolong_subscription_message(user_id, promo.days_sub, active_user_sub.id)

        return True
    elif promo.type_promo == "discount":
        promo_activations = await promo_activations_repository.get_activations_by_promo_id(promo_id=promo.id)
        if promo.active is False:
            if from_referral is None or not from_referral:
                await main_bot.send_message(user_id, "К сожалению, данный промокод уже неактивен")
            else:
                await main_bot.send_message(user_id,
                                            "К сожалению, данный промокод уже неактивен",
                                            reply_markup=menu_keyboard.as_markup())
            return False
        if len(promo_activations) >= promo.max_activations:
            if from_referral is None or not from_referral:
                await main_bot.send_message(user_id,
                                            "К сожалению, данный промокод был активирован максимальное количество раз")
            else:
                await main_bot.send_message(user_id,
                                            "К сожалению, данный промокод был активирован максимальное количество раз",
                                            reply_markup=menu_keyboard.as_markup())
            return False
        if user_id in [promo_activation.activate_user_id for promo_activation in promo_activations]:
            if from_referral is None or not from_referral:
                await main_bot.send_message(user_id, "Ты уже активировал данный промокод ранее")
            else:
                await main_bot.send_message(user_id,
                                            "Ты уже активировал данный промокод ранее",
                                            reply_markup=menu_keyboard.as_markup())
            return False
        await referral_system_repository.update_activations_by_promo_id(promo_id=promo.id)
        await promo_activations_repository.add_activation(promo_id=promo.id, activate_user_id=user_id)

        await discount_repository.create_discount(user_id=user_id,
                                                  end_timestamp=get_now_utc_time() + timedelta(days=promo.days_sub),
                                                  value=promo.value)
        await main_bot.send_message(user_id, f"Теперь у тебя есть скидка в {promo.value}% на {promo.days_sub} дней!")
        return True
    return False

