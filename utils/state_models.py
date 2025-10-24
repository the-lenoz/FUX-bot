from aiogram.fsm.state import StatesGroup, State


class InputMessage(StatesGroup):
    enter_admin_id = State()
    enter_message_mailing = State()
    enter_promo = State()
    enter_initials = State()
    enter_answer_fast_help = State()
    enter_answer_go_deeper = State()
    enter_email = State()
    enter_time_checkup = State()
    enter_timezone = State()
    edit_time_checkup = State()
    enter_answer_exercise = State()
    enter_promo_days = State()
    enter_max_activations_promo = State()
    enter_discount_value = State()


class AccountSettingsStates(StatesGroup):
    edit_name = State()
    edit_age = State()
    edit_gender = State()
    edit_email = State()
    edit_timezone = State()

class AdminBotStates(StatesGroup):
    enter_promocode = State()

