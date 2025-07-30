import datetime
from typing import List

from pydantic import BaseModel

from db.repository import users_repository, operation_repository, ai_requests_repository, events_repository, \
    checkup_repository
from settings import messages_dict


class MainStatistics(BaseModel):
    new_users_per_day: int = 0
    new_users_per_week: int = 0
    new_users_per_month: int = 0
    all_users: int = 0

    current_day_active_users: int = 0
    current_week_active_users: int = 0
    current_month_active_users: int = 0

    payments_per_day: int = 0
    payments_per_week: int = 0
    payments_per_month: int = 0
    all_payments: int = 0

    promocodes_per_day: int = 0
    promocodes_per_week: int = 0
    promocodes_per_month: int = 0
    all_promocodes: int = 0

    new_messages_per_day: int = 0
    new_messages_per_week: int = 0
    new_messages_per_month: int = 0

    active_trackings: int = 0

    top_3_users_str: str = ""

    all_messages: int = 0

    @staticmethod
    async def generate():
        now_date = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

        operations = await operation_repository.select_all_operations()
        events = await events_repository.select_all_events()
        active_trackings = await checkup_repository.select_all_active_checkups()
        users = await users_repository.select_all_users()

        payments_per_day: int = 0
        payments_per_week: int = 0
        payments_per_month: int = 0
        all_payments: int = 0

        for operation in operations:
            if operation.is_paid:
                if now_date.date() == operation.creation_date.date():
                    payments_per_day += 1
                if (now_date.isocalendar().week == operation.creation_date.isocalendar().week
                        and now_date.isocalendar().year == operation.creation_date.isocalendar().year):
                    payments_per_week += 1
                if now_date.month == operation.creation_date.month and now_date.year == operation.creation_date.year:
                    payments_per_month += 1
                all_payments += 1

        new_users_per_day: int = 0
        new_users_per_week: int = 0
        new_users_per_month: int = 0
        all_users = 0

        for user in users:
            if now_date.date() == user.creation_date.date():
                new_users_per_day += 1
            if (now_date.isocalendar().week == user.creation_date.isocalendar().week
                    and now_date.isocalendar().year == user.creation_date.isocalendar().year):
                new_users_per_week += 1
            if now_date.month == user.creation_date.month and now_date.year == user.creation_date.year:
                new_users_per_month += 1
            all_users += 1

        current_day_active_users_set = set()
        current_week_active_users_set = set()
        current_month_active_users_set = set()
        for event in events:
            if now_date.date() == event.creation_date.date():
                current_day_active_users_set.add(event.user_id)
            if (now_date.isocalendar().week == event.creation_date.isocalendar().week
                    and now_date.isocalendar().year == event.creation_date.isocalendar().year):
                current_week_active_users_set.add(event.user_id)
            if now_date.month == event.creation_date.month and now_date.year == event.creation_date.year:
                current_month_active_users_set.add(event.user_id)

        return MainStatistics(
            new_users_per_day=new_users_per_day,
            new_users_per_week=new_users_per_week,
            new_users_per_month=new_users_per_month,
            all_users=all_users,
            current_day_active_users=len(current_day_active_users_set),
            current_week_active_users=len(current_week_active_users_set),
            current_month_active_users=len(current_week_active_users_set),
            payments_per_day=payments_per_day,
            payments_per_week=payments_per_week,
            payments_per_month=payments_per_month,
            all_payments=all_payments,
            new_messages_per_day=0,
            new_messages_per_week=0,
            promocodes_per_day=0,
            promocodes_per_week=0,
            promocodes_per_month=0,
            active_trackings=len(active_trackings),
            top_3_users_str="",
            all_messages=0
        )

async def generate_statistics_text():
    statistics = await MainStatistics.generate()
    return messages_dict["statistic_message_format"].format(**statistics.model_dump())

