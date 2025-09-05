from db.models import Subscription
from db.repository import users_repository, subscriptions_repository


async def get_user_subscription(user_id: int) -> Subscription | None:
    user = await users_repository.get_user_by_user_id(user_id=user_id)
    if user is not None:
        user_sub = await subscriptions_repository.get_active_subscription_by_user_id(user_id=user_id)
        return user_sub
    return None