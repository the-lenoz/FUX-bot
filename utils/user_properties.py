from db.repository import users_repository
from utils.prompts import SENSITIVE_PROMPT, STRAIGHTFORWARD_PROMPT


async def get_user_description(user_id: int, is_psy: bool = False) -> str:
    user = await users_repository.get_user_by_user_id(user_id)

    description = ['СТРОГО! Общайся с пользователем на "ты" или по имени. Никогда не на "Вы".\n\n']

    if user.name and user.name != "NoName":
        description.append(f"\nName: {user.name}\n")
    if user.gender:
        description.append(f"\nGender: {user.gender}\n")
    if user.age:
        description.append(f"\nAge: {user.age}\n")

    if user.ai_temperature == 0.6:
        description.append(STRAIGHTFORWARD_PROMPT)
    elif user.ai_temperature == 1.3:
        description.append(SENSITIVE_PROMPT)

    if user.mental_data and is_psy:
        description.append(user.mental_data)

    return "".join(description)