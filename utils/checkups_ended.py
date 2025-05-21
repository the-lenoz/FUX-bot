from datetime import datetime

from db.repository import days_checkups_repository


async def sent_today(day_checkup_id: int) -> bool:
    day_checkup = await days_checkups_repository.get_latest_ended_day_checkup_by_checkup_id(day_checkup_id)
    if day_checkup and day_checkup.creation_date and day_checkup.creation_date.date() == datetime.now().date():
        return True
    return False
