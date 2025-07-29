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

    top_3_active_users: List[str]

    all_messages: int = 0

    @staticmethod
    async def generate():
        now_date = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        users_count_statistic = await users_repository.get_user_creation_statistics()
        messages_count_statistic = await ai_requests_repository.get_ai_requests_statistics()

        operations = await operation_repository.select_all_operations()
        events = await events_repository.select_all_events()
        active_trackings = await checkup_repository.select_all_active_checkups()

        payments_per_day: int = 0
        payments_per_week: int = 0
        all_payments: int = 0

        for operation in sorted(operations, key=lambda op: op.upd_date, reverse=True):
            if operation.is_paid:
                if now_date - operation.upd_date.replace(tzinfo=None) < datetime.timedelta(hours=24):
                    payments_per_day += 1
                if now_date - operation.upd_date.replace(tzinfo=None) < datetime.timedelta(days=7):
                    payments_per_week += 1
                all_payments += 1

        current_day_active_users_set = set()
        current_week_active_users_set = set()
        for event in events:
            if now_date - event.creation_date.replace(tzinfo=None) < datetime.timedelta(hours=24):
                current_day_active_users_set.add(event.user_id)
            if now_date - event.creation_date.replace(tzinfo=None) < datetime.timedelta(days=7):
                current_week_active_users_set.add(event.user_id)

        return MainStatistics(
            new_users_per_day=users_count_statistic.get('day'),
            new_users_per_week=users_count_statistic.get('week'),
            all_users=users_count_statistic.get('all_time'),
            payments_per_day=payments_per_day,
            payments_per_week=payments_per_week,
            all_payments=all_payments,
            new_messages_per_day=messages_count_statistic.get('day').get('total'),
            new_messages_per_week=messages_count_statistic.get('week').get('total'),
            all_messages=messages_count_statistic.get('all_time').get('total'),
            current_day_active_users=len(current_day_active_users_set),
            current_week_active_users=len(current_week_active_users_set),
            active_trackings=len(active_trackings)
        )

async def generate_statistics_text():
    statistics = await MainStatistics.generate()
    return messages_dict["statistic_message_format"].format(**statistics.model_dump())

