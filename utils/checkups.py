from datetime import datetime, timezone, timedelta

from bots import main_bot
from data.keyboards import emotions_keyboard, productivity_keyboard
from db.repository import days_checkups_repository, checkup_repository
from data.images import checkup_emotions_photo, checkup_productivity_photo, productivity_emoji_description_photo, \
    emotions_emoji_description_photo


async def send_checkup(checkup_id: int):
    checkup = await checkup_repository.get_checkup_by_checkup_id(checkup_id)
    now_date = datetime.now(timezone.utc).replace(tzinfo=None)
    checkup_day = await days_checkups_repository.get_active_day_checkup_by_checkup_id(checkup_id=checkup.id)
    if checkup_day is None:
        days_checkup = await days_checkups_repository.get_days_checkups_by_checkup_id(checkup_id=checkup.id)
        await days_checkups_repository.add_day_checkup(checkup_id=checkup.id,
                                                       day=len(days_checkup) + 1,
                                                       points=0,
                                                       user_id=checkup.user_id,
                                                       checkup_type=checkup.type_checkup)
        checkup_day = await days_checkups_repository.get_active_day_checkup_by_checkup_id(checkup_id=checkup.id)
    checkup_id, day_checkup_id, type_checkup = checkup.id, checkup_day.id, checkup.type_checkup

    emotions_photo, productivity_photo = (checkup_emotions_photo, checkup_productivity_photo) if now_date - checkup.creation_date.replace(tzinfo=None) > timedelta(weeks=1) else (emotions_emoji_description_photo, productivity_emoji_description_photo)

    message_photo = emotions_photo
    check_data = "|".join([str(checkup_id), str(day_checkup_id), type_checkup])
    keyboard = emotions_keyboard(check_data)
    if type_checkup == "productivity":
        message_photo = productivity_photo
        keyboard = productivity_keyboard(check_data)
    await main_bot.send_photo(photo=message_photo,
                              chat_id=checkup.user_id,
                              reply_markup=keyboard.as_markup())
    await checkup_repository.update_last_date_send_checkup_by_checkup_id(checkup_id=checkup.id,
                                                                         last_date_send=now_date)


