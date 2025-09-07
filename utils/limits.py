from bots import main_bot
from data.keyboards import buy_sub_keyboard
from data.message_templates import messages_dict
from db.repository import limits_repository
from settings import LIMITS_NOTIFICATION_THRESHOLDS


async def decrease_psy_requests_limit(user_id: int) -> bool:
    user_limits = await limits_repository.get_user_limits(user_id=user_id)

    if not user_limits.psychological_requests_remaining:
        return False

    await limits_repository.update_user_limits(
        user_id=user_id,
        psychological_requests_remaining=user_limits.psychological_requests_remaining - 1
    )

    if user_limits.psychological_requests_remaining - 1 in LIMITS_NOTIFICATION_THRESHOLDS["psychological_requests"]:
        await main_bot.send_message(
            user_id,
            messages_dict["limit_remaining_notification_text"].format(
                n=user_limits.psychological_requests_remaining - 1,
                item_name="психологических запросов"),
            reply_markup=buy_sub_keyboard.as_markup()
        )

    return True

async def decrease_universal_requests_limit(user_id: int):
    user_limits = await limits_repository.get_user_limits(user_id=user_id)

    if not user_limits.universal_requests_remaining:
        return False

    await limits_repository.update_user_limits(
        user_id=user_id,
        universal_requests_remaining=user_limits.universal_requests_remaining - 1
    )

    if user_limits.universal_requests_remaining - 1 in LIMITS_NOTIFICATION_THRESHOLDS["universal_requests"]:
        await main_bot.send_message(
            user_id,
            messages_dict["limit_remaining_notification_text"].format(
                n=user_limits.universal_requests_remaining - 1,
                item_name="универсальных запросов"),
            reply_markup=buy_sub_keyboard.as_markup()
        )

    return True

async def decrease_attachments_limit(user_id: int):
    user_limits = await limits_repository.get_user_limits(user_id=user_id)

    if not user_limits.attachments_remaining:
        return False

    await limits_repository.update_user_limits(
        user_id=user_id,
        attachments_remaining=user_limits.attachments_remaining - 1
    )

    if user_limits.attachments_remaining - 1 in LIMITS_NOTIFICATION_THRESHOLDS["attachments"]:
        await main_bot.send_message(
            user_id,
            messages_dict["limit_remaining_notification_text"].format(
                n=user_limits.attachments_remaining - 1,
                item_name="файлов и картинок"),
            reply_markup=buy_sub_keyboard.as_markup()
        )

    return True

async def decrease_voices_limit(user_id: int):
    user_limits = await limits_repository.get_user_limits(user_id=user_id)

    if not user_limits.voices_remaining:
        return False

    await limits_repository.update_user_limits(
        user_id=user_id,
        voices_remaining=user_limits.voices_remaining - 1
    )

    if user_limits.voices_remaining - 1 in LIMITS_NOTIFICATION_THRESHOLDS["voices"]:
        await main_bot.send_message(
            user_id,
            messages_dict["limit_remaining_notification_text"].format(
                n=user_limits.voices_remaining - 1,
                item_name="голосовых сообщений"),
            reply_markup=buy_sub_keyboard.as_markup()
        )

    return True

async def decrease_exercises_limit(user_id: int):
    user_limits = await limits_repository.get_user_limits(user_id=user_id)

    if not user_limits.exercises_remaining:
        return False

    await limits_repository.update_user_limits(
        user_id=user_id,
        exercises_remaining=user_limits.exercises_remaining - 1
    )

    if user_limits.exercises_remaining - 1 in LIMITS_NOTIFICATION_THRESHOLDS["exercises"]:
        await main_bot.send_message(
            user_id,
            messages_dict["limit_remaining_notification_text"].format(
                n=user_limits.exercises_remaining - 1,
                item_name="упражнений"),
            reply_markup=buy_sub_keyboard.as_markup()
        )

    return True