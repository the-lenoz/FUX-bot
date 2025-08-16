from db.repository import ai_requests_repository, checkup_repository, events_repository, exercises_user_repository, \
    mental_problems_repository, payment_methods_repository, recommendations_repository, \
    subscriptions_repository, user_timezone_repository, users_repository, pending_messages_repository


async def delete_user(user_id: int):
    await ai_requests_repository.delete_requests_by_user_id(user_id)

    await checkup_repository.delete_checkups_by_user_id(user_id)

    await events_repository.delete_events_by_user_id(user_id)

    await exercises_user_repository.delete_exercises_by_user_id(user_id)

    await payment_methods_repository.delete_payment_method_by_user_id(user_id)

    await pending_messages_repository.delete_pending_messages_by_user_id(user_id)

    await recommendations_repository.delete_recommendations_by_user_id(user_id)

    await subscriptions_repository.delete_subscriptions_by_user_id(user_id)

    await user_timezone_repository.delete_user_timezone_by_user_id(user_id)

    await mental_problems_repository.delete_problems_by_user_id(user_id)

    await users_repository.delete_user_by_id(user_id)