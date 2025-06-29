from db.repository import users_repository, mental_problems_repository, exercises_user_repository, admin_repository, \
    ai_requests_repository, checkup_repository, days_checkups_repository, subscriptions_repository
from utils.prompts import SENSITIVE_PROMPT, STRAIGHTFORWARD_PROMPT


async def get_user_description(user_id: int, is_psy: bool = False) -> str:
    user = await users_repository.get_user_by_user_id(user_id)

    description = ['СТРОГО! Общайся с пользователем на "ты" или по имени. Никогда не на "Вы".\n\n']

    if user.name:
        description.append(f"\nName: {user.name}\n")
    if user.gender:
        description.append(f"\nGender: {user.gender}\n")
    if user.age:
        description.append(f"\nAge: {user.age}\n")

    if is_psy:
        user_problems = await mental_problems_repository.get_problems_by_user_id(user_id=user_id)

        problems_data = "\n\n\nПроблемы пользователя:(\n\n\n" + "\n\n".join(
            [problem.problem_summary + "\nПользователь прорабатывал проблему следующими упражнениями:[" +
             "\n-\n".join([exercise.text
                           for exercise in await exercises_user_repository.get_exercises_by_problem_id(problem.id)]) +
             "]"
             for problem in user_problems]
        ) + ")"

        description.append(problems_data)

    return "".join(description)


async def delete_user(user_id: int):
    await admin_repository.delete_admin_by_admin_id(user_id)

    checkups = await checkup_repository.get_checkups_by_user_id(user_id)
    for checkup in checkups:
        await checkup_repository.delete_checkup_by_checkup_id(checkup.id)

    subscription = await subscriptions_repository.get_active_subscription_by_user_id(user_id)
    if subscription:
        await subscriptions_repository.deactivate_subscription(subscription.id)

    await users_repository.delete_user_by_id(user_id) # DO NOT USE