from db.repository import users_repository, subscriptions_repository


async def check_is_subscribed(user_id: int) -> bool:
    user = await users_repository.get_user_by_user_id(user_id=user_id)
    if user is not None and user.full_registration:
        user_sub = await subscriptions_repository.get_active_subscription_by_user_id(user_id=user_id)
        if user_sub is not None:
            return True
    return False