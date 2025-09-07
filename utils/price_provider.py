from db.repository import users_repository
from settings import SUBSCRIPTION_PLANS, POWER_MODE_DAY_DISCOUNT
from utils.text import strike


async def get_price_for_user(user_id: int, plan: int):
    base_price = SUBSCRIPTION_PLANS[plan]

    user = await users_repository.get_user_by_user_id(user_id)

    discounted_price_multiplier = calculate_discounted_price_multiplier(user.power_mode_days)

    return round(base_price * discounted_price_multiplier)

async def get_user_price_string(user_id: int, plan: int):
    personal_price = await get_price_for_user(user_id, plan)
    return f"{strike(str(SUBSCRIPTION_PLANS[plan]) + 'р')}  {personal_price}р" if personal_price != SUBSCRIPTION_PLANS[plan] else str(personal_price) + "р"


def calculate_discounted_price_multiplier(power_mode_days: int):
    return max(.0, 1 - POWER_MODE_DAY_DISCOUNT * power_mode_days)