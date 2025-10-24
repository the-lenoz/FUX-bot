from typing import List, Iterable

from db.repository import users_repository, discount_repository
from settings import SUBSCRIPTION_PLANS, POWER_MODE_DAY_DISCOUNT, MAX_POWER_MODE_DISCOUNT
from utils.text import strike


async def get_price_for_user(user_id: int, plan: int):
    base_price = SUBSCRIPTION_PLANS[plan]

    user = await users_repository.get_user_by_user_id(user_id)
    discounts = await discount_repository.get_discounts_by_user_id(user_id)

    discounted_price_multiplier = calculate_discounted_price_multiplier(user.power_mode_days,
                                                                        (discount.value for discount in discounts))

    return round(base_price * discounted_price_multiplier)

async def get_user_price_string(user_id: int, plan: int):
    personal_price = await get_price_for_user(user_id, plan)
    return f"{strike(str(SUBSCRIPTION_PLANS[plan]) + 'р')}  {personal_price}р" \
        if personal_price != SUBSCRIPTION_PLANS[plan] else str(personal_price) + "р"


def calculate_discounted_price_multiplier(power_mode_days: int, user_discount_values: Iterable[int]):
    nut_discount_multiplier = max(1 - MAX_POWER_MODE_DISCOUNT, 1 - POWER_MODE_DAY_DISCOUNT * power_mode_days)
    personal_discount_multiplier = 1
    for value in user_discount_values:
        personal_discount_multiplier *= (1 - value / 100)

    return nut_discount_multiplier * personal_discount_multiplier