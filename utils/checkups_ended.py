from datetime import datetime

from db.repository import days_checkups_repository


async def is_ended_today(checkup_id: int) -> bool:
    day_checkup = await days_checkups_repository.get_latest_ended_day_checkup_by_checkup_id(checkup_id)
    if day_checkup and day_checkup.date_end_day and day_checkup.date_end_day.date() == datetime.now().date():
        return True
    return False
