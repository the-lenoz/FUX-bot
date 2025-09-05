import asyncio

from bots import main_bot
from db.repository import pending_messages_repository, recommendations_repository
from settings import messages_dict, you_fooher_photo
from utils.checkup_stat import send_weekly_checkup_report, send_monthly_checkup_report
from utils.gpt_distributor import user_request_handler
from utils.messages_provider import send_subscription_management_menu, send_new_subscription_message


async def subscribed_callback(user_id: int, subscription_days: int, paid: bool = False):
    await main_bot.send_photo(user_id, you_fooher_photo)
    await asyncio.sleep(7)
    await send_subscription_management_menu(user_id)
    await asyncio.sleep(7)
    await send_new_subscription_message(user_id, subscription_days, paid)

    pending_messages = await pending_messages_repository.get_user_pending_messages(user_id)
    if pending_messages.recommendation_id:
        await main_bot.send_message(
            user_id,
            messages_dict["got_recommendation_on_subscription_start"]
        )
        recommendation = await recommendations_repository.get_recommendation_by_recommendation_id(pending_messages.recommendation_id)
        await user_request_handler.AI_handler.send_recommendation(user_id, recommendation.text, recommendation.problem_id)
    if pending_messages.weekly_tracking_date:
        await send_weekly_checkup_report(user_id, pending_messages.weekly_tracking_date)
    if pending_messages.monthly_tracking_date:
        await send_monthly_checkup_report(user_id, pending_messages.weekly_tracking_date)
    await pending_messages_repository.update_user_pending_messages(user_id, weekly_tracking_date=None, monthly_tracking_date=None, recommendation_id=None)


